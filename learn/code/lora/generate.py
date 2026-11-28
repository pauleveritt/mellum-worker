#!/usr/bin/env python
"""Generate golden tasks from a catalog of domain specs.

Every task is the same proven shape — a FastAPI + Jinja2 + sqlite-utils app
carrying the four target shapes (second endpoint of a pair, exact 303 redirect,
write/apply/track/idempotent migration, exact JSON summary) — parametrised by
domain, entity, fields, the flag verb-pair, and the extra migration column.

`catalog.json` is the single source of truth; this engine renders each spec
into `tasks/<name>/`. Verify every generated task (guard + checks) before it
counts — see verify.py.

  uv run python learn/code/lora/generate.py        # regenerate all tasks
"""
from __future__ import annotations

import json
import shutil
import string
from pathlib import Path

ROOT = Path(__file__).parent

# Variation pools — rotate these over each base domain to multiply the catalog.
# Every token here is guard-clean (no hard-suite domain literal), and "un"+field
# reads naturally for the summary keys.
FLAG_POOL = [
    ("pinned", "pin", "unpin"),
    ("saved", "save", "unsave"),
    ("starred", "star", "unstar"),
    ("flagged", "flag", "unflag"),
    ("favorited", "favorite", "unfavorite"),
    ("liked", "like", "unlike"),
    ("hidden", "hide", "unhide"),
    ("muted", "mute", "unmute"),
    ("locked", "lock", "unlock"),
    ("tracked", "track", "untrack"),
]
EXTRA_POOL = [
    ("color", "str", "white"),
    ("label", "str", "none"),
    ("rank", "int", 0),
    ("tag", "str", ""),
    ("priority", "int", 0),
    ("score", "int", 0),
    ("category", "str", "general"),
    ("weight", "int", 1),
    ("position", "int", 0),
    ("slug", "str", ""),
]


def expand(base_catalog: list[dict]) -> list[dict]:
    """Multiply each base domain into len(FLAG_POOL) variants by rotating the
    flag verb-pair and the extra migration column (and renaming app/db/seed to
    match). Field set and routes stay the base's, so each reference is coherent."""
    specs = []
    for base in base_catalog:
        old_flag = base["flag"]["field"]
        for i, (flag_field, on, off) in enumerate(FLAG_POOL):
            ename, etype, edefault = EXTRA_POOL[i]
            seed = [
                {**{k: v for k, v in row.items() if k != old_flag}, flag_field: row[old_flag]}
                for row in base["seed"]
            ]
            specs.append(
                {
                    **base,
                    "name": f"{base['name']}-v{i}",
                    "app": f"{base['app']}{i}",
                    "db_env": f"{base['db_env']}_{i}",
                    "db_file": f"{base['table']}_{i}.db",
                    "flag": {"field": flag_field, "on": on, "off": off},
                    "extra": [ename, etype, edefault],
                    "seed": seed,
                }
            )
    return specs
TASKS = ROOT / "tasks"
PYT = {"str": "str", "int": "int"}

MODELS = string.Template('''import os

import sqlite_utils

DB_PATH = os.environ.get("$db_env", "$db_file")

SEED = $seed


def get_db(path: str | None = None) -> "sqlite_utils.Database":
    return sqlite_utils.Database(path or DB_PATH)


def init_db(db) -> None:
    if "$table" not in db.table_names():
        db["$table"].create($colspec, pk="id")
    if db["$table"].count == 0:
        for row in SEED:
            db["$table"].insert(row)


def list_rows(db) -> list[dict]:
    return list(db["$table"].rows_where(order_by="id"))


def add_row(db, $add_args) -> int:
    return db["$table"].insert($insert_dict).last_pk


def set_flag(db, row_id: int, on: bool) -> None:
    db["$table"].update(row_id, {"$flag": 1 if on else 0})


def summary(db) -> dict:
    total = db["$table"].count
    on = db["$table"].count_where("$flag = 1")
    return {"total": int(total), "$flag": int(on), "un$flag": int(total - on)}
''')

MIGR = string.Template('''"""Tracked, idempotent migrations for $app."""
from __future__ import annotations

BACKFILL_DATE = "2026-01-01T00:00:00"


def _has_column(db, table: str, col: str) -> bool:
    return col in db[table].columns_dict


def _m_add_created_at(db) -> None:
    if not _has_column(db, "$table", "created_at"):
        db["$table"].add_column("created_at", str)


def _m_backfill_created_at(db) -> None:
    db.execute(
        "UPDATE $table SET created_at = ? WHERE created_at IS NULL", [BACKFILL_DATE]
    )
    db.conn.commit()


def _m_add_extra(db) -> None:
    if not _has_column(db, "$table", "$extra_name"):
        db["$table"].add_column("$extra_name", $extra_pytype)
        db.execute(
            "UPDATE $table SET $extra_name = $extra_default_sql WHERE $extra_name IS NULL"
        )
        db.conn.commit()


def _m_index_flag(db) -> None:
    db["$table"].create_index(
        ["$flag"], index_name="$index_name", if_not_exists=True
    )


MIGRATIONS = [
    ("001_add_created_at", _m_add_created_at),
    ("002_backfill_created_at", _m_backfill_created_at),
    ("$m3_name", _m_add_extra),
    ("$m4_name", _m_index_flag),
]


def _ensure_tracking(db) -> None:
    if "_migrations" not in db.table_names():
        db["_migrations"].create({"name": str, "applied_at": str}, pk="name")


def applied(db) -> set[str]:
    _ensure_tracking(db)
    return {r["name"] for r in db["_migrations"].rows}


def run_migrations(db) -> list[str]:
    _ensure_tracking(db)
    done = applied(db)
    for name, fn in MIGRATIONS:
        if name not in done:
            fn(db)
            db["_migrations"].insert({"name": name, "applied_at": BACKFILL_DATE})
            done.add(name)
    return sorted(done)
''')

APP = string.Template('''from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

import migrations
import models

BASE = Path(__file__).parent
templates = Jinja2Templates(directory=str(BASE / "templates"))

app = FastAPI()
APP_NAME = "$app"


@app.on_event("startup")
def _startup() -> None:
    db = models.get_db()
    models.init_db(db)
    migrations.run_migrations(db)


def _db():
    return models.get_db()


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request, "home.html", {"app_name": APP_NAME})


@app.get("$route", response_class=HTMLResponse)
def listing(request: Request):
    return templates.TemplateResponse(
        request, "list.html", {"app_name": APP_NAME, "rows": models.list_rows(_db())}
    )


@app.post("$route")
def create($form_params):
    models.add_row(_db(), $form_call_args)
    return RedirectResponse("$route", status_code=303)


@app.post("$route/{$id_param}/$on")
def flag_on($id_param: int):
    models.set_flag(_db(), $id_param, True)
    return RedirectResponse("$route", status_code=303)


@app.post("$route/{$id_param}/$off")
def flag_off($id_param: int):
    models.set_flag(_db(), $id_param, False)
    return RedirectResponse("$route", status_code=303)


@app.get("/summary")
def summary():
    return JSONResponse(models.summary(_db()))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", reload=True)
''')

BASE_HTML = string.Template('''<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{% block title %}{{ app_name }}{% endblock %}</title>
  </head>
  <body>
    <nav>
      <a href="/">{{ app_name }}</a>
      <a href="$route">$nav</a>
    </nav>
    {% block content %}{% endblock %}
  </body>
</html>
''')

HOME_HTML = string.Template('''{% extends "base.html" %}
{% block content %}
<h1>{{ app_name }}</h1>
<p>$tagline</p>
{% endblock %}
''')

LIST_HTML = string.Template('''{% extends "base.html" %}
{% block content %}
<h1>$nav</h1>
<ul>
  {% for r in rows %}
  <li>$list_line{% if r.$flag %} ($flag){% endif %}</li>
  {% endfor %}
</ul>
<form method="post" action="$route">
$form_inputs
  <button type="submit">Add</button>
</form>
{% endblock %}
''')

TASK = string.Template('''# $app — a $domain app

Build a small FastAPI application called $app, backed by a SQLite database
(use `sqlite-utils`). Implement ALL of the following — every route, column,
status code, and migration.

## Pages and routes
- `app.py` with a FastAPI app instance.
- `templates/base.html` — a shared Jinja2 layout: HTML5 doctype,
  `<html lang="en">`, a title block defaulting to the app name, and a navbar
  linking Home (`/`) and $nav (`$route`).
- `GET /` returns a home page that extends the layout and shows the app name
  "$app".
- `GET $route` lists every row ($field_list), ordered by id, and renders an
  add form.

## Create (exact redirect)
- `POST $route` reads form fields $field_backticks, inserts a new row, and
  redirects to `GET $route` using status code 303.

## $on_cap and $off_cap (both endpoints)
- `POST $route/{$id_param}/$on` sets `$flag` to 1 and redirects to `$route`
  with status 303.
- `POST $route/{$id_param}/$off` sets `$flag` to 0 and redirects to `$route`
  with status 303.

## Migrations (write, apply, record, idempotent)
Put migrations in `migrations.py` and apply them at startup. Track applied
migrations in a `_migrations` table so re-running is a no-op.
- `001_add_created_at` — add a `created_at` text column.
- `002_backfill_created_at` — set `created_at` to `2026-01-01T00:00:00`
  wherever it is null.
- `$m3_name` — add a `$extra_name` $extra_word column defaulting to $extra_default_doc.
- `$m4_name` — create an index named `$index_name` on `$table($flag)`.
Running the migrations twice must not error, duplicate a column, or re-record a
migration.

## Summary API (exact JSON)
- `GET /summary` returns JSON with exactly the keys `total`, `$flag`,
  `un$flag`, all integers, where `total == $flag + un$flag`.
''')

CHECKS = string.Template('''"""Per-requirement checker for the $app golden task (generated)."""
import os
import sys
import tempfile
from pathlib import Path

REF = Path(__file__).parent / "reference"
sys.path.insert(0, str(REF))

_DB = tempfile.mktemp(suffix=".db")
os.environ["$db_env"] = _DB

import sqlite_utils  # noqa: E402
from starlette.testclient import TestClient  # noqa: E402

import app as appmod  # noqa: E402
import migrations  # noqa: E402
import models  # noqa: E402

models.init_db(models.get_db())
migrations.run_migrations(models.get_db())
client = TestClient(appmod.app)


def _db():
    return sqlite_utils.Database(_DB)


def _fresh():
    db = sqlite_utils.Database(tempfile.mktemp(suffix=".db"))
    models.init_db(db)
    migrations.run_migrations(db)
    return db


def test_home_ok_and_names_app():
    r = client.get("/")
    assert r.status_code == 200
    assert "$app" in r.text


def test_listing_shows_seed():
    r = client.get("$route")
    assert r.status_code == 200
    assert "$display_check" in r.text


def test_create_redirects_303_and_appears():
    r = client.post("$route", data=$new_literal, follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == "$route"
    assert "$expect" in client.get("$route").text


def test_flag_on_redirects_303():
    r = client.post("$route/$flag_id/$on", follow_redirects=False)
    assert r.status_code == 303
    assert _db()["$table"].get($flag_id)["$flag"] == 1


def test_flag_off_redirects_303():
    client.post("$route/$flag_id/$on", follow_redirects=False)
    r = client.post("$route/$flag_id/$off", follow_redirects=False)
    assert r.status_code == 303
    assert _db()["$table"].get($flag_id)["$flag"] == 0


def test_migration_index_exists():
    names = {i.name for i in _fresh()["$table"].indexes}
    assert "$index_name" in names


def test_migration_extra_column_added():
    assert "$extra_name" in _fresh()["$table"].columns_dict


def test_migration_created_at_backfilled():
    nulls = _fresh().execute(
        "select count(*) from $table where created_at is null"
    ).fetchone()[0]
    assert nulls == 0


def test_migrations_are_recorded():
    names = {r["name"] for r in _fresh()["_migrations"].rows}
    assert names == {"001_add_created_at", "002_backfill_created_at", "$m3_name", "$m4_name"}


def test_rerunning_migrations_is_a_noop():
    db = _fresh()
    cols_before = len(db["$table"].columns_dict)
    mig_before = db["_migrations"].count
    migrations.run_migrations(db)
    migrations.run_migrations(db)
    assert len(db["$table"].columns_dict) == cols_before
    assert db["_migrations"].count == mig_before


def test_summary_exact_shape_and_sums():
    s = client.get("/summary").json()
    assert set(s.keys()) == {"total", "$flag", "un$flag"}
    assert all(isinstance(v, int) for v in s.values())
    assert s["total"] == s["$flag"] + s["un$flag"]
''')


def _ctx(spec: dict) -> dict:
    fields = spec["fields"]  # [[name, type], ...]
    fnames = [n for n, _ in fields]
    flag = spec["flag"]["field"]
    on, off = spec["flag"]["on"], spec["flag"]["off"]
    ename, etype, edefault = spec["extra"]
    table = spec["table"]
    colspec = (
        "{"
        + ", ".join(
            ['"id": int'] + [f'"{n}": {PYT[t]}' for n, t in fields] + [f'"{flag}": int']
        )
        + "}"
    )
    extra_default_sql = f"'{edefault}'" if etype == "str" else str(edefault)
    return {
        "app": spec["app"],
        "domain": spec["domain"],
        "db_env": spec["db_env"],
        "db_file": spec["db_file"],
        "table": table,
        "route": spec["route"],
        "id_param": spec["id_param"],
        "nav": spec["nav"],
        "tagline": spec["tagline"],
        "flag": flag,
        "on": on,
        "off": off,
        "on_cap": on.capitalize(),
        "off_cap": off.capitalize(),
        "flag_id": "2",
        "colspec": colspec,
        "seed": repr(spec["seed"]),
        "add_args": ", ".join(fnames),
        "insert_dict": "{"
        + ", ".join([f'"{n}": {n}' for n in fnames] + [f'"{flag}": 0'])
        + "}",
        "form_params": ", ".join(f"{n}: {PYT[t]} = Form(...)" for n, t in fields),
        "form_call_args": ", ".join(fnames),
        "extra_name": ename,
        "extra_pytype": PYT[etype],
        "extra_default_sql": extra_default_sql,
        "extra_word": "text" if etype == "str" else "integer",
        "extra_default_doc": f"`{edefault}`" if etype == "str" else str(edefault),
        "m3_name": f"003_add_{ename}",
        "m4_name": f"004_index_{flag}",
        "index_name": f"idx_{table}_{flag}",
        "list_line": " — ".join("{{ r.%s }}" % n for n in fnames),
        "form_inputs": "\n".join('  <input name="%s" />' % n for n in fnames),
        "field_list": ", ".join(fnames),
        "field_backticks": ", ".join("`%s`" % n for n in fnames),
        "display_check": str(spec["seed"][0][fnames[0]]),
        "new_literal": repr(spec["new"]),
        "expect": str(spec["new"][fnames[0]]),
    }


def _meta(spec: dict, ctx: dict) -> str:
    reqs = [
        "GET / home page shows the app name",
        f"GET {spec['route']} lists rows and renders an add form",
        f"POST {spec['route']} creates a row and redirects 303 to {spec['route']}",
        f"POST {spec['route']}/{{id}}/{ctx['on']} sets {ctx['flag']}=1 and redirects 303",
        f"POST {spec['route']}/{{id}}/{ctx['off']} sets {ctx['flag']}=0 and redirects 303",
        f"migration {ctx['m4_name']} creates {ctx['index_name']}",
        f"migration {ctx['m3_name']} adds the {ctx['extra_name']} column",
        "migration 002_backfill_created_at leaves no null created_at",
        "all four migrations recorded in _migrations",
        "re-running migrations is a no-op",
        f"GET /summary returns exact integer keys total/{ctx['flag']}/un{ctx['flag']}",
    ]
    return json.dumps(
        {
            "domain": spec["domain"],
            "app_name": spec["app"],
            "stack": ["fastapi", "jinja2", "sqlite-utils"],
            "generated": True,
            "requirements": reqs,
            "shapes": [
                "second-endpoint-of-a-pair",
                "exact-status-code",
                "write-apply-track-idempotent-migration",
                "exact-json-shape",
            ],
        },
        indent=2,
    )


def render(spec: dict) -> None:
    ctx = _ctx(spec)
    base = TASKS / spec["name"]
    ref = base / "reference"
    (ref / "templates").mkdir(parents=True, exist_ok=True)
    (ref / "models.py").write_text(MODELS.substitute(ctx))
    (ref / "migrations.py").write_text(MIGR.substitute(ctx))
    (ref / "app.py").write_text(APP.substitute(ctx))
    (ref / "templates" / "base.html").write_text(BASE_HTML.substitute(ctx))
    (ref / "templates" / "home.html").write_text(HOME_HTML.substitute(ctx))
    (ref / "templates" / "list.html").write_text(LIST_HTML.substitute(ctx))
    (base / "task.md").write_text(TASK.substitute(ctx))
    (base / "checks.py").write_text(CHECKS.substitute(ctx))
    (base / "meta.json").write_text(_meta(spec, ctx) + "\n")


def main() -> int:
    base = json.loads((ROOT / "catalog.json").read_text())
    specs = expand(base)
    if TASKS.exists():
        for d in TASKS.iterdir():
            if d.is_dir():
                shutil.rmtree(d)
    for spec in specs:
        render(spec)
    print(f"generated {len(specs)} task(s) from {len(base)} base domains into {TASKS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
