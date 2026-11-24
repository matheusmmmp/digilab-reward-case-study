"""Build data/body_triage_reference.json (case 2: official aggregate numbers of the triage)
from its resultado.json.

What is copied: the run's start, end, duration and process count (from its meta.json), the triage's estimates, the by-place and by-cell descriptive values for
the published measures, the count behind "11 distinct cells", and the values the official
result quotes from the earlier study (C4) in `comparacao_com_a_c4`. Nothing else."""
import argparse
import hashlib
import json
from pathlib import Path

SHA = "02a9e2f05d1895264edd36a3ad433509a55f05f63cf5761837c8849a83a62887"
META_SHA = "7b16e08c74860480d20adb9d89bf684cfa540e885892b36e0760677a0ff71b46"  # the run's metadata file
C4_SHA = "136c304837710a8bf543c63530ad44b6b898784e1dfc84b4ef574359b7969f2d"  # as recorded in the triage result
ARM = {"CTRL": "control", "DTB": "body_variant"}
OWNER = {"atencioso": "attentive", "relapso": "neglectful",
         "aleatorio": "random", "incoerente": "inconsistent"}
PLACE = {"comedouro": "at_feeder", "longe": "far", "longe_fixo": "far_fixed"}
GROUP = {"12_celulas": "12_cells", "11_celulas": "11_cells", **PLACE}
# source descriptive key -> published column
MEAS = {"tempo_bem": "time_well", "tempo_bem_8_14": "time_well_d8_14", "saude_media": "health_d8_14",
        "privacao_vida": "deprivation", "exaustao_vida": "exhaustion", "taxa_por_episodio": "episode_rate",
        "refeicoes_por_dia": "meals_per_day", "fracao_ticks_dormindo": "sleep_frac_ticks",
        "chutes": "kicks", "brincar": "play_decisions"}
NEAR_CEILING = "tempo_bem_perto_do_teto"  # share of lives with time_well above the plan's 0.99 cut


def cell(key):
    o, p = key.split("|")
    return f"{OWNER[o]}|{PLACE[p]}"


def est(x):
    """levels by arm and the paired body_variant - control estimate"""
    d = x["DTB - CTRL"]
    if d["motivo"] is not None:
        raise ValueError(f"estimate without a CI: {d['motivo']}")
    return {"control": x["niveis"]["CTRL"], "body_variant": x["niveis"]["DTB"], "n": d["n"],
            "mean": d["media"], "sd": d["dp"], "ci_low": d["ic95"]["ic_inferior"], "ci_high": d["ic95"]["ic_superior"]}


def ci(x):
    return {"mean": x["media"], "ci_low": x["ic95"]["ic_inferior"], "ci_high": x["ic95"]["ic_superior"]}


def estimate_name(k):
    if k.startswith("tempo_bem_"):
        return f"time_well|{GROUP[k.removeprefix('tempo_bem_')]}"
    if k == "saude_12_celulas":
        return "health_d8_14|12_cells"
    if k == "saude_sem_comida":
        return "health_d8_14|neglectful_and_random"
    if k == "taxa_por_episodio_longe_fixo":
        return "episode_rate|far_fixed"
    if k.startswith("saude|"):
        return "health_d8_14|" + cell(k.removeprefix("saude|"))
    raise KeyError(k)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True, help="resultado.json of the triage")
    ap.add_argument("--meta", required=True, help="meta.json of the triage (only the run times are read)")
    ap.add_argument("--out", default="data/body_triage_reference.json")
    a = ap.parse_args()
    raw = Path(a.source).read_bytes()
    got = hashlib.sha256(raw).hexdigest()
    if got != SHA:
        raise SystemExit(f"source sha256 mismatch: {got} != {SHA}")
    x = json.loads(raw)
    meta_raw = Path(a.meta).read_bytes()
    if hashlib.sha256(meta_raw).hexdigest() != META_SHA:
        raise SystemExit("meta.json sha256 mismatch")
    meta = json.loads(meta_raw)
    if meta["artefatos_sha256"]["resultado.json"] != SHA:
        raise SystemExit("meta.json is not the metadata of this result")
    if x["modo"] != "triagem":
        raise ValueError("not the triage result")
    d = x["descritivo"]
    out = {"source_resultado_sha256": SHA, "source_meta_sha256": META_SHA,
           "run": {"start": meta["inicio"], "end": meta["fim"], "duration_s": meta["duracao_s"],
                   "processes": meta["processos"]},
           "lives": x["vidas"], "units": x["unidades"], "margin": x["margem"],
           "formal_reading": False,  # the triage has no class, no p and no confirm / not-confirm
           "estimates": {}, "effect_over_margin": {}, "by_group": {}, "time_well_by_cell": {}}
    for k, v in x["estimativas"].items():
        out["estimates"][estimate_name(k)] = est(v)
        if "efeito_sobre_a_margem" in v:
            out["effect_over_margin"][estimate_name(k)] = v["efeito_sobre_a_margem"]
    for g, name in GROUP.items():
        out["by_group"][name] = {c: est(d["por_lugar"][g][k]) for k, c in MEAS.items()}
        out["by_group"][name]["share_time_well_above_0_99"] = est(d["por_lugar"][g][NEAR_CEILING])
    out["arm_means"] = {arm: {c: out["by_group"]["12_cells"][c][arm] for c in MEAS.values()}
                        for arm in ARM.values()}
    for k, v in d["por_dono"].items():
        out["time_well_by_cell"][cell(k)] = est(v["tempo_bem"])
    out["inconsistent_equals_attentive"] = {
        f"{ARM[k.split('|')[0]]}|{PLACE[k.split('|')[1]]}": {"lives": v["vidas"], "equal": v["iguais"]}
        for k, v in d["incoerente_igual_ao_atencioso"].items()}
    c4 = d["comparacao_com_a_c4"]
    if c4["fontes_sha256"]["c4/resultado.json"] != C4_SHA:
        raise SystemExit("the quoted C4 values do not come from the expected C4 result")
    gmap = {"saude_12_celulas": "health_d8_14|12_cells", "saude_sem_comida": "health_d8_14|neglectful_and_random",
            "taxa_por_episodio_longe_fixo": "episode_rate|far_fixed",
            **{f"tempo_bem_{p}": f"time_well|{q}" for p, q in PLACE.items()}}
    out["c4_quoted"] = {
        "source_c4_resultado_sha256": c4["fontes_sha256"]["c4/resultado.json"],
        "units": 200,  # the C4 run size, stated in the official result (200 units)
        "values": {
            "time_well|12_cells": {**ci(c4["primaria"]["12_celulas"]),
                                   "control": c4["primaria"]["12_celulas"]["niveis"]["CTRL"],
                                   "body_variant": c4["primaria"]["12_celulas"]["niveis"]["DTB"]},
            "time_well|11_cells": {**ci(c4["primaria"]["11_celulas"]),
                                   "control": c4["primaria"]["11_celulas"]["niveis"]["CTRL"],
                                   "body_variant": c4["primaria"]["11_celulas"]["niveis"]["DTB"]},
            **{gmap[k]: ci(v) for k, v in c4["guardas"].items()},
            **{"health_d8_14|" + cell(k): ci(v) for k, v in c4["saude_por_celula"].items()},
        },
    }
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(out, indent=2) + "\n", newline="\n")
    print("wrote", a.out)


if __name__ == "__main__":
    main()
