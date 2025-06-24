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
    append = bool(command.count('>') - 1)
    err_flag = False

    for x, symbol in enumerate(command):
        if symbol == '>' and x:
            if command[x - 1] == '2':
                err_flag = True
                break

    if any(x in command for x in write_list):
        io_splitter = command.replace('1>', '>').replace('2>', '>').replace('>>', '>').split('>')
        write_command = io_splitter[0]
        output_file = io_splitter[1]
    else:
        return (command, None, False, False)

    return (write_command, output_file.strip(), append, err_flag)

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

    pids = []
    for i, cmd in enumerate(commands):
        pid = os.fork()
        if pid == 0:
            if i > 0:
                os.dup2(pipes[i - 1][0], 0)
            if i < n - 1:
                os.dup2(pipes[i][1], 1)
            for r, w in pipes:
                os.close(r)
                os.close(w)
            os.execvp(parser(cmd, as_list=True)[0], parser(cmd, as_list=True))
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

    def complete(self, text, symbol_iter):
        results = [x for x in self.commands if x.startswith(text)] + [None]
        self.results = results
        return results[symbol_iter] + ' ' if len(results) <= 2 else results[symbol_iter]

def main():
    history_list = []
    history_file = None
    history_pointer = 0
    flag_history_from_file = False

    command_list = ['exit', 'echo', 'type', 'pwd', 'cd', 'history']
    completer = Autocomplete(command_list)
    completer.commands = copy(command_list)

    dynamic_path = [f for f in subprocess.run('echo $PATH', shell=True, capture_output=True).stdout.decode().split(':') if f[:4] == '/tmp']
    for folder in dynamic_path:
        folder_list = subprocess.run(f'ls -1 {folder}', shell=True, capture_output=True).stdout.decode()
        completer.commands.extend(folder_list.strip().split('\n'))

    readline.clear_history()
    readline.set_completer(completer.complete)
    readline.parse_and_bind('tab: complete')
    readline.set_completer_delims('\t')

    while True:
        output_file = None
        append = None
        err_flag = None

        command = input('$ ')
        command_foo = copy(command)
        history_list.append(command_foo)
        command, output_file, append, err_flag = check_for_file_to_write(command)

        if '|' in command:
            execute_pipeline([c.strip() for c in command.split('|')])
            continue

        command_full = parser(command).split(' ', 1)
        identifier = command_full[0]

        match identifier:
            case 'exit':
                if os.getenv('HISTFILE'):
                    with open(os.getenv('HISTFILE'), 'w') as h:
                        for line in history_list:
                            h.write(f'{line}\n')
                exit(int(command_full[1]) if len(command_full) > 1 else 0)

            case 'echo':
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
                if history_file:
                    with open(history_file, 'r') as hist_temp:
                        curr_history_path = [l.rstrip() for l in hist_temp]
                else:
                    curr_history_path = history_list

                if len(command_full) == 1:
                    if flag_history_from_file:
                        print(f' 1 history -r {history_file}')
                    for x, line in enumerate(curr_history_path):
                        print(f' {x + 1 + int(flag_history_from_file)} {line}')
                    if flag_history_from_file:
                        print(f' {x + 2} history')
                else:
                    if command_full[1][0] == '-':
                        match command_full[1][1]:
                            case 'r':
                                history_file = command_full[1][3:]
                                flag_history_from_file = True
                            case 'w':
                                history_file = command_full[1][3:]
                                with open(history_file, 'w') as h:
                                    for line in history_list:
                                        h.write(f'{line}\n')
                            case 'a':
                                history_file = command_full[1][3:]
                                with open(history_file, 'a') as h:
                                    for x, line in enumerate(history_list):
                                        if x >= history_pointer:
                                            h.write(f'{line}\n')
                                history_pointer = x + 1
                    else:
                        command_number = int(command_full[1])
                        cut = len(history_list) - command_number
                        for y, line in enumerate(history_list[cut:]):
                            print(f' {y + 2 + command_number} {line}')

            case _:  # default
                if shutil.which(identifier if identifier else ''):
                    subprocess.run(command_foo, shell=True)
                else:
                    print(f'{command}: command not found')

if __name__ == '__main__':
    main()
