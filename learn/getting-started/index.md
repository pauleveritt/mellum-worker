# Getting Started

This track is in a fixed order: each step builds on the one before, and
each ends with a check you can run. Six steps, then two paths.

![A small robot with a backpack at the start of a path of stepping stones up a hill](../assets/illustrations/getting-started.webp){ .illustration }

## Steps

1. **[Base Pi on llama.cpp](base-pi-on-llamacpp.md)**: Install `uv`, llama.cpp and the Mellum weights, and get an answer from base Pi through a private profile. Start here.
2. **[Working With Pi](working-with-pi.md)**: Use Pi's interactive terminal: prompts, tools, sessions, project trust, and the course's `/lesson` and `/remedy` commands.
3. **[Eval suites and the telemetry](eval-suites.md)**: Run the Bronze, Silver and Gold suites through the provided harness, grade the model's files, and read why a run failed from its trace.
4. **[The Harness](the-harness.md)**: Write a mini harness that runs Pi in a fresh folder and scores it, the instrument every lesson's before and after line uses.
5. **[Extensions and Remedy Units](extensions.md)**: Learn what a Pi extension and a remedy unit are, how presets group units, and the two ways to switch them on.
6. **[Troubleshooting](troubleshoot.md)**: Fix `uv` and `llama-server` when a setup step fails.

## Two paths from here

**Take the lessons.** Open [S0 Start Here](../lessons/start-here.md) on this
site, or type `/lesson S0` in Pi from a trusted checkout. Each lesson adds one
remedy unit and shows the run before and after it.

**Go straight to [The Challenge](../challenge/index.md).** Run Bronze, Silver
and Gold, apply remedies with `--remedy preset:…`, and bring your own
extension with `--extension`. Use the lessons as a reference when a run fails
in a way you do not understand.
