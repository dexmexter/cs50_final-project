import getpass
import string

def stick_art(n):

guess_pool = list(string.ascii_lowercase)

target = getpass.getpass("What is the target word?\n")
target_list = list(target)
letters_remaining = []

for i in target:
    if i not in letters_remaining:
        letters_remaining.append(i)

check_word = "*" * len(target)
check_list = list(check_word)

print("Welcome to Hangman, good luck guessing the word!\n")

strikes = 0
while strikes < 6:
    print(strike_art[strikes])
    print("".join(check_list) + "\n")
    user_guess = input(print("\nYour guess:"))

    if user_guess not in guess_pool:
        core.print_slow("That guess is either not valid or has already been used, please guess again.\n")

    elif user_guess not in letters_remaining:
        strikes += 1
        print("You have %s incorrect guesses remaining.\n" %(str(6 - strikes)))

    elif user_guess in letters_remaining:
        guess_pool.remove(user_guess)
        letters_remaining.remove(user_guess)

        store_index = [i for i, x in enumerate(target_list) if x == user_guess]
        for i in store_index:
            check_list[i] = user_guess

    if len(letters_remaining) == 0:
        print("".join(check_list) + "\n")
        return print("You've won!\n")

print(strike_art[strikes])
return print("Sorry you ran out of tries! The word you were trying to guess was: \n%s\n" %(target))
