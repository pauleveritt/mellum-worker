# Small AI Learning Center

![A small robot at a workbench with a laptop, a magnifying glass, a chart, a wrench and a notebook, ready to learn](assets/illustrations/home.webp){ .illustration }

Python developers are interested in how agentic coding can help on routine work on their laptop. This space has
progressed rapidly, but the truth remains: small models need agents that help them stay on track.

## For the impatient

Clone the repo and run the installer from its root. On macOS/Linux it then
takes over — the weights, the server and your first answer. On Windows
`install.bat` only checks the prerequisites (llama-server and Node); you fetch
the weights and start the server yourself:

**macOS / Linux**
```bash
git clone https://github.com/andrevanzuydam/mellum-worker.git
cd mellum-worker
bash ./install.sh
```

**Windows**
```bat
git clone https://github.com/andrevanzuydam/mellum-worker.git
cd mellum-worker
.\install.bat
```

You need about 10 GB free for the `Q4_K_M` weights; a GPU with 8 GB or more
helps (it ran on an 8 GB card), and CPU works without one.

## Who it's for

Developers on macOS, Linux or Windows who know a terminal and Python or Node, and want to run a small coding
model locally behind Pi, and fix what goes wrong, with evidence. No machine-learning background is needed; the
[Introduction](introduction/index.md) covers the concepts and the [Glossary](glossary.md) defines every term.

## How every finding is told

Every finding is told the same way: the problem, how to reproduce it, the evidence, the fix, and whether the fix
worked. You can see exactly how strong each piece of evidence is.

Each step of a lesson carries an [evidence badge](about/evidence.md), from measured runs to reasoned conjecture, so
you always know what is proven and what is still open. [How to read a lesson](about/how-to-read.md) walks through
one page.

## Start here

Start with the **[Getting started](getting-started/index.md)** track: six steps that go from llama.cpp to a graded
eval harness and the remedy units. After that, any [lesson](lessons/index.md) stands alone and lists what you need first, and
[The Challenge](challenge/index.md) is where you test what you have learnt.

## Where to go

<div class="grid cards" markdown>

-   **[Introduction](introduction/index.md)**

    ---

    [Introduction](introduction/index.md): Demystifying agents and harnesses
    from first principles: models, prompts, context, tools, harnesses, agents
    and the feedback loop.

-   **[Getting Started](getting-started/index.md)**

    ---

    Set up a local model and Pi, in a fixed order: from
    [base Pi on llama.cpp](getting-started/base-pi-on-llamacpp.md) through
    [working with Pi](getting-started/working-with-pi.md) to
    [eval suites](getting-started/eval-suites.md). Then take the lessons, or go
    straight to The Challenge.

-   **[Lessons](lessons/index.md)**

    ---

    One failure, measured and fixed, per lesson. The findings lessons are
    being rebuilt; each will stand alone.

-   **[The Challenge](challenge/index.md)**

    ---

    Test what you have learnt: Easy, Medium and Hard, the same three
    projects every lesson is measured on. Can your setup beat the baseline?

-   **[Pathologies](pathologies.md)**

    ---

    The ways a small model goes wrong on an agentic task, each with the record
    that shows it: a map of failure, not a scoreboard.

-   **[Glossary](glossary.md)**

    ---

    Every term the center uses, defined once. Terms link here the first time
    a page uses them.

-   **[About](about/index.md)**

    ---

    [How to read a lesson](about/how-to-read.md),
    [evidence and badges](about/evidence.md), and
    [how to contribute](about/contributing.md).

</div>

## Contribute

The center is a collaboration between Paul and Andre, built in the open. To add a lesson, start from the
[lesson template](lesson-template.md); to see how the project runs, read the [project pages](project/index.md) and
[how to contribute](about/contributing.md).
