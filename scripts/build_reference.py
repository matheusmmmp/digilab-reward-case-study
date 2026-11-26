"""Build data/reference.json (official aggregate numbers) from resultado.json."""

import argparse
import hashlib
import json
from pathlib import Path

SHA = "97892493ab0b3c5b551e3319351cfd5e62e69b1ac2156668c8d967ac235360ae"
ARM = {
    "R0": "no_petting",
    "R-CORPO": "petting_body_only",
    "R-CB": "petting_with_credit",
    "R-SORT": "petting_with_credit_random_time",
}
MEAS = {
    "t_acordado": "awake_frac_d1_14",
    "t_acordado_8_14": "awake_frac_d8_14",
    "tempo_bem": "time_well",
    "taxa_por_episodio": "episode_rate",
    "comer": "eat_decisions",
    "brincar": "play_decisions",
}
OWNER = {"atencioso": "attentive", "relapso": "neglectful", "aleatorio": "random", "incoerente": "inconsistent"}
PLACE = {"comedouro": "at_feeder", "perto": "near", "longe": "far"}
# Breakdowns are copied only for the two measures the case study shows by group.
SUBSET_MEAS = {"t_acordado": "awake_frac_d1_14", "tempo_bem": "time_well"}
# Official reading labels, original wording and the English used on the site.
READINGS = {
    "L-ACORDADO": ("L-AWAKE", {"nao: com a recompensa o pet dorme mais": "no: with the reward the pet sleeps more"}),
    "L-BEM": ("L-WELL", {"o pet fica melhor": "the pet is better off"}),
    "L-PORQUE": (
        "L-WHY",
        {"pela recompensa na hora, e pelo que o pet aprende": "by the timely reward and by what the pet learns"},
    ),
}


def contrast(v):
    return {"mean": v["media"], "ci_low": v["ic_inferior"], "ci_high": v["ic_superior"]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True)
    ap.add_argument("--out", default="data/reference.json")
    a = ap.parse_args()
    raw = Path(a.source).read_bytes()
    got = hashlib.sha256(raw).hexdigest()
    if got != SHA:
        raise SystemExit(f"source sha256 mismatch: {got} != {SHA}")
    x = json.loads(raw)
    out = {"source_resultado_sha256": SHA, "arm_means": {}, "contrasts": {}, "contrast_definitions": {}}
    for code, arm in ARM.items():
        out["arm_means"][arm] = {c: x["medias"][code][k] for k, c in MEAS.items()}
    for k, c in MEAS.items():
        out["contrasts"][c] = {}
        for d in ("D1", "D2", "D3"):
            v = x["contrastes"][k][d]
            out["contrasts"][c][d] = contrast(v)
            out["contrast_definitions"][d] = {"a": ARM[v["a"]], "b": ARM[v["b"]]}
    for key, names, label in (("por_dono", OWNER, "by_owner"), ("por_lugar", PLACE, "by_place")):
        out[label] = {}
        for g, name in names.items():
            out[label][name] = {c: {d: contrast(x[key][g][k][d]) for d in ("D1", "D2", "D3")} for k, c in SUBSET_MEAS.items()}
    out["readings"] = {}
    for k, (en, labels) in READINGS.items():
        pt = x["leitura"][k]["leitura"]
        out["readings"][en] = {"label": labels[pt], "label_original": pt}
    out["guards_not_measured"] = len(x["leitura"]["guardas_nao_medidas"])
    out["dose_premise_held"] = bool(x["premissas"]["P-DOSE"]["cumpre"])
    out["preregistered"] = {
        "delta_a": x["leitura"]["numeros"]["delta_a"],
        "margin_well": x["leitura"]["numeros"]["margem_bem"],
        "units": x["unidades"],
        "lives": x["vidas"],
    }
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(out, indent=2) + "\n", newline="\n")
    print("wrote", a.out)


if __name__ == "__main__":
    main()
