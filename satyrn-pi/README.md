# Staging directory for `satyrn-pi`

This directory is the seed of a new repository and lives here only while it is
being written and reviewed. Its layout mirrors the target repository, so
"create the repository" is a copy of this tree, not a reconstruction:

```
satyrn-pi/
  BRIEF.md                      -> needs to be read first
  ROADMAP.md                    -> the twelve phases as feature cycles
  docs/sdd.md                   -> verbatim source process, staged for phase 2
  docs/provenance/              -> verbatim source project rules
  docs/rules-applicability.md   -> effective scope, precedence and path mappings
  docs/superpowers/research/    -> inspection evidence and named decision owners
```

This is a planning handoff; none of the twelve product phases has shipped.
Read [BRIEF.md](BRIEF.md), [the applicability rules](docs/rules-applicability.md),
[the preserved process](docs/sdd.md), then [ROADMAP.md](ROADMAP.md).
Phase 2 installs the effective rules and re-earns their executable checks.
The [Superpowers/SDD workflow](BRIEF.md#how-we-develop-superpowers-sdd-and-the-roadmap)
applies from the first porting cycle and continues after the port. The
[upstream supplement](docs/superpowers/research/2026-11-16-upstream-acceptance-feedback.md)
records the November 15 acceptance-feedback changes without moving the
original provenance pin.

Nothing here is executed or imported by the source product. The source's
default tests do not discover this tree. Its document caps still apply here;
check the staged roadmap's file and cell sizes separately when editing it.

Reviewed here, copied out when the planning is finished. Corrections after the
copy live in the new repository, not here.
