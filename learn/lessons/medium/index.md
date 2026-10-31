# Medium Lessons

You start where Easy ended, with every Easy unit on, so every failure here is one
the Easy remedies cannot fix. Each lesson adds one thing: what the model is
told, how its turns end, a tool of ours, a check, or the shape of the task.
After M8 you can measure a remedy yourself, and Hard starts.

![A small robot studying a long unrolled scroll through a magnifying glass](../../assets/illustrations/tier-medium.webp){ .illustration }

<div class="grid cards" markdown>

-   **[M1 · Tell It How to Test](tell-it-how-to-test.md)**

    ---

    The project's own test command, in every request.
    Adds `context/add-project-facts`.

-   **[M2 · A Short Prompt](a-short-prompt.md)**

    ---

    A 643-character prompt in place of a procedure.
    Adds `context/use-short-prompt`.

-   **[M3 · Nudge an Empty Turn](nudge-an-empty-turn.md)**

    ---

    A turn that ends with nothing, part-way through.
    Adds `nudge/nudge-empty-turn`.

-   **[M4 · Run Long Commands Safely](run-long-commands-safely.md)**

    ---

    A watcher or server run in the background, with its output returned.
    Adds `tool/background-long-commands`.

-   **[M5 · Look It Up](look-it-up.md)**

    ---

    A `lookup` tool over the installed packages, instead of a guess.
    Adds `tool/lookup-library-docs`.

-   **[M6 · Check Before Finishing](check-before-finishing.md)**

    ---

    Lint and type checks before the model may stop.
    Adds `check/check-code-quality`.

-   **[M7 · Keep a Plan](keep-a-plan.md)**

    ---

    A plan file the model writes, follows and amends.
    Adds `tool/keep-a-plan`. Not built yet.

-   **[M8 · Build a Suite](build-a-suite.md)**

    ---

    A grader that fails the broken build, built by you in Pi.
    Your grader is the remedy. Not built yet.

</div>
