# Provenance of the phase records

The phase records in this directory were moved here from the research
repository.

- Source repository: https://github.com/pauleveritt/mellum-mlx (local
  checkout read-only; nothing in it was changed).
- Source path: `docs/research/ladder/`.
- Source commit: `4b0f7e58a5ac0b10bfe678cce465c378d70161b1`.
- Moved: 2026-10-09 (phase M.6, one repo).
- Release tag for the raw evidence: `research-2026-10-09`.

## What was copied

Tracked files at that commit, via `git archive`, minus the raw files:
30 phase directories (A0 to A17 and the earlier phases) plus
`ablation-summary.md`.

- Per run directory: `run.json`, `final.md`, `brief.md`.
- Per phase: `README.md`, `table.md`.
- Each phase `README.md` gains one final line linking its tarball.
  Three phases had no README (`phase0-baseline-attempt1`,
  `phase1b-tuned-nopenalty-v3`, `phase2-guards-v3-attempt1`); each got
  one holding its name and that link.

## Moved research notes

The recovery README under `docs/superpowers/research/2026-10-07-mellum-recovery/`
gained the Moved-from line, and its line in `manifest.sha256` was updated to
match; `shasum -a 256 -c manifest.sha256` passes there. The `.zip` beside the
directory keeps the byte-original bundle. Paths quoted inside the moved notes
(for example `ladder/run_ladder.py`, `ladder/briefs/`) are pre-move paths, now
under `ladder/ladder/`.

## What was not copied

The raw files `trace.jsonl`, `stdout.txt` and `diff.patch` (450 each,
about 380 MB). They are archived per phase instead and listed in
`.gitignore`, so new runs write them locally without committing them.
Every one of the 30 phases had raw files, so there are 30 tarballs.

Before the 30 tarballs were built, `git status --short --ignored
docs/research/ladder` in the source checkout was empty and its HEAD was
the source commit above, so the working tree matched the commit.

A 31st phase, `smoke-m6-one-repo`, was added after the move: one rung-1 Mellum
Mode run launched from this checkout (2026-10-09, commit `e5e72f3`). It is
not part of the moved set, so it has no source commit; its raw files were
archived the same way, giving 31 tarballs in all.

Three M.7 phases followed, each launched from this checkout and archived the
same way: `ablation-a18-agentclinic-facts-off` (2026-10-09, commit
`38a4e64`), `ablation-a19-facts-on` and `ablation-a20-facts-fallback-only`
(2026-10-10, commit `aff031a`). That gives 34 tarballs in all.

## Raw archives

One `<phase>.tar.gz` per phase directory, holding the raw files at their
original relative paths (`<phase>/<run>/trace.jsonl`, and so on). Names
sorted, mtime 0, owner and group empty, mode 0644, so the same inputs give
the same hash. Each is attached to the `research-2026-10-09` release at
`https://github.com/pauleveritt/mellum-worker/releases/download/research-2026-10-09/<phase>.tar.gz`.

The tarballs stay in the maintainer's scratch directory until the release
is created and they are uploaded.

Rebuild one or all from a checkout of the source commit:

    cd ladder
    uv run python -m ladder.archive_raw --out OUT_DIR --tag research-2026-10-09 PATH_TO_SOURCE/docs/research/ladder/*/

The command prints `<phase> <sha256>` per tarball; compare with the table.

| phase | tarball | sha256 |
| --- | --- | --- |
| ablation-a0-replace | `ablation-a0-replace.tar.gz` | `63ffeb5c7a558e86b1f1cf1dcc5ca7030acf6967a2cbf677b0d0a42c0a02d4d7` |
| ablation-a1-noguards | `ablation-a1-noguards.tar.gz` | `21544904efac2251c0e4023cf7d6e48a9055b3c4a46c9709322b23cdae7b4880` |
| ablation-a10-delegated-v5 | `ablation-a10-delegated-v5.tar.gz` | `f4b7a5352604c9646cafd1a5bec8766caa6da8f08a9e54b493eb2c039518b248` |
| ablation-a11-delegated-nointercom | `ablation-a11-delegated-nointercom.tar.gz` | `7c3910b5871ff777f7f5bc16539570b01a440d0d1179d784abe1154772d57224` |
| ablation-a12-strip-thinking | `ablation-a12-strip-thinking.tar.gz` | `0da3fe7e1a00f2a3e54f901a86af6108f2967bf6a8044a3e95240dcd754bcea1` |
| ablation-a13-budget-medium | `ablation-a13-budget-medium.tar.gz` | `01409a5822cafb1cb80f6ffe9b2cce4e25aeee22f2366f4a6aab76d783e8c0a6` |
| ablation-a14-mellum-mode | `ablation-a14-mellum-mode.tar.gz` | `062a5dc0708ac160b43c0aa0d1236d14051dd7adc980f8cb196608f37a7aa331` |
| ablation-a15-chunked-brief | `ablation-a15-chunked-brief.tar.gz` | `42130b076ed17a8ef3d9bcff4936bdb3d8252c5eaa597b3a4fdfa43e2d7f8f27` |
| ablation-a16-brief-one-prompt | `ablation-a16-brief-one-prompt.tar.gz` | `a96020c95967dff7dbdcb4a3640883547cc233230e3b0f2da12ee941735904d7` |
| ablation-a17-mode-v012 | `ablation-a17-mode-v012.tar.gz` | `12f563de4375ca62bdb5d4765530ad4923cef11c5447640471c9ac5620659256` |
| ablation-a2-v4a | `ablation-a2-v4a.tar.gz` | `85c0951f52856afcfdc8d57485ee829165cec4ec0cf99ae4d168788df1aca343` |
| ablation-a3-v4b | `ablation-a3-v4b.tar.gz` | `fb0508b980fef528b914332fd1046670a8ef9edcb2121b6463dac1b4a43afc67` |
| ablation-a4-v4c | `ablation-a4-v4c.tar.gz` | `bcf0b0e5dce191445c61b5b65d0f395ffc0a8f714bdbfd99f10a29ff2304e7e2` |
| ablation-a5-thinking-medium | `ablation-a5-thinking-medium.tar.gz` | `467764a4b245338b6a3e50ef8ed1dbf855cb8f6b3acefeb96ba3749c4124700a` |
| ablation-a8-delegated-lean | `ablation-a8-delegated-lean.tar.gz` | `8e777e369cee88a0e867c63f4483aa8ca0f31cb11859b006ffb8a2549c2200ce` |
| ablation-a9-delegated-final | `ablation-a9-delegated-final.tar.gz` | `6a7973a19c457dc11abb84a431ced0d535358486e45fcfe3329d5fb9b9f90758` |
| phase0-baseline-attempt1 | `phase0-baseline-attempt1.tar.gz` | `b949633747eb1509a9d906c7cf9a69e2f37d3e2ae18cb01897bd1338e4986a19` |
| phase0-baseline | `phase0-baseline.tar.gz` | `e0aa596d940da77ebeeb6a5bddbd91e24c28bf44f68a919591e6ac9b9fcf4283` |
| phase0b-baseline-v3 | `phase0b-baseline-v3.tar.gz` | `b46f19c356c4580540d7655f1abea143b1c4f4bcc8a4a8657dd549141e4ed5bc` |
| phase0c-primary-operator | `phase0c-primary-operator.tar.gz` | `76bde981799dcbd600ff838d2690046bcd7895809acb15b788e33eec353144ec` |
| phase0c-primary-plain | `phase0c-primary-plain.tar.gz` | `6b960750bf29826cabd05348840945e30101e7b93ef774c2e7d80df4ee2ab6fb` |
| phase1-tuned-v3 | `phase1-tuned-v3.tar.gz` | `f3122e4bf0e203cdb2abc512b6909cac4917cfb15c68ba7139e79fcbfc53f6d5` |
| phase1b-tuned-nopenalty-v3 | `phase1b-tuned-nopenalty-v3.tar.gz` | `05a5f693f1b1cba432cac7802009c241ac19eefe3699edff2c2434f989e4b681` |
| phase1c-baseline-greedy | `phase1c-baseline-greedy.tar.gz` | `828abbbf3b85f8295ec49dc83b9e441c5ab812ac0df478abe4e8ad92ecd18364` |
| phase1d-tuned-effective | `phase1d-tuned-effective.tar.gz` | `7564d6647b4f8a58ca7b0e372f8e7455baea2db233867b8858aaf9e01d57169c` |
| phase2-guards-v3-attempt1 | `phase2-guards-v3-attempt1.tar.gz` | `c16804efdfb37848081f5147610caadd388d0dde0d4d49d3eb959bd0de56f878` |
| phase2-guards-v3 | `phase2-guards-v3.tar.gz` | `cd6f5def393ff9abfe91de80267c69f39343dd677ae434b16b5393410947b9d2` |
| phase2b-guards-bounded | `phase2b-guards-bounded.tar.gz` | `9049222a168013e921a2fe221cfa38da371775eb1230fc0b93a9638d7b186f08` |
| phase3a-delegated-noskill | `phase3a-delegated-noskill.tar.gz` | `bc1997d958a0934d7a38973f36692c279d8632605665f7435cc6982a9239cf8e` |
| phase3b-delegated-skill | `phase3b-delegated-skill.tar.gz` | `1da9291896c9246b24770786d27b3bac6f18b4282daf2efb8d962febf0cd5d9a` |
| smoke-m6-one-repo | `smoke-m6-one-repo.tar.gz` | `b68eb25192c06676486be6bba7fdb18c25315a8438c3a648c88edae2d918ef0c` |
| ablation-a18-agentclinic-facts-off | `ablation-a18-agentclinic-facts-off.tar.gz` | `de705fd02d80afd57e0ab9ddf154e35886cd8d8e05180e5401bb59e9ccdf83fe` |
| ablation-a19-facts-on | `ablation-a19-facts-on.tar.gz` | `aca9d936997ef15ffb33e4eea5b71af60d64a5956326b7cedff6121ac5aab895` |
| ablation-a20-facts-fallback-only | `ablation-a20-facts-fallback-only.tar.gz` | `b549e06a201fbffdd0badb268cb52ee6eaec4ab9ce90ffa74796962fdc3e84d0` |

## M.7C telemetry smokes

Two existing rung-1 attempts (Mode and delegated Worker), launched on
2026-10-11 America/New_York, trace UTC date 2026-10-12. Source checkout
commit `b108aac`; details and content review in [smoke-m7c](smoke-m7c/README.md).
Pi 1.1.0, Node v24.3.0; actual canonical Pi package identity matched launch
intent, including the child. Installed pi-subagents revision:
`8983754bb3ef6603cbbe46dcc2314ec8563ffc23`.

The deterministic six-member archive contains only `trace.jsonl`, `stdout.txt`
and `diff.patch` from the two attempts. Members match their retained sources
byte-for-byte. Downloaded published bytes were checked against SHA-256:

- Asset: [`smoke-m7c.tar.gz`](https://github.com/pauleveritt/mellum-worker/releases/download/research-2026-10-11/smoke-m7c.tar.gz).
- SHA-256: `a62352518e2497950e28e5edb7037033781d8208b0115461aca07cef6df32fae`.
- Release tag is an evidence container, not the implementation/source version.
- Earlier October 11 preservation manifests remain unchanged.

## A21 and A21 control

Twelve Mellum Mode runs each on AgentClinic rungs 6–9, 2026-10-13 08:04–09:09
America/New_York, preregistered in
[2026-10-13-a21-preregistration.md](../superpowers/research/2026-10-13-a21-preregistration.md).
Source checkout commit `30d441b` (worker `v0.1.7-5-g30d441b`); Pi 1.1.0,
oMLX 0.7.0. Records: [A21](ablation-a21-light-section-roadmap/README.md),
[A21 control](ablation-a21-control/README.md).

Each deterministic archive (`ladder.archive_raw`) holds only `trace.jsonl`,
`stdout.txt` and `diff.patch`, 12 of each. Downloaded published bytes were
checked against SHA-256:

- Asset: [`ablation-a21-light-section-roadmap.tar.gz`](https://github.com/pauleveritt/mellum-worker/releases/download/research-2026-10-13/ablation-a21-light-section-roadmap.tar.gz).
- SHA-256: `dfec3ab7b89e8ead690a5799593a81eaa2a3f00f16beb192efb75f823d628890`.
- Asset: [`ablation-a21-control.tar.gz`](https://github.com/pauleveritt/mellum-worker/releases/download/research-2026-10-13/ablation-a21-control.tar.gz).
- SHA-256: `a73cd5f77905af04b68d8016fc5986f7fefcdbbbf3e2485632c7b3e709c97e41`.
- Release tag is an evidence container, not the implementation/source version.

## Rung 9 screen

Three Mellum Mode runs per arm on rung 9, 2026-10-13 09:17–09:32
America/New_York, an exploratory screen
([note](../superpowers/research/2026-10-13-rung9-screen.md)). Source checkout
commit `b31372b` (worker `v0.1.8-1-gb31372b`); Pi 1.1.0, oMLX 0.7.0. Each
archive holds only `trace.jsonl`, `stdout.txt` and `diff.patch`, 3 of each,
attached to the same evidence release as A21. Downloaded published bytes
were checked against SHA-256:

- Asset: [`screen-rung9-light-section.tar.gz`](https://github.com/pauleveritt/mellum-worker/releases/download/research-2026-10-13/screen-rung9-light-section.tar.gz).
- SHA-256: `501b59825e7b482aceaae8765c0ebddd2310698c557c17513b311768049bf2ff`.
- Asset: [`screen-rung9-one-file-roadmap.tar.gz`](https://github.com/pauleveritt/mellum-worker/releases/download/research-2026-10-13/screen-rung9-one-file-roadmap.tar.gz).
- SHA-256: `a7b51399a57c37f45afd5cb7c2b96a96e137b32d9a418eeb3e997e56c1ad44f0`.
