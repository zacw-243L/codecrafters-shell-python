#qddaw

import sys
import os
import shutil
import subprocess
from pathlib import Path
from copy import copy
import readline


def parser(string, as_list=False):
    string_builder = str()
    result = []

    is_single_quoted = False
    is_double_quoted = False
    is_escaped = False

    for x, char in enumerate(string):
        if is_escaped:
            is_escaped = False
            continue

        if char == "'":
            if is_double_quoted:
                string_builder += char
            elif is_single_quoted:
                is_single_quoted = False
            else:
                is_single_quoted = True
            continue

        if char == '"':
            if is_single_quoted:
                string_builder += char
            elif is_double_quoted:
                is_double_quoted = False
            else:
                is_double_quoted = True
            continue

        if ord(char) == 92:
            if is_single_quoted:
                string_builder += char
            elif is_double_quoted:
                if string[x + 1] in (chr(92), '$', '"'):
                    string_builder += string[x + 1]
                    is_escaped = True
                else:
                    string_builder += char
            else:
                string_builder += string[x + 1]
                is_escaped = True
            continue

        if not any([is_single_quoted, is_double_quoted]):
            if char == ' ':
                result.append(string_builder)
                string_builder = str()
            else:
                string_builder += char
        else:
            string_builder += char

    result.append(string_builder)
    while '' in result:
        result.remove('')

    return result if as_list else ' '.join(result)


def check_for_file_to_write(command):
    write_list = ['>', '1>', '2>', '>>', '1>>', '2>>']
    append = False
    err_flag = False

    # Determine if the command contains any redirection operator
    for x, symbol in enumerate(command):
        if symbol == '>' and x:
            if command[x - 1] == '2':
                err_flag = True
                break

    if any(x in command for x in write_list):
        # Handle redirection operators in order of specificity
        if '2>>' in command:
            io_splitter = command.split('2>>', 1)
            write_command = io_splitter[0].strip()
            output_file = io_splitter[1].strip()
            append = True
            err_flag = True
        elif '2>' in command:
            io_splitter = command.split('2>', 1)
            write_command = io_splitter[0].strip()
            output_file = io_splitter[1].strip()
            append = False
            err_flag = True
        elif '1>>' in command:
            io_splitter = command.split('1>>', 1)
            write_command = io_splitter[0].strip()
            output_file = io_splitter[1].strip()
            append = True
        elif '>>' in command:
            io_splitter = command.split('>>', 1)
            write_command = io_splitter[0].strip()
            output_file = io_splitter[1].strip()
            append = True
        elif '1>' in command:
            io_splitter = command.split('1>', 1)
            write_command = io_splitter[0].strip()
            output_file = io_splitter[1].strip()
            append = False
        else:
            io_splitter = command.split('>', 1)
            write_command = io_splitter[0].strip()
            output_file = io_splitter[1].strip()
            append = False
    else:
        return (command, None, False, False)

    return (write_command, output_file, append, err_flag)


def write_to(file, text, append=False):
    filepath = file[::-1].split(chr(47), 1)[1][::-1]
    file_name = file[::-1].split(chr(47), 1)[0][::-1]
    os.chdir(filepath.strip())
    open(file_name, 'a' if append else 'w').write(str(text))
    return None


def execute_pipeline(commands):
    n = len(commands)
    pipes = []
    for _ in range(n - 1):
        pipes.append(os.pipe())

    builtins = {
        'exit', 'echo', 'type', 'pwd', 'cd', 'history'
    }

    pids = []
    for i, cmd in enumerate(commands):
        args = parser(cmd, as_list=True)
        is_builtin = args[0] in builtins

        if is_builtin and n == 1:
            return  # Built-in single command already handled in main()

        pid = os.fork()
        if pid == 0:
            if i > 0:
                os.dup2(pipes[i - 1][0], 0)
            if i < n - 1:
                os.dup2(pipes[i][1], 1)
            for r, w in pipes:
                os.close(r)
                os.close(w)

            if is_builtin:
                if args[0] == 'echo':
                    print(' '.join(args[1:]))
                elif args[0] == 'pwd':
                    print(os.getcwd())
                elif args[0] == 'type':
                    target = args[1] if len(args) > 1 else ''
                    if target in builtins:
                        print(f'{target} is a shell builtin')
                    elif PATH := shutil.which(target):
                        print(f'{target} is {PATH}')
                    else:
                        print(f'{target}: not found')
                os._exit(0)
            else:
                os.execvp(args[0], args)
                os._exit(1)
        else:
            pids.append(pid)

    for r, w in pipes:
        os.close(r)
        os.close(w)
    for pid in pids:
        os.waitpid(pid, 0)


class Autocomplete:
    def __init__(self, commands):
        self.commands = commands
        self.last_text = None
        self.tab_count = 0
        self.suggestions = []
        self.last_prefix = None

    def readline_complete(self, text, state):
        if text != self.last_text:
            self.tab_count = 0
            self.last_text = text
            self.last_prefix = text
            self.suggestions = sorted([cmd for cmd in self.commands if cmd.startswith(text)])

        # No matches
        if not self.suggestions:
            return None

        # Only one candidate: complete it
        if len(self.suggestions) == 1:
            if state == 0:
                return self.suggestions[0] + ' '
            return None

        # Multiple matches
        prefix = os.path.commonprefix(self.suggestions)
        # If the prefix is longer than what the user typed, complete up to the prefix
        if len(prefix) > len(text):
            if state == 0:
                return prefix
            return None

        # Handle multiple matches for TAB presses
        if state == 0:
            self.tab_count += 1
            if self.tab_count == 1:
                # First TAB: ring bell
                sys.stdout.write('\a')
                sys.stdout.flush()
                return None
            elif self.tab_count == 2:
                # Second TAB: print matches on new line, then prompt
                sys.stdout.write('\n' + '  '.join(self.suggestions) + '\n')
                sys.stdout.write(f'$ {text}')
                sys.stdout.flush()
                return None
        return None


def main():
    history_list = []
    history_file = os.getenv('HISTFILE')
    history_pointer = 0
    flag_history_from_file = False

    if history_file and os.path.exists(history_file):
        with open(history_file, 'r') as h:
            history_list.extend([line.rstrip() for line in h if line.rstrip()])
        history_pointer = len(history_list)

    command_list = ['exit', 'echo', 'type', 'pwd', 'cd', 'history']
    completer = Autocomplete(command_list)
    completer.commands = copy(command_list)

    # Dynamically add executables from PATH (especially /tmp/...)
    dynamic_path = [f for f in subprocess.run('echo $PATH', shell=True, capture_output=True).stdout.decode().split(':')
                    if f[:4] == '/tmp']
    for folder in dynamic_path:
        folder_list = subprocess.run(f'ls -1 {folder}', shell=True, capture_output=True).stdout.decode()
        for name in folder_list.strip().split('\n'):
            if name and name not in completer.commands:
                completer.commands.append(name)

    readline.clear_history()
    readline.set_completer(completer.readline_complete)
    readline.parse_and_bind('tab: complete')
    readline.set_completer_delims(' \t\n')

    while True:
        output_file = None
        append = None
        err_flag = None

        command = input('$ ')
        command_foo = copy(command)
        command_full = parser(command).split(' ', 1)
        identifier = command_full[0]
        history_list.append(command_foo)

        command, output_file, append, err_flag = check_for_file_to_write(command)

        if '|' in command:
            execute_pipeline([c.strip() for c in command.split('|')])
            continue

        if '2>>' in command_foo:
            parts = command_foo.split('2>>')
            cmd_part = parts[0].strip()

        if '1>>' in command_foo or ('>>' in command_foo and '1>>' not in command_foo and '2>>' not in command_foo):
            if '1>>' in command_foo:
                parts = command_foo.split('1>>')
            else:
                parts = command_foo.split('>>')
            cmd_part = parts[0].strip()
            file_part = parts[1].strip()
            with open(file_part, 'a') as f:  # Open the file in append mode
                subprocess.run(cmd_part, shell=True, stdout=f)  # Append output to the file
            continue

        match identifier:
            case 'exit':
                if history_file:
                    with open(history_file, 'a') as h:
                        for line in history_list[history_pointer:]:
                            h.write(f'{line}\n')
                exit(int(command_full[1]) if len(command_full) > 1 else 0)

            case 'echo':
                # Remove any redirection from the output for echo
                echo_arg = command_full[1]
                for redir in ['2>>', '2>', '1>>', '1>', '>>', '>']:
                    if redir in echo_arg:
                        echo_arg = echo_arg.split(redir, 1)[0].rstrip()
                if output_file:
                    if err_flag:
                        try:
                            open(output_file, 'r')
                        except FileNotFoundError:
                            write_to(output_file, '', append=append)
                        finally:
                            write_to(output_file, '', append=append)
                            print(command_full[1])
                    else:
                        write_to(output_file, command_full[1] + '\n', append=append)
                else:
                    print(command_full[1])

            case 'type':
                if command_full[1].strip() in command_list:
                    print(f'{command_full[1]} is a shell builtin')
                elif PATH := shutil.which(command_full[1] if len(command_full) > 1 else ''):
                    print(f'{command_full[1]} is {PATH}')
                else:
                    print(f'{command_full[1]}: not found')

            case 'pwd':
                print(os.getcwd())

            case 'cd':
                try:
                    os.chdir(Path.home() if command_full[1] == '~' else command_full[1])
                except:
                    print(f'cd: {command_full[1]}: No such file or directory')

            case 'history':
                if len(command_full) == 2:
                    if command_full[1].startswith('-a'):
                        file = command_full[1][3:] if len(command_full[1]) > 2 else history_file
                        if file:
                            with open(file, 'a') as h:
                                for line in history_list[history_pointer:]:
                                    h.write(f'{line}\n')
                            history_pointer = len(history_list)
                        continue
                    elif command_full[1].startswith('-w'):
                        file = command_full[1][3:]
                        if file:
                            with open(file, 'w') as h:
                                for line in history_list:
                                    h.write(f'{line}\n')
                            with open(file, 'a') as h:
                                pass
                        continue
                    elif command_full[1].startswith('-r'):
                        file = command_full[1][3:]
                        if file and os.path.exists(file):
                            with open(file, 'r') as h:
                                history_list.extend([line.rstrip() for line in h if line.rstrip()])
                        continue

                curr_history_path = history_list
                if len(command_full) == 2 and command_full[1].isdigit():
                    limit = int(command_full[1])
                    curr_history_path = history_list[-limit:]
                    offset = len(history_list) - len(curr_history_path)
                else:
                    offset = 0
                for x, line in enumerate(curr_history_path):
                    print(f' {x + 1 + offset} {line}')

            case _:  # default
                if shutil.which(identifier if identifier else ''):
                    subprocess.run(command_foo, shell=True)
                else:
                    print(f'{command}: command not found')


if __name__ == '__main__':
    main()
