import sys


def main():
    # Uncomment this block to pass the first stage
    sys.stdout.write("$ ")
    # Wait for user input
    command = input()
    print(f"{command}: command not found")
    main()


if __name__ == "__main__":
    main()
