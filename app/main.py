#!/usr/bin/env python3
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
            string_builder += char
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

        if char == '\\':
            if x + 1 < len(string):
                if is_single_quoted:
                    string_builder += char
                elif is_double_quoted:
                    if string[x + 1] in ('\\', '$', '"'):
                        string_builder += string[x + 1]
                        is_escaped = True
                    else:
                        string_builder += char
                else:
                    string_builder += string[x + 1]
                    is_escaped = True
            continue

        if not any([is_single_quoted, is_double_quoted]):
            if char == '|' and not as_list:
                result.append(string_builder.strip())
                string_builder = str()
                continue
            if char == ' ' and as_list:
                result.append(string_builder)
                string_builder = str()
            else:
                string_builder += char
        else:
            string_builder += char

    if string_builder.strip():
        result.append(string_builder.strip())

    while '' in result:
        result.remove('')

    return result if as_list else ' '.join(result)


def check_for_file_to_write(command):
    write_list = ['>', '1>', '2>', '>>', '1>>', '2>>']
    append = False
    err_flag = False

    if isinstance(command, str):
        command = parser(command, as_list=True)

    for x, symbol in enumerate(command):
        if symbol in write_list:
            append = symbol in ['>>', '1>>', '2>>']
            err_flag = symbol in ['2>', '2>>']
            output_file = command[x + 1].strip()
            command = command[:x]
            return (command, output_file, append, err_flag)

    return (command, None, False, False)


def write_to(file, text, append=False):
    filepath = file[::-1].split('/', 1)[1][::-1] if '/' in file else '.'
    file_name = file[::-1].split('/', 1)[0][::-1]

    os.makedirs(filepath, exist_ok=True)
    with open(os.path.join(filepath, file_name), 'a' if append else 'w') as f:
        f.write(str(text))


def check_fork(com):
    return '|' in com


class Autocomplete:
    def __init__(self, commands):
        self.commands = commands

    def complete(self, text, symbol_iter):
        results = [x for x in self.commands if x.startswith(text)] + [None]
        self.results = results
        if len(results) > 2:
            return results[symbol_iter]
        else:
            return results[symbol_iter] + ' ' if results[symbol_iter] else None


def run_pipeline(commands, output_file=None, append=False, err_flag=False):
    processes = []
    prev_pipe_read = None

    for i, cmd in enumerate(commands):
        cmd_args = parser(cmd, as_list=True)
        stdout = subprocess.PIPE if i < len(commands) - 1 else (open(output_file, 'a' if append else 'w') if output_file and not err_flag else sys.stdout)
        stderr = open(output_file, 'a' if append else 'w') if output_file and err_flag else sys.stderr
        stdin = prev_pipe_read if prev_pipe_read else None

        try:
            proc = subprocess.Popen(cmd_args, stdin=stdin, stdout=stdout, stderr=stderr, text=True)
            processes.append(proc)
        except FileNotFoundError:
            print(f"{cmd_args[0]}: command not found", file=sys.stderr)
            return

        if prev_pipe_read:
            prev_pipe_read.close()
        prev_pipe_read = proc.stdout if i < len(commands) - 1 else None

    for proc in processes:
        proc.wait()

    if output_file and not err_flag and stdout != sys.stdout:
        stdout.close()
    if output_file and err_flag and stderr != sys.stderr:
        stderr.close()


def main():
    if os.getenv('HISTFILE'):
        history_list = [line.rstrip() for line in open(os.getenv('HISTFILE'), 'r').readlines()]
        for line in history_list:
            readline.add_history(line)
    else:
        history_list = []
    history_file = None
    history_pointer = 0
    flag_history_from_file = False

    command_list = ['exit', 'echo', 'type', 'pwd', 'cd', 'history']
    completer = Autocomplete(command_list)
    completer.commands = copy(command_list)
    dynamic_path = [folder for folder in
                    subprocess.run('echo $PATH', shell=True, capture_output=True).stdout.decode().split(':') if
                    folder[:4] == '/tmp']
    dynamic_commands = []
    for folder in dynamic_path:
        folder_list = subprocess.run(f'ls -1 {folder}', shell=True, capture_output=True).stdout.decode().splitlines()
        dynamic_commands.extend(folder_list)
    completer.commands.extend(sorted(dynamic_commands))
    readline.clear_history()
    readline.set_completer(completer.complete)
    readline.parse_and_bind('tab: complete')
    readline.parse_and_bind('up: previous-history')
    readline.parse_and_bind('down: next-history')
    readline.set_completer_delims('\t')

    while True:
        try:
            sys.stdout.write('$ ')
            sys.stdout.flush()
            command = input()
            if not command.strip():
                continue

            readline.add_history(command)
            history_list.append(command)

            if check_fork(command):
                commands = parser(command, as_list=True)
                command, output_file, append, err_flag = check_for_file_to_write(commands[-1])
                commands[-1] = ' '.join(command)
                run_pipeline(commands, output_file, append, err_flag)
                continue

            command, output_file, append, err_flag = check_for_file_to_write(command)
            command_full = parser(command, as_list=True)
            identifier = command_full[0] if command_full else ''

            if command and command[0] in ("'", '"'):
                command_full = parser(command, as_list=True)
                command_full[0] = 'cat '
                command = ' '.join(command_full)
                identifier = 'cat'

            match identifier:
                case 'exit':
                    if os.getenv('HISTFILE'):
                        with open(os.getenv('HISTFILE'), 'w') as h:
                            for line in history_list:
                                h.write(f'{line}\n')
                    exit(int(command_full[1]) if len(command_full) > 1 else 0)

                case 'echo':
                    output = ' '.join(command_full[1:]) if len(command_full) > 1 else ''
                    if output_file:
                        if err_flag:
                            print(output, file=sys.stderr)
                            write_to(output_file, output + '\n', append=append)
                        else:
                            write_to(output_file, output + '\n', append=append)
                    else:
                        print(output)

                case 'type':
                    query = command_full[1].strip() if len(command_full) > 1 else ''
                    if query in command_list:
                        print(f'{query} is a shell builtin')
                    elif PATH := shutil.which(query):
                        print(f'{query} is {PATH}')
                    else:
                        print(f'{query}: not found')

                case 'pwd':
                    print(os.getcwd())

                case 'cd':
                    path = command_full[1] if len(command_full) > 1 else Path.home()
                    if path == '~':
                        path = Path.home()
                    try:
                        os.chdir(path)
                    except FileNotFoundError:
                        print(f'cd: {path}: No such file or directory')

                case 'history':
                    if history_file is not None:
                        with open(history_file, 'r') as hist_temp:
                            curr_history_path = [l.rstrip() for l in hist_temp]
                    else:
                        curr_history_path = history_list

                    if len(command_full) == 1:
                        if flag_history_from_file:
                            print(f' {1} history -r {history_file}')
                        for x, line in enumerate(curr_history_path):
                            print(f' {x + 1 + int(flag_history_from_file)} {line}')
                        if flag_history_from_file:
                            print(f' {x + 2} history')
                    else:
                        if command_full[1].startswith('-'):
                            option = command_full[1][1]
                            history_file = command_full[1][3:] if len(command_full[1]) > 3 else ''
                            if option == 'r':
                                flag_history_from_file = True
                                if os.path.exists(history_file):
                                    with open(history_file, 'r') as h:
                                        history_list.extend([l.rstrip() for l in h])
                                        for line in history_list:
                                            readline.add_history(line)
                            elif option == 'w':
                                with open(history_file, 'w') as h:
                                    for line in history_list:
                                        h.write(f'{line}\n')
                            elif option == 'a':
                                with open(history_file, 'a') as h:
                                    for x, line in enumerate(history_list[history_pointer:]):
                                        h.write(f'{line}\n')
                                history_pointer = len(history_list)
                        else:
                            command_number = int(command_full[1])
                            cut = max(0, len(history_list) - command_number)
                            for y, line in enumerate(history_list[cut:]):
                                print(f' {y + cut + 1} {line}')

                case _:
                    if identifier and (identifier := shutil.which(identifier)):
                        proc = subprocess.run([identifier] + command_full[1:], shell=False, text=True,
                                             stdout=open(output_file, 'a' if append else 'w') if output_file and not err_flag else sys.stdout,
                                             stderr=open(output_file, 'a' if append else 'w') if output_file and err_flag else sys.stderr)
                        if proc.returncode != 0:
                            print(f"{identifier}: command failed", file=sys.stderr)
                    else:
                        print(f"{command}: command not found")

        except KeyboardInterrupt:
            print('^C')
            continue
        except EOFError:
            break


if __name__ == '__main__':
    main()