// Page furniture for the PDF reports (format: typst). Included in the header, before Quarto's own
// `#set page(...)`, which adds the paper size and margins to these settings.
#set page(
  header: context {
    if counter(page).get().first() > 1 {
      set text(size: 8pt, fill: rgb("#52514e"))
      link("https://matheusmmmp.github.io/digilab-reward-case-study/")[matheusmmmp.github.io/digilab-reward-case-study]
      h(1fr)
      [Two experiments on a virtual pet]
    }
  },
  footer: context {
    set text(size: 8pt, fill: rgb("#52514e"))
    [© 2026 Matheus de Medeiros Pereira. Text, figures and data: all rights reserved.]
    h(1fr)
    counter(page).display("1 / 1", both: true)
  },
)

// Long column values (e.g. petting_with_credit_random_time) may break after an underscore in tables.
#show table.cell: it => {
  show "_": "_" + sym.zws
  it
}
#show table: set text(size: 0.85em)
