import random

def generate_word():
    with open("./large") as f:
        contents = f.read()
    lines = contents.splitlines()
    line_number = random.randrange(0, len(lines))
    return lines[line_number]

def main():
    target = generate_word()
    print(target)

    while "'" in target:
        target = generate_word()

    print(target)

main()
