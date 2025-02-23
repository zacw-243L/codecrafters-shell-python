import sys
import os
import subprocess


def split_input(inp):
    i = 0
    inpList = []
    toFile = ""
    errFile = ""
    curWord = ""
    while i < len(inp):
        if inp[i] == "\\":
            curWord += inp[i + 1]
            i += 1
        elif inp[i] == " ":
            if ">" in curWord:
                parts = inp[i + 1:].split()
                if curWord == "2>":
                    errFile = parts[0]
                else:
                    toFile = parts[0]
                return inpList, toFile, errFile
            if curWord:
                inpList.append(curWord)
            curWord = ""
        elif inp[i] == "'":
            i += 1
            while inp[i] != "'":
                curWord += inp[i]
                i += 1
        elif inp[i] == '"':
            i += 1
            while inp[i] != '"':
                if inp[i] == "\\" and inp[i + 1] in ["\\", "$", '"']:
                    curWord += inp[i + 1]
                    i += 2
                else:
                    curWord += inp[i]
                    i += 1
        else:
            curWord += inp[i]
        i += 1
    inpList.append(curWord)
    return inpList, toFile, errFile


def main():
    exited = False
    path_list = os.environ["PATH"].split(":")
    builtin_list = ["exit", "echo", "type", "pwd", "cd"]
    while not exited:
        sys.stdout.write("$ ")
        userinp = input()
        inpList, toFile, errFile = split_input(userinp)
        output = ""
        error = ""
        match inpList[0]:
            case "cd":
                path = inpList[1]
                if path == "~":
                    os.chdir(os.environ["HOME"])
                elif os.path.isdir(path):
                    os.chdir(path)
                else:
                    error = path + ": No such file or directory"
            case "pwd":
                output = os.getcwd()
            case "type":
                for path in path_list:
                    if os.path.isfile(f"{path}/{inpList[1]}"):
                        output = inpList[1] + " is " + f"{path}/{inpList[1]}"
                        break
                if inpList[1] in builtin_list:
                    output = inpList[1] + " is a shell builtin"
                if not output:
                    error = inpList[1] + ": not found"
            case "echo":
                output = " ".join(inpList[1:])
            case "exit":
                exited = True
            case _:
                isCmd = False
                for path in path_list:
                    p = f"{path}/{inpList[0]}"
                    if os.path.isfile(p) and os.access(p, os.X_OK):
                        result = subprocess.run(
                            [inpList[0]] + inpList[1:],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True,
                            cwd=path
                        )
                        output = result.stdout.rstrip()
                        error = result.stderr.rstrip()
                        isCmd = True
                        break
                if not isCmd:
                    error = userinp + ": command not found"
        if not toFile:
            if output:
                print(output, file=sys.stdout)
        else:
            with open(toFile, "a") as f:
                print(output, end="", file=f)
        if errFile:
            with open(errFile, "a") as f:
                print(error, end="", file=f)
        elif error:
            print(error, file=sys.stderr)


if __name__ == "__main__":
    main()
