# shortcuts.py
import subprocess
import shlex
from typing import Dict

def run_command(command: str) -> None:
    """Execute the given command safely."""
    try:
        # Split the command respecting quoted arguments
        args = shlex.split(command, posix=False)
        subprocess.run(args, check=False, shell=False)
    except Exception as exc:
        print(f"[Thud] failed to run '{command}': {exc}")
