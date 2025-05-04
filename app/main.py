from collections.abc import Mapping
import readline
import shlex
import subprocess
import sys
import pathlib
import os
from typing import Final, TextIO

SHELL_BUILTINS: Final[list[str]] = [
    "echo",
    "exit",
    "type",
    "pwd",
    "cd",
]


def parse_programs_in_path(path: str, programs: dict[str, pathlib.Path]) -> None:
    p = pathlib.Path(path)
    if p.exists() and p.is_dir():
        for b in p.iterdir():
            if b.is_file() and os.access(b, os.X_OK):
                programs[b.name] = b


def generate_program_paths() -> Mapping[str, pathlib.Path]:
    programs: dict[str, pathlib.Path] = {}
    for p in (os.getenv("PATH") or "").split(":"):
        parse_programs_in_path(p, programs)
    return programs


PROGRAMS_IN_PATH: Final[Mapping[str, pathlib.Path]] = {**generate_program_paths()}
COMPLETIONS: Final[list[str]] = [*SHELL_BUILTINS, *PROGRAMS_IN_PATH.keys()]


def display_matches(substitution, matches, longest_match_length):
    print()
    if matches:
        print("  ".join(matches))
    print("$ " + substitution, end="")


def complete(text: str, state: int) -> str | None:
    matches = list(set([s for s in COMPLETIONS if s.startswith(text)]))
    if len(matches) == 1:
        return matches[state] + " " if state < len(matches) else None
    return matches[state] if state < len(matches) else None


readline.set_completion_display_matches_hook(display_matches)
readline.parse_and_bind("tab: complete")
readline.set_completer(complete)


def main():
    while True:
        sys.stdout.write("$ ")
        cmds = shlex.split(input())
        out = sys.stdout
        err = sys.stderr
        close_out = False
        close_err = False
        try:
            # Redirection (stdout, stderr)
            for symbol, mode, stream, close_flag in [
                (">", "w", "out", "close_out"),
                ("1>", "w", "out", "close_out"),
                ("2>", "w", "err", "close_err"),
                (">>", "a", "out", "close_out"),
                ("1>>", "a", "out", "close_out"),
                ("2>>", "a", "err", "close_err"),
            ]:
                if symbol in cmds:
                    idx = cmds.index(symbol)
                    f = open(cmds[idx + 1], mode)
                    if stream == "out":
                        out = f
                        close_out = True
                    else:
                        err = f
                        close_err = True
                    cmds = cmds[:idx] + cmds[idx + 2:]

            # Pipeline support
            if "|" in cmds:
                pipe_idx = cmds.index("|")
                lhs = cmds[:pipe_idx]
                rhs = cmds[pipe_idx + 1:]
                execute_pipeline(lhs, rhs, out, err)
            else:
                handle_all(cmds, out, err)
        finally:
            if close_out:
                out.close()
            if close_err:
                err.close()


def handle_all(cmds: list[str], out: TextIO, err: TextIO):
    match cmds:
        case ["echo", *s]:
            out.write(" ".join(s) + "\n")
        case ["type", s]:
            type_command(s, out, err)
        case ["exit", "0"]:
            sys.exit(0)
        case ["pwd"]:
            out.write(f"{os.getcwd()}\n")
        case ["cd", dir]:
            cd(dir, out, err)
        case [cmd, *args] if cmd in PROGRAMS_IN_PATH:
            process = subprocess.Popen([cmd, *args], stdout=out, stderr=err)
            process.wait()
        case command:
            out.write(f"{' '.join(command)}: command not found\n")


def execute_pipeline(cmd1: list[str], cmd2: list[str], out: TextIO, err: TextIO):
    try:
        p1 = subprocess.Popen(cmd1, stdout=subprocess.PIPE, stderr=err)
        p2 = subprocess.Popen(cmd2, stdin=p1.stdout, stdout=out, stderr=err)
        p1.stdout.close()
        p1.wait()
        p2.wait()
    except Exception as e:
        err.write(f"Pipeline error: {e}\n")


def type_command(command: str, out: TextIO, err: TextIO):
    if command in SHELL_BUILTINS:
        out.write(f"{command} is a shell builtin\n")
        return
    if command in PROGRAMS_IN_PATH:
        out.write(f"{command} is {PROGRAMS_IN_PATH[command]}\n")
        return
    out.write(f"{command}: not found\n")


def cd(path: str, out: TextIO, err: TextIO) -> None:
    if path.startswith("~"):
        home = os.getenv("HOME") or "/root"
        path = path.replace("~", home)
    p = pathlib.Path(path)
    if not p.exists():
        out.write(f"cd: {path}: No such file or directory\n")
        return
    os.chdir(p)


if __name__ == "__main__":
    main()
