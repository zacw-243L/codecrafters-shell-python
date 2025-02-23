import sys
import os
import readline
import shlex
import subprocess


def completer(text, state):
    """Autocomplete function for built-in commands."""
    builtin = ["echo ", "exit ", "type ", "pwd ", "cd "]
    matches = [cmd for cmd in builtin if cmd.startswith(text)]
    return matches[state] if state < len(matches) else None


def main():
    builtin = ["echo", "exit", "type", "pwd", "cd"]
    PATH = os.environ.get("PATH")
    HOME = os.environ.get("HOME")  # Get the user's home directory
    # Set up autocomplete
    readline.set_completer(completer)
    readline.parse_and_bind("tab: complete")
    while True:
        # Prompt for input
        sys.stdout.write("$ ")
        sys.stdout.flush()
        try:
            # Read input and parse using shlex
            command_line = input().strip()
            if not command_line:
                continue
            # Handle stderr redirection (2>>)
            if "2>>" in command_line:
                parts = shlex.split(command_line)
                split_index = parts.index("2>>")
                command_args = parts[:split_index]
                error_file = parts[split_index + 1]
                with open(error_file, "a") as f:
                    result = subprocess.run(
                        command_args, stdout=subprocess.PIPE, stderr=f, text=True
                    )
                # Write any stdout output to the shell
                if result.stdout:
                    sys.stdout.write(result.stdout)
                    sys.stdout.flush()
                continue
            # Handle stdout redirection (>>) or (1>>)
            if ">>" in command_line or "1>>" in command_line:
                parts = shlex.split(command_line)
                if ">>" in parts:
                    split_index = parts.index(">>")
                else:
                    split_index = parts.index("1>>")
                command_args = parts[:split_index]
                output_file = parts[split_index + 1]
                with open(output_file, "a") as f:
                    result = subprocess.run(
                        command_args, stdout=f, stderr=subprocess.PIPE, text=True
                    )
                # Write any stderr output to the shell
                if result.stderr:
                    sys.stderr.write(result.stderr)
                    sys.stderr.flush()
                continue
            # Handle stderr redirection (2>)
            if "2>" in command_line:
                parts = shlex.split(command_line)
                split_index = parts.index("2>")
                command_args = parts[:split_index]
                error_file = parts[split_index + 1]
                with open(error_file, "w") as f:
                    result = subprocess.run(
                        command_args, stdout=subprocess.PIPE, stderr=f, text=True
                    )
                # Write any stdout output to the shell
                if result.stdout:
                    sys.stdout.write(result.stdout)
                    sys.stdout.flush()
                continue
            # Handle stdout redirection (>) or (1>)
            if ">" in command_line or "1>" in command_line:
                parts = shlex.split(command_line)
                if ">" in parts:
                    split_index = parts.index(">")
                else:
                    split_index = parts.index("1>")
                command_args = parts[:split_index]
                output_file = parts[split_index + 1]
                with open(output_file, "w") as f:
                    result = subprocess.run(
                        command_args, stdout=f, stderr=subprocess.PIPE, text=True
                    )
                # Write any stderr output to the shell
                if result.stderr:
                    sys.stderr.write(result.stderr)
                    sys.stderr.flush()
                continue
            args = shlex.split(
                command_line
            )  # Properly split command while handling quotes
            command = args[0]
            # Handle "exit"
            if command == "exit":
                sys.exit(0)
            # Handle "echo"
            elif command == "echo":
                output = " ".join(args[1:])
                sys.stdout.write(output + "\n")
                sys.stdout.flush()
            # Handle "pwd"
            elif command == "pwd":
                sys.stdout.write(os.getcwd() + "\n")
                sys.stdout.flush()
            # Handle "cd"
            elif command == "cd":
                # Default to HOME if no argument is provided
                directory = args[1] if len(args) > 1 else HOME
                # Handle ~ for home directory
                if directory == "~":
                    directory = HOME
                try:
                    os.chdir(directory)
                except FileNotFoundError:
                    sys.stderr.write(f"cd: {directory}: No such file or directory\n")
                except PermissionError:
                    sys.stderr.write(f"cd: {directory}: Permission denied\n")
                except Exception as e:
                    sys.stderr.write(f"cd: {directory}: {str(e)}\n")
                sys.stdout.flush()
            # Handle "type"
            elif command == "type":
                if len(args) < 2:
                    sys.stderr.write("type: missing argument\n")
                else:
                    new_command = args[1]
                    cmd_path = None
                    # Search for the command in PATH
                    for path in PATH.split(os.pathsep):
                        full_path = os.path.join(path, new_command)
                        if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
                            cmd_path = full_path
                            break
                    if new_command in builtin:
                        sys.stdout.write(f"{new_command} is a shell builtin\n")
                    elif cmd_path:
                        sys.stdout.write(f"{new_command} is {cmd_path}\n")
                    else:
                        sys.stderr.write(f"{new_command}: not found\n")
                sys.stdout.flush()
            # Handle external commands
            else:
                cmd_path = None
                # Search for the command in PATH
                for path in PATH.split(os.pathsep):
                    full_path = os.path.join(path, command)
                    if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
                        cmd_path = full_path
                        break
                if cmd_path:
                    try:
                        # Run the command with arguments
                        result = subprocess.run(args, capture_output=True, text=True)
                        sys.stdout.write(result.stdout)
                        sys.stderr.write(result.stderr)
                    except Exception as e:
                        sys.stderr.write(f"Error executing command: {e}\n")
                else:
                    sys.stderr.write(f"{command}: command not found\n")
                sys.stdout.flush()
        except EOFError:  # Handle Ctrl+D gracefully
            sys.stdout.write("\n")
            break
        except Exception as e:
            sys.stderr.write(f"Error: {e}\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
