import sys
import os
import subprocess
import re
import shlex
import readline


def main():
    builtins = ['echo', 'exit', 'type', 'pwd', 'cd']
    readline.set_completion_display_matches_hook(display_matches)
    readline.parse_and_bind("tab: complete")
    readline.set_completer(completer)

    while True:
        sys.stdout.write("$ ")
        command = input()

        if "2>>" in command:
            parts = shlex.split(command)
            split_index = parts.index("2>>")
            command_args = parts[:split_index]
            error_file = parts[split_index + 1]
            with open(error_file, "a") as f:
                result = subprocess.run(
                    command_args, stderr=f, text=True
                )
            continue
        if "1>>" in command or ">>" in command:
            parts = shlex.split(command)
            if "1>>" in parts:
                split_index = parts.index("1>>")
            else:
                split_index = parts.index(">>")
            command_args = parts[:split_index]
            error_file = parts[split_index + 1]
            with open(error_file, "a") as f:
                result = subprocess.run(
                    command_args, stdout=f, text=True
                )
            continue
        if "2>" in command:
            parts = shlex.split(command)
            split_index = parts.index("2>")
            command_args = parts[:split_index]
            error_file = parts[split_index + 1]
            with open(error_file, "w") as f:
                result = subprocess.run(
                    command_args, stderr=f, text=True
                )
            continue
        if ">" in command or "1>" in command:
            parts = shlex.split(command)
            if ">" in parts:
                split_index = parts.index(">")
            else:
                split_index = parts.index("1>")
            command_args = parts[:split_index]
            output_file = parts[split_index + 1]
            with open(output_file, "w") as f:
                result = subprocess.run(
                    command_args, stdout=f, text=True
                )
            continue
        if command == "exit 0":
            sys.exit(0)
        elif command.startswith('echo'):
            # print(echo(command))
            echo(command)
        elif command.startswith('type'):
            print(type(command))
        elif command.startswith('pwd'):
            print(pwd(command))
        elif command.startswith('cd'):
            cd(command)
        else:
            commands = shlex.split(command, posix=True)
            command_name = commands[0]
            args = commands[1:]
            executable_path = find_executable(command_name)
            if executable_path:
                try:
                    command_name_only = os.path.basename(executable_path)
                    result = subprocess.run(
                        [command_name_only] + args, text=True
                    )
                except Exception as e:
                    print(f"Error executing {command[0]}: {e}")
            else:
                print(f"{command_name}: command not found")
        # input()


def display_matches(substitution, matches, longest_match_length):
    print()
    if matches:
        print("  ".join(matches))
    print("$ " + substitution, end="")


def get_path_executables():
    executables = []
    path_dirs = os.environ.get("PATH", "").split(":")

    for directory in path_dirs:
        if not directory:
            continue
        try:
            for item in os.listdir(directory):
                full_path = os.path.join(directory, item)
                if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
                    executables.append(item)
        except OSError:
            continue
    return executables


def completer(text, state):
    builtins = ['echo', 'exit', 'type', 'pwd', 'cd']
    all_commands = builtins + get_path_executables()
    matches = [cmd + "" for cmd in all_commands if cmd.startswith(text)]
    if len(matches) == 1:
        return matches[state] + " " if state < len(matches) else sys.stdout.write("\a")
    if matches[0] in builtins:
        return matches[state] + " " if state < len(matches) else sys.stdout.write("\a")
    return matches[state] if state < len(matches) else sys.stdout.write("\a")


def cd(command):
    command = command.split()
    path = command[1]
    if path == "~":
        try:
            os.chdir(os.environ["HOME"])
        except OSError:
            print(f"cd: {path}: No such file or directory")
    else:
        try:
            os.chdir(path)
        except OSError:
            print(f"cd: {path}: No such file or directory")


def pwd(command):
    full_path = os.path.abspath(command)
    dir_name = os.path.dirname(full_path)
    return dir_name


def find_executable(command):
    path_dirs = os.environ.get("PATH", "").split(":")
    for directory in path_dirs:
        possible_path = os.path.join(directory, command)
        if os.path.isfile(possible_path) and os.access(possible_path, os.X_OK):
            return possible_path
    return None


def echo(command):
    string = command.replace('echo ', '')
    if string.startswith("'") and string.endswith("'") and "\\" not in string:
        string = string.replace("'", "")
        print(string)
    elif string.startswith('"') and string.endswith('"') and "\\" not in string:
        string = string.replace(' "', '')
        string = string.replace('"', '')
        print(string)
    elif "\\" in string:
        if "\\" * 3 in string:
            string = string.strip('"')
            string = string.strip("'")
        elif "\\" * 2 in string:
            if string.startswith("'"):
                string = string.strip("'")
            else:
                string = string.replace('\\"', '"')
                string = string.replace('\\' * 2, '\\')
                string = string.strip('"')
        else:
            if string.startswith("'"):
                string = string.strip("'")
                string = string.replace('""', '"')
            else:
                string = string.replace('"', '')
                string = string.replace('\\n', 'n')
                string = string.strip('"')
                string = string.replace('\\', '"')
                string = string.replace('""', '"')
                string = string.replace('" ', ' ')
                string = string.replace('"\'"', '\'"')
        print(string)
    else:
        new_string = re.sub(r"\s+", " ", string)
        print(new_string)


def type(command):
    PATH = os.environ.get('PATH')
    cmd_path = None
    paths = PATH.split(':')
    type_list = ['type', 'echo', 'exit', 'pwd', 'cd']
    string = command.replace('type ', '')

    for path in paths:
        if os.path.isfile(f'{path}/{string}'):
            cmd_path = f'{string} is {path}/{string}'

    if string in type_list:
        if string == 'cat':
            message = f'{string} is {path}/{string}'
        else:
            message = f'{string} is a shell builtin'
        return message
    elif cmd_path:
        return cmd_path
    else:
        message = f'{string}: not found'
        return message


if __name__ == "__main__":
    main()