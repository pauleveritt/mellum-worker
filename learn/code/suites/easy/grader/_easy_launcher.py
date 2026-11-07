"""Run the submitted launcher with real uvicorn, redirecting its listening port.

Only network binding is adapted. Config/Server/run all keep their real behavior,
including reload's child processes. Importable classes remain pickleable under
uvicorn's spawn context. This helper lives outside the submitted application.
"""

import importlib
import inspect
import json
import os
import runpy
import signal
import subprocess
import threading
import time
from pathlib import Path

import uvicorn


OriginalConfig = uvicorn.Config


def event(kind, **values):
    with Path(os.environ["EASY_LAUNCH_EVENTS"]).open("a") as output:
        output.write(json.dumps({"kind": kind, "pid": os.getpid(), **values}) + "\n")


class PortConfig(OriginalConfig):
    def __init__(self, *args, **kwargs):
        arguments = inspect.signature(OriginalConfig).bind(*args, **kwargs)
        arguments.arguments.update(host="127.0.0.1", port=int(os.environ["EASY_LAUNCH_PORT"]))
        super().__init__(**arguments.arguments)
        event("config", reload=self.reload)

    def load(self):
        super().load()
        event("loaded")


def run():
    # The hidden pytest parent may be forcibly stopped, bypassing its finally.
    # A separate session needs its own bound and parent-death cleanup.
    parent_pid = os.getppid()
    threading.Thread(target=_watch_parent, args=(parent_pid,), daemon=True).start()
    uvicorn.Config = PortConfig
    importlib.import_module("uvicorn.main").Config = PortConfig
    importlib.import_module("uvicorn.config").Config = PortConfig
    runpy.run_path("app.py", run_name="__main__")


def _watch_parent(parent_pid):
    handle, kernel = None, None
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        kernel.WaitForSingleObject.restype = wintypes.DWORD
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel.CloseHandle.restype = wintypes.BOOL
        handle = kernel.OpenProcess(0x00100000, False, parent_pid)
    deadline = time.monotonic() + 30
    try:
        while time.monotonic() < deadline:
            alive = bool(handle) and kernel.WaitForSingleObject(handle, 0) == 258 if kernel else os.getppid() == parent_pid
            if not alive:
                break
            time.sleep(0.1)
        if os.name == "nt":
            subprocess.run(["taskkill", "/PID", str(os.getpid()), "/T", "/F"], capture_output=True, timeout=3)
            os._exit(1)
        else:
            os.killpg(os.getpgrp(), signal.SIGKILL)
    finally:
        if handle:
            kernel.CloseHandle(handle)
