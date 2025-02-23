import sys
import os
import subprocess


def split_input(inp):
    i = 0
    inpList = []
    toFile = ""
    curWord = ""
    while i < len(inp):
        if inp[i] == "\\":
            curWord += inp[i + 1]
            i += 1
        elif inp[i] == " ":
            if ">" in curWord:
                toFile = inp[i + 1:]
                return inpList, toFile
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
    return inpList, toFile


def main():
    exited = False
    path_list = os.environ["PATH"].split(":")
    builtin_list = ["exit", "echo", "type", "pwd", "cd"]
    while not exited:
        sys.stdout.write("$ ")
        userinp = input()
        inpList, toFile = split_input(userinp)
        output = ""
        match inpList[0]:
            case "cd":
                path = inpList[1]
                if path == "~":
                    os.chdir(os.environ["HOME"])
                elif os.path.isdir(path):
                    os.chdir(path)
                else:
                    output = path + ": No such file or directory"
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
                    output = inpList[1] + ": not found"
            case "echo":
                output = " ".join(inpList[1:])
            case "exit":
                exited = True
            case _:
                isCmd = False
                for path in path_list:
                    p = f"{path}/{inpList[0]}"
                    if os.path.isfile(p):
                        # Run the command and capture the output
                        result = subprocess.run(
                            [p] + inpList[1:], stdout=subprocess.PIPE, text=True
                        )
                        # Format the output as expected
                        output = f"Program was passed {len(inpList)} args (including program name).\n"
                        output += f"Arg #0 (program name): {os.path.basename(p)}\n"  # Use basename to get just the name
                        for idx, arg in enumerate(inpList[1:], start=1):
                            output += f"Arg #{idx}: {arg}\n"
                        output += f"Program Signature: {result.returncode}\n"  # Assuming you want to show the return code
                        isCmd = True
                        break
                if not isCmd:
                    output = userinp + ": command not found"

        # Handle output redirection
        if toFile:
            with open(toFile, "w") as f:
                if output:
                    f.write(output)
        else:
            if output:
                print(output, file=sys.stdout)


if __name__ == "__main__":
    main()
    