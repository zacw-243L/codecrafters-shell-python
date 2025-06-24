import sys
import os
import shutil
import subprocess
from pathlib import Path
from copy import copy
import readline
import io


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

    if as_list:
        return result
    else:
        return ' '.join(result)


def check_for_file_to_write(command):
    write_list = ['>', '1>', '2>', '>>', '1>>', '2>>']

    append = bool(command.count('>') - 1)

    for x, symbol in enumerate(command):
        if symbol == '>' and x:
            if command[x - 1] == '2':
                err_flag = True
                break
            else:
                err_flag = False

    if any([x for x in command if x in write_list]):
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


class Autocomplete:
    def __init__(self, commands):
        self.commands = commands

    def complete(self, text, symbol_iter):
        results = [x for x in self.commands if x.startswith(text)] + [None]
        self.results = results
        return results[symbol_iter]


def main():
    history_list = []
    history_pointer = None

    command_list = ['exit', 'echo', 'type', 'pwd', 'cd', 'history']
    string_agg = ''

    completer = Autocomplete(command_list)
    completer.commands = copy(command_list)
    dynamic_path = [folder for folder in
                    subprocess.run('echo $PATH', shell=True, capture_output=True).stdout.decode().split(':') if
                    folder[:4] == '/tmp']
    dynamic_commands = []
    for folder in dynamic_path:
        folder_list = subprocess.run(f'ls -1 {folder}', shell=True, capture_output=True).stdout.decode()
        dynamic_commands.append(''.join(folder_list).strip())
    dynamic_commands = sorted(dynamic_commands)
    completer.commands.extend(dynamic_commands)

    readline.clear_history()
    readline.set_completer(completer.complete)
    readline.parse_and_bind('tab: complete')  # history-preserve-point on')
    readline.set_completer_delims('\t')
    # readline.set_auto_history(False)

    # print('$ ', end = '')
    while True:

        output_file = None
        append = None
        err_flag = None

        command = input('$ ')

        command_foo = copy(command)
        history_list.append(command_foo)

        command, output_file, append, err_flag = check_for_file_to_write(command)

        command_full = parser(command).split(' ', 1)
        identifier = command_full[0]

        if command[0] in ("'", '"'):
            command_full = parser(command, as_list=True)
            command_full[0] = 'cat '
            command = ''.join(command_full)
            identifier = 'cat'

        match identifier:

            case 'exit':
                exit(int(command_full[1]))

            case 'echo':
                if output_file:
                    if err_flag:
                        try:
                            open(output_file, 'r')
                        except FileNotFoundError:
                            write_to(output_file, '', append=append)
                            # print(command_full[1])
                        finally:
                            write_to(output_file, '', append=append)
                            print(command_full[1])
                    else:
                        write_to(output_file, command_full[1] + '\n', append=append)
                else:
                    print(command_full[1])

            case 'type':
                if command_full[1].strip() in command_list:
                    # if command_full[1].strip() in command_list[:-1]:
                    print(f'{command_full[1]} is a shell builtin')
                elif PATH := shutil.which(command_full[1] if command_full[1] else ''):
                    print(f'{command_full[1]} is {PATH}')
                else:
                    print(f'{command_full[1]}: not found')

            case 'pwd':
                print(os.getcwd())

            case 'cd':
                if command_full[1] == '~':
                    os.chdir(Path.home())
                else:
                    try:
                        os.chdir(command_full[1])
                    except FileNotFoundError:
                        print(f'cd: {command_full[1]}: No such file or directory')

            case 'history':
                if len(command_full) == 1:
                    for x, line in enumerate(history_list):
                        print(f' {x + 1} {line}')
                else:
                    command_number = int(command_full[1])
                    cut = len(history_list) - command_number
                    for y, line in enumerate(history_list[cut:]):
                        print(f' {y + 2 + command_number} {line}')

            case default:
                if identifier := shutil.which(identifier if identifier else ''):
                    subprocess.run(command_foo, shell=True)
                else:
                    print(f'{command}: command not found')

        # print('$ ', end = '')


if __name__ == '__main__':
    main()