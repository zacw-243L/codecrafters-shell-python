import sys
import shutil
import subprocess

BUILTIN_CMD = {"exit", "echo", "type", "cd", "pwd"}


def type_cmd(command):
    if command in BUILTIN_CMD:
        print(f"{command} is a shell builtin")
    elif path := shutil.which(command):
        print(f"{command} is {path}")
    else:
        print(f"{command}: not found")


def run_external_command(command):
    try:
        # Execute the command and capture the output
        result = subprocess.run(command, check=True, text=True, capture_output=True)
        print(result.stdout, end='')  # Print the output from the command
    except subprocess.CalledProcessError as e:
        print(f"{e.cmd}: command failed with exit code {e.returncode}")


def main():
    while True:
        sys.stdout.write("$ ")
        command = input()
        match command.split():
            case ["exit", "0"]:
                exit()
            case ["echo", *args]:
                print(*args)
            case ["type", cmd]:
                type_cmd(cmd)
            case _:
                # Split the command into a list for external execution
                external_command = command.split()
                run_external_command(external_command)


if __name__ == "__main__":
    main()
