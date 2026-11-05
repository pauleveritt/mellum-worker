"""Native session isolation (LC.39): no containers, so sweep the session user and probe its reach.

On a pod each session runs as `mellum-session` and grading as `mellum-grade`
(rig.SESSION_USER, rig.GRADE_USER). After each, `sweep_user` kills everything that
user owns, checks no listener survives and resets the home. On the Mac, sessions
run as the operator: the sweep is scoped to the session's own process tree and a
home is never reset. Nothing here raises; a sweep reports what it could not clear.
"""
import os
import pwd
import shutil
import signal
import subprocess
import time
from pathlib import Path

from rig import GRADE_USER, SESSION_USER

RIG_USERS = {SESSION_USER, GRADE_USER}


def parse_lsof(text: str) -> list[dict]:
    """Parse `lsof -F pcun` field output into one row per listening socket."""
    rows, current = [], {}
    for line in text.splitlines():
        if not line:
            continue
        tag, value = line[0], line[1:]
        if tag == "p":
            current = {"pid": int(value)}
        elif tag == "c":
            current["command"] = value
        elif tag == "u":
            current["uid"] = int(value)
        elif tag == "n" and "pid" in current:
            port = value.rsplit(":", 1)[-1]
            rows.append({**current, "address": value, "port": int(port) if port.isdigit() else None})
    return rows


def listeners(uid: int | None = None) -> list[dict]:
    try:
        out = subprocess.run(["lsof", "-nP", "-iTCP", "-sTCP:LISTEN", "-F", "pcun"],
                             capture_output=True, text=True, timeout=30).stdout
    except (OSError, subprocess.TimeoutExpired):
        return []
    rows = parse_lsof(out)
    return [row for row in rows if uid is None or row.get("uid") == uid]


def _processes() -> list[tuple[int, int, int, str]]:
    try:
        out = subprocess.run(["ps", "-axo", "pid=,ppid=,uid=,stat=,comm="], capture_output=True, text=True,
                             timeout=30).stdout
    except (OSError, subprocess.TimeoutExpired):
        return []
    rows = []
    for line in out.splitlines():
        parts = line.split(None, 4)
        # A zombie holds no sockets or files; it only waits for its parent to reap it.
        if len(parts) == 5 and parts[0].isdigit() and not parts[3].startswith("Z"):
            rows.append((int(parts[0]), int(parts[1]), int(parts[2]), parts[4]))
    return rows


def user_processes(uid: int, roots: set[int] | None = None) -> list[tuple[int, str]]:
    """Processes owned by uid; with roots, only those roots and their descendants."""
    rows = [row for row in _processes() if row[2] == uid and row[0] != os.getpid()]
    if roots is None:
        return [(pid, command) for pid, _, _, command in rows]
    scope, changed = set(roots), True
    while changed:
        changed = False
        for pid, ppid, _, _ in rows:
            if ppid in scope and pid not in scope:
                scope.add(pid)
                changed = True
    return [(pid, command) for pid, _, _, command in rows if pid in scope]


def _signal(pid: int, number: int):
    try:
        os.kill(pid, number)
    except (ProcessLookupError, PermissionError):
        pass


def sweep_user(name: str, *, grace: float = 1.0, roots: set[int] | None = None) -> dict:
    try:
        account = pwd.getpwnam(name)
    except KeyError:
        return {"killed": [], "listeners_after": [], "home_reset": False, "ok": False, "error": "no such user"}
    targets = user_processes(account.pw_uid, roots)
    for pid, _ in targets:
        _signal(pid, signal.SIGTERM)
    until = time.monotonic() + grace
    while time.monotonic() < until and user_processes(account.pw_uid, roots):
        time.sleep(0.05)
    for pid, _ in user_processes(account.pw_uid, roots):
        _signal(pid, signal.SIGKILL)
    time.sleep(0.1)
    remaining = user_processes(account.pw_uid, roots)
    in_scope = {pid for pid, _ in targets} | {pid for pid, _ in remaining}
    after = [row for row in listeners(account.pw_uid) if roots is None or row["pid"] in in_scope]
    home_reset = False
    if name in RIG_USERS and roots is None and not remaining:
        home = Path(account.pw_dir)
        try:
            shutil.rmtree(home, ignore_errors=True)
            home.mkdir(mode=0o700)
            os.chown(home, account.pw_uid, account.pw_gid)
            home_reset = True
        except OSError:
            home_reset = False
    ok = not remaining and not after and (home_reset or name not in RIG_USERS or roots is not None)
    return {"killed": targets, "remaining": remaining, "listeners_after": after, "home_reset": home_reset, "ok": ok}


def preflight_mac(ports: list[int] | None = None) -> dict:
    """The Mac has no session user: refuse to start while a port the session needs is taken."""
    taken = [row for row in listeners() if ports is None or row.get("port") in set(ports)]
    return {"ok": not taken, "listeners": taken}


def _permits(info: os.stat_result, uid: int, gids: set[int], bit: int) -> bool:
    """Whether uid (with supplementary/primary gids) has permission `bit` (4 read, 1 execute) on a file."""
    if info.st_uid == uid:
        return bool(info.st_mode & (bit << 6))
    if info.st_gid in gids:
        return bool(info.st_mode & (bit << 3))
    return bool(info.st_mode & bit)


def reachable(path: Path, uid: int, gids: set[int]) -> bool:
    """Whether uid could read path: every parent must be traversable and the file itself readable."""
    path = Path(path).absolute()
    try:
        for parent in reversed(path.parents):
            if not _permits(parent.stat(), uid, gids, 1):
                return False
        return _permits(path.stat(), uid, gids, 4)
    except FileNotFoundError:
        return False


def isolation_probe(session_user: str, protected: list[Path], pids: list[int]) -> dict:
    """What the session user could reach: protected files it can read, processes it can signal."""
    try:
        account = pwd.getpwnam(session_user)
    except KeyError:
        return {"ok": False, "findings": [{"kind": "no_user", "user": session_user}]}
    uid, gids = account.pw_uid, {account.pw_gid}   # sessions run with their primary group only (drop_privileges)
    findings = []
    for path in protected:
        if reachable(Path(path), uid, gids):
            findings.append({"kind": "readable", "path": str(path)})
    owners = {pid: owner for pid, _, owner, _ in _processes()}
    for pid in pids:
        if owners.get(pid) == uid:
            findings.append({"kind": "signalable", "pid": pid})
    return {"ok": not findings, "findings": findings}
