import sys
import os
import subprocess


def split_command(input_str):
    parts = input_str.split()
    if '>' in parts:
        idx = parts.index('>')
        cmd_args = parts[:idx]
        output_file = parts[idx + 1]
        return cmd_args, output_file
    return parts, None


def main():
    while True:
        sys.stdout.write("$ ")
        user_input = input().strip()
        if not user_input:
            continue

        # Split command and handle redirection
        cmd_args, output_file = split_command(user_input)
        if not cmd_args:
            continue

        # Handle built-in commands
        if cmd_args[0] == "cd":
            try:
                os.chdir(cmd_args[1] if len(cmd_args) > 1 else os.environ["HOME"])
            except Exception as e:
                print(f"cd: {e}", file=sys.stderr)
            continue
        elif cmd_args[0] == "pwd":
            output = os.getcwd()
        elif cmd_args[0] == "exit":
            break
        else:
            # Run external programs
            try:
                if output_file:
                    # Redirect stdout to the specified file
                    with open(output_file, 'w') as f:
                        subprocess.run(cmd_args, stdout=f, stderr=subprocess.PIPE, check=True, text=True)
                else:
                    # Capture and print output
                    result = subprocess.run(cmd_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                    print(result.stdout, end='')
                    if result.stderr:
                        print(result.stderr, file=sys.stderr, end='')
            except FileNotFoundError:
                print(f"{cmd_args[0]}: command not found", file=sys.stderr)
            except subprocess.CalledProcessError as e:
                print(e.stderr, file=sys.stderr, end='')


if __name__ == "__main__":
    main()
    