"""Shell command building."""
import shlex
from string.templatelib import Interpolation, Template


def command(line: Template) -> str:
    return "".join(shlex.quote(str(p.value)) if isinstance(p, Interpolation) else p for p in line)
