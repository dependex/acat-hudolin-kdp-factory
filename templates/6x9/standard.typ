// KDP 6x9 Standard Template
// Trim: 6 x 9 inches
// Margins: top 0.75, bottom 0.75, inside 0.875, outside 0.625
// Bleed: 0.125 inches

#set page(
  width: 6in,
  height: 9in,
  margin: (top: 0.75in, bottom: 0.75in, inside: 0.875in, outside: 0.625in),
  numbering: "1",
  number-align: center + bottom,
)

#set text(font: "Libertinus Serif", size: 11pt, lang: "it")
#set par(leading: 1.4em, first-line-indent: 1.5em, justify: true)
#set heading(numbering: "1.1")

#show heading.where(level: 1): it => {
  pagebreak(weak: true)
  v(2em)
  text(font: "Libertinus Sans", size: 18pt, weight: "bold")[#it]
  v(1em)
}

#show heading.where(level: 2): it => {
  v(1.5em)
  text(font: "Libertinus Sans", size: 14pt, weight: "bold")[#it]
  v(0.5em)
}
