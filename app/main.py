import sys
import shutil
import subprocess
import os  # Importing os module for pwd functionality

BUILTIN_CMD = {"exit", "echo", "type", "pwd", "cd"}  # Added cd to the built-in commands


def type_cmd(command):
    if command in BUILTIN_CMD:
        print(f"{command} is a shell builtin")
    elif path := shutil.which(command):
        print(f"{command} is {path}")
    else:
        print(f"{command}: not found")  # Updated error message


def run_external_command(command):
    try:
        # Execute the command and capture the output
        result = subprocess.run(command, check=True, text=True, capture_output=True)
        print(result.stdout, end='')  # Print the output from the command
    except FileNotFoundError:
        print(f"{command[0]}: not found")  # Updated error message
    except subprocess.CalledProcessError as e:
        print(f"{e.cmd}: command failed with exit code {e.returncode}")


def change_directory(path):
    # Check if the path is ~ and change to the home directory
    if path == "~":
        path = os.path.expanduser("~")  # Get the home directory
    try:
        os.chdir(path)  # Change the current working directory
    except FileNotFoundError:
        print(f"cd: {path}: No such file or directory")  # Error message for invalid path


def main():
    while True:
        sys.stdout.write("$ ")
        command = input()
        match command.split():
            case ["exit", "0"]:
                exit(0)  # Exit with status code 0
            case ["echo", *args]:
                print(*args)
            case ["type", cmd]:
                type_cmd(cmd)
            case ["pwd"]:  # Handle pwd command
                print(os.getcwd())  # Print the current working directory
            case ["cd", path]:  # Handle cd command
                change_directory(path)  # Change the directory
            case _:
                # Split the command into a list for external execution
                external_command = command.split()
                run_external_command(external_command)


if __name__ == "__main__":
    main()
    