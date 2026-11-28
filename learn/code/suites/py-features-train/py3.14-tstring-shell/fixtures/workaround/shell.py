"""Shell command building."""
import shlex


def command(line) -> str:
    return shlex.join(str(line).split())
