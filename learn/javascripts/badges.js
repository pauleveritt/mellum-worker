// Turn each "**Badge:** `name`" line into an icon pill. The Markdown stays
// plain (it reads the same on GitHub and the lesson tests check it); only the
// rendered site gets the icon, colour and a link to the badge definitions.
(() => {
  const ICON = {
    "reference-run": '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><path d="m9 11 3 3L22 4"/>',
    cited: '<path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>',
    screen: '<path d="M9 3h6"/><path d="M10 3v6L4.5 19a1.5 1.5 0 0 0 1.3 2h12.4a1.5 1.5 0 0 0 1.3-2L14 9V3"/><path d="M7 15h10"/>',
    conjecture: '<circle cx="12" cy="12" r="10"/><path d="M9.1 9a3 3 0 0 1 5.8 1c0 2-3 3-3 3"/><path d="M12 17h.01"/>',
  };
  const TITLE = {
    "reference-run": "Reference run: a recorded run on the suites",
    cited: "Cited: rests on a cited record",
    screen: "Screen: a few targeted runs; a lead, not a rate",
    conjecture: "Conjecture: reasoned, not yet measured",
  };

  function decorate(root) {
    for (const strong of root.querySelectorAll(".md-typeset p > strong:first-child")) {
      if (strong.textContent.trim() !== "Badge:") continue;
      const p = strong.parentElement;
      const code = p.querySelector("code");
      const name = code?.textContent.trim();
      if (!ICON[name] || p.classList.contains("badge-line")) continue;
      const evidence = document.querySelector('a[href$="about/evidence/"]')?.getAttribute("href");
      const pill = document.createElement(evidence ? "a" : "span");
      if (evidence) pill.href = `${evidence}#badges`;
      pill.className = `evidence-badge evidence-badge--${name}`;
      pill.title = TITLE[name];
      pill.innerHTML = `<svg viewBox="0 0 24 24" aria-hidden="true">${ICON[name]}</svg><span>${name}</span>`;
      p.classList.add("badge-line");
      p.replaceChildren(pill);
    }
  }

  // The legend: the badge table under the "Badges" heading shows the same pills.
  function legend(root) {
    const heading = root.querySelector(".md-typeset h2#badges");
    let table = heading?.nextElementSibling;
    while (table && table.tagName !== "TABLE" && !table.querySelector?.("table")) table = table.nextElementSibling;
    table = table?.tagName === "TABLE" ? table : table?.querySelector("table");
    for (const code of table?.querySelectorAll("tbody td:first-child code") ?? []) {
      const name = code.textContent.trim();
      if (!ICON[name]) continue;
      const pill = document.createElement("span");
      pill.className = `evidence-badge evidence-badge--${name}`;
      pill.title = TITLE[name];
      pill.innerHTML = `<svg viewBox="0 0 24 24" aria-hidden="true">${ICON[name]}</svg><span>${name}</span>`;
      code.replaceWith(pill);
    }
  }

  const run = () => { decorate(document); legend(document); };
  if (window.document$?.subscribe) window.document$.subscribe(run);
  else document.addEventListener("DOMContentLoaded", run);
})();
