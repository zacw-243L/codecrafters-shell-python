from collections.abc import Mapping
import readline
import shlex
import subprocess
import sys
import pathlib
import os
from typing import Final, TextIO
from io import StringIO

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

            if "|" in cmds:
                parts = []
                current = []
                for tok in cmds:
                    if tok == "|":
                        parts.append(current)
                        current = []
                    else:
                        current.append(tok)
                parts.append(current)
                execute_pipeline_parts(parts, out, err)
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


def is_builtin(cmd: str) -> bool:
    return cmd in SHELL_BUILTINS


def execute_single_command(cmd: list[str], stdin: TextIO, stdout: TextIO, stderr: TextIO):
    if not cmd:
        return
    if is_builtin(cmd[0]):
        original_stdin = sys.stdin
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        sys.stdin = stdin
        sys.stdout = stdout
        sys.stderr = stderr
        try:
            handle_all(cmd, stdout, stderr)
        finally:
            sys.stdin = original_stdin
            sys.stdout = original_stdout
            sys.stderr = original_stderr
    elif cmd[0] in PROGRAMS_IN_PATH:
        subprocess.run(cmd, stdin=stdin, stdout=stdout, stderr=stderr)
    else:
        stderr.write(f"{cmd[0]}: command not found\n")


def execute_pipeline_parts(commands: list[list[str]], final_out: TextIO, final_err: TextIO):
    processes = []
    num_cmds = len(commands)
    prev_read = None

    for i, cmd in enumerate(commands):
        if i == 0:
            read_end, write_end = os.pipe()
            if is_builtin(cmd[0]):
                with os.fdopen(write_end, 'w') as w:
                    execute_single_command(cmd, sys.stdin, w, final_err)
                prev_read = os.fdopen(read_end)
            else:
                p = subprocess.Popen(cmd, stdout=write_end, stderr=final_err, close_fds=True)
                os.close(write_end)
                prev_read = os.fdopen(read_end)
                processes.append(p)
        elif i == num_cmds - 1:
            execute_single_command(cmd, prev_read, final_out, final_err)
            if prev_read:
                prev_read.close()
        else:
            read_end, write_end = os.pipe()
            if is_builtin(cmd[0]):
                with os.fdopen(write_end, 'w') as w:
                    execute_single_command(cmd, prev_read, w, final_err)
                if prev_read:
                    prev_read.close()
                prev_read = os.fdopen(read_end)
            else:
                p = subprocess.Popen(cmd, stdin=prev_read, stdout=write_end, stderr=final_err, close_fds=True)
                if prev_read:
                    prev_read.close()
                os.close(write_end)
                prev_read = os.fdopen(read_end)
                processes.append(p)

    for p in processes:
        p.wait()


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
