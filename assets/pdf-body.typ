// Before the body of the PDF reports (format: typst), so that these rules come after the ones of
// Quarto's article template: ragged right (code spans and long numbers stretch justified lines),
// and table cells never justified.
#set par(justify: false)
#show table.cell: set par(justify: false)
