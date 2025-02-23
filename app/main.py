import os  # alot of stuff!
import sys  # for output , exit and other such stuff
from os.path import (
    abspath,
)  # to find the absolute path i.e. path from the home directory
import subprocess  # to run the executable files
import platform  # to check the for the current platform
import shlex  # to handle the quotes in the command line
import readline  # to use for autocompletion

built_in_commands = ["exit", "echo", "type", "pwd", "cd"]
PATH = os.environ["PATH"]  # makes a list of all the paths of the current environment
user_input = ""
user_command = []
paths = PATH.split(":")
executable_commands = []
for path in paths:
    try:
        for filename in os.listdir(path):
            fullpath = os.path.join(path, filename)
            if os.access(fullpath, os.X_OK):
                executable_commands.append(filename)
    except FileNotFoundError:
        pass


def redirecting(output, error):
    if output:
        sys.stdout.write(output + "\n")
        sys.stdout.flush()
    if error:
        sys.stderr.write(error + "\n")
        sys.stderr.flush()


def main():
    while True:
        text_parse_bind()
        readline.set_completer(auto_completer)
        readline.parse_and_bind("tab: complete")
        global user_input
        user_input = input("$ ")
        paths = PATH.split(":")
        global user_command
        user_command = shlex.split(user_input, posix=True)
        output = ""
        error = ""

        if user_input == "":
            pass
        else:
            if user_command[0] == "exit" and len(user_command) == 2:
                try:
                    sys.exit(int(user_command[1]))
                except ValueError:
                    sys.stdout.write("the exit code must be an integer\n")
            elif user_command[0] == "exit" and len(user_command) != 2:
                sys.stdout.write(
                    f"{user_command[0]} requires one argument, exit code.\n"
                )
            elif user_command[0] == "echo":
                if not any(op in user_command for op in [">", "1>", "2>", ">>", "1>>", "2>>"]):
                    output = " ".join(user_command[1:])
                    redirecting(output, error)
                else:
                    output = f"{user_command[1]}\n"
                    redirecting(output, error)
            elif user_command[0] == "type":
                if len(user_command) != 1:
                    command = user_command[1]
                    command_path = None
                    for path in reversed(paths):  # Ensure last match is returned
                        if os.path.isfile(f"{path}/{command}"):
                            command_path = f"{path}/{command}"
                    if len(user_command) != 2:
                        error = "type requires only one argument, command"
                    elif command in built_in_commands:
                        output = f"{command} is a shell builtin"
                    elif command_path:
                        output = f"{command} is {command_path}"
                    else:
                        error = f"{command}: not found"
                    redirecting(output, error)
                else:
                    error = "type requires one argument, command"
                    redirecting(output, error)
            elif user_command[0] == "pwd":
                output = f"{abspath(os.getcwd())}"
                redirecting(output, error)
            elif executable_file(user_command[0]):
                result = subprocess.run(user_command, capture_output=True, text=True)
                output = result.stdout
                error = result.stderr
                redirecting(output, error)
            elif user_command[0] == "cd":
                try:
                    new_path = user_command[1]
                    if platform.system() == "Windows":
                        if user_command[1][0] == "~":
                            new_path = user_command[1].replace("~", os.environ.get("USERPROFILE"))
                    elif platform.system() == "Linux":
                        if user_command[1][0] == "~":
                            new_path = user_command[1].replace("~", os.environ.get("HOME"))
                    os.chdir(new_path)
                except IndexError:
                    if len(user_command) == 1:
                        if platform.system() == "Windows":
                            new_path = os.environ.get("USERPROFILE")
                            os.chdir(new_path)
                        elif platform.system() == "Linux":
                            new_path = os.environ.get("HOME")
                            os.chdir(new_path)
                    else:
                        error = f"{user_command[0]} requires one argument, directory\n"
                    redirecting(output=None, error=error)
                except FileNotFoundError:
                    sys.stdout.write(
                        f"cd: {user_command[1]}: No such file or directory\n"
                    )
            else:
                sys.stdout.write(f"{user_command[0]}: command not found\n")
                sys.stdout.flush()


# checks if the file is an executable program
def executable_file(command: str):
    paths = PATH.split(":")
    for path in paths:
        if os.path.isfile(f"{path}/{command}"):
            return True


# autocompletes built-in commands
def auto_completer(text, state):
    matches = [match for match in built_in_commands if match.startswith(text)]
    matches_exec_cmd = [cmd for cmd in executable_commands if cmd.startswith(text)]
    for s in matches_exec_cmd:
        matches.append(s)
    if len(matches) > state:
        return f"{matches[state]} "
    else:
        return None


def text_parse_bind():
    readline.parse_and_bind("tab: complete")
    readline.parse_and_bind(r"'\C-a': beginning-of-line")
    readline.parse_and_bind(r"'\C-e': end-of-line")
    readline.parse_and_bind(r"'\C-r': reverse-search-history")
    readline.parse_and_bind(r"'\M-b': backward-word")
    readline.parse_and_bind(r"'\M-f': forward-word")
    readline.parse_and_bind(r"'\C-u': unix-line-discard")


if __name__ == "__main__":
    main()
