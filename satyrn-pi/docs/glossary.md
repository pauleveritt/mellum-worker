# Satyrn Pi glossary

Use Vanilla → Base → Easy → Medium → Hard directly. A suite says what work is
graded; the chosen name says what is enabled. Historical names are mapped in
the [vocabulary review](superpowers/research/2026-11-16-vocabulary-review.md).
The Zensical glossary presentation lands in phase 3.

### Vanilla

<!-- zensical-glossary-aliases: Vanilla Pi -->
Pi using the subject model, with the trace recorder and no worker extension or
remedies. The baseline for comparisons. It loads no remedy preset.

### Base

The thin worker in its active mode, plus the remedies explicitly listed in
`base.json`. The list starts empty. The worker switches to the subject model,
drops pre-marker history, tracks and records the span, then restores the main
model. It bundles no prompt replacement, tool restriction, project facts or
guards. Common remedies must earn additions through measurement.

### Remedy

One explicit, additive behaviour addressing an observed failure, implemented
in one inspectable TypeScript file under `remedies/<kind>/`. Its applicability
and evidence are recorded; it encodes no suite-specific answer. A guard blocks
an action; a nudge adds a corrective message; other remedies can change the
prompt, context or available tools.

### Preset

A named, ordered JSON list of remedies, with no includes or implicit additions.
`base.json`, `easy.json`, `medium.json` and `hard.json` each list their complete
contents. Easy retains Base's remedies, Medium retains Easy's, and Hard retains
Medium's; each adds only remedies earned through measurement. Adjacent lists
may be equal. Loading a preset selects remedies, not a model or a suite, and
does not prove a passing result.

### Eval suite

The tasks and fixtures to run, with their grading expectations. Easy, Medium
and Hard name suites as well as presets; say "Easy suite" or "Easy preset"
where the distinction matters. Compare Vanilla and Base on the same suite;
retaining Easy's remedies does not establish that they help on Medium or Hard.
