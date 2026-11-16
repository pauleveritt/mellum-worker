# Staging directory for `satyrn-pi`

This directory is the seed of a new repository and lives here only while it is
being written and reviewed. Its layout mirrors the target repository, so
populating the repository means copying this tree, not reconstructing it:

```
satyrn-pi/
  BRIEF.md                      -> needs to be read first
  ROADMAP.md                    -> the twelve phases as feature cycles
  docs/sdd.md                   -> verbatim source process, staged for phase 2
  docs/provenance/              -> verbatim source project rules
  docs/rules-applicability.md   -> effective scope, precedence and path mappings
  docs/glossary.md              -> core product definitions
  docs/superpowers/research/    -> inspection evidence and named decision owners
```

This is a planning handoff; none of the twelve product phases has shipped.
Read [BRIEF.md](BRIEF.md), [the applicability rules](docs/rules-applicability.md),
[the preserved process](docs/sdd.md), then [ROADMAP.md](ROADMAP.md).
P1.2 defines the worker/eval domain and vocabulary before SDD setup.
Phase 2 installs the effective rules and re-earns their executable checks.
The [Superpowers/SDD workflow](BRIEF.md#how-we-develop-superpowers-sdd-and-the-roadmap)
applies from the first porting cycle and continues after the port. The
[upstream supplement](docs/superpowers/research/2026-11-16-upstream-acceptance-feedback.md)
records the November 15 acceptance-feedback changes without moving the
original provenance pin.

The public progression is Vanilla → Base → Easy → Medium → Hard. The
[glossary](docs/glossary.md) distinguishes remedy presets from the suites they
run on; Vanilla loads no remedy preset. The
[vocabulary review](docs/superpowers/research/2026-11-16-vocabulary-review.md)
maps historical terms without changing the source.

Nothing here is executed or imported by the source product. The source's
default tests do not discover this tree. Its document caps still apply here;
check the staged roadmap's file and cell sizes separately when editing it.

Reviewed here, copied out when the planning is finished. Corrections after the
copy live in the new repository, not here.
