import os
import sys
import shlex
import subprocess


def findExecutable(command):
    paths = os.getenv("PATH", "").split(os.pathsep)
    for path in paths:
        executablePath = os.path.join(path, command)
        if os.path.isfile(executablePath):
            return executablePath
    return None


def main():
    while True:
        sys.stdout.write("$ ")
        command = input()
        if command == "exit 0":
            sys.exit(0)
        elif command == "pwd":
            print(os.getcwd())
        elif command.startswith("cd"):
            args = command.split(" ")
            if len(args) > 1:
                paths = args[1].strip()
            else:
                paths = os.path.expanduser("~")
            # handle `~` character.
            if paths.startswith("~"):
                paths = os.path.expanduser(paths)
            try:
                os.chdir(paths)
            except Exception:
                print(f"cd: {paths}: No such file or directory")
        elif command.startswith("echo"):
            if command.startswith("'") and command.endswith("'"):
                message = command[6:-1]
                print(message)
            else:
                parts = shlex.split(command[5:])
                print(" ".join(parts))
        elif command.startswith("type"):
            seriesCommand = command.split(" ")
            builtinCommand = seriesCommand[1]
            if builtinCommand in ("echo", "exit", "type", "pwd", "cd"):
                print(f"{builtinCommand} is a shell builtin")
            else:
                executablePath = findExecutable(builtinCommand)
                if executablePath:
                    print(f"{builtinCommand} is {executablePath}")
                else:
                    print(f"{builtinCommand}: not found")
        else:
            # Check for output redirection
            if '>' in command:
                parts = command.split('>')
                command_to_run = parts[0].strip()  # The command before the >
                output_file = parts[1].strip() if len(parts) > 1 else None  # The file to redirect to

                # Prepare the command arguments
                args = shlex.split(command_to_run)

                # Run the command and redirect output
                if output_file:
                    with open(output_file, 'w') as f:
                        result = subprocess.run(args, stdout=f, stderr=subprocess.STDOUT)
            else:
                args = shlex.split(command)
                executablePath = findExecutable(args[0])
                if executablePath:
                    result = subprocess.run(args, capture_output=True, text=True)
                    print(result.stdout, end="")
                else:
                    print(f"{command}: command not found")


if __name__ == "__main__":
    main()
    