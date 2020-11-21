import matplotlib.pylab as plt
import random
import numpy as np

sbox = [
    # 0    1    2    3    4    5    6    7    8    9    a    b    c    d    e    f
    0x63, 0x7c, 0x77, 0x7b, 0xf2, 0x6b, 0x6f, 0xc5, 0x30, 0x01, 0x67, 0x2b, 0xfe, 0xd7, 0xab, 0x76,  # 0
    0xca, 0x82, 0xc9, 0x7d, 0xfa, 0x59, 0x47, 0xf0, 0xad, 0xd4, 0xa2, 0xaf, 0x9c, 0xa4, 0x72, 0xc0,  # 1
    0xb7, 0xfd, 0x93, 0x26, 0x36, 0x3f, 0xf7, 0xcc, 0x34, 0xa5, 0xe5, 0xf1, 0x71, 0xd8, 0x31, 0x15,  # 2
    0x04, 0xc7, 0x23, 0xc3, 0x18, 0x96, 0x05, 0x9a, 0x07, 0x12, 0x80, 0xe2, 0xeb, 0x27, 0xb2, 0x75,  # 3
    0x09, 0x83, 0x2c, 0x1a, 0x1b, 0x6e, 0x5a, 0xa0, 0x52, 0x3b, 0xd6, 0xb3, 0x29, 0xe3, 0x2f, 0x84,  # 4
    0x53, 0xd1, 0x00, 0xed, 0x20, 0xfc, 0xb1, 0x5b, 0x6a, 0xcb, 0xbe, 0x39, 0x4a, 0x4c, 0x58, 0xcf,  # 5
    0xd0, 0xef, 0xaa, 0xfb, 0x43, 0x4d, 0x33, 0x85, 0x45, 0xf9, 0x02, 0x7f, 0x50, 0x3c, 0x9f, 0xa8,  # 6
    0x51, 0xa3, 0x40, 0x8f, 0x92, 0x9d, 0x38, 0xf5, 0xbc, 0xb6, 0xda, 0x21, 0x10, 0xff, 0xf3, 0xd2,  # 7
    0xcd, 0x0c, 0x13, 0xec, 0x5f, 0x97, 0x44, 0x17, 0xc4, 0xa7, 0x7e, 0x3d, 0x64, 0x5d, 0x19, 0x73,  # 8
    0x60, 0x81, 0x4f, 0xdc, 0x22, 0x2a, 0x90, 0x88, 0x46, 0xee, 0xb8, 0x14, 0xde, 0x5e, 0x0b, 0xdb,  # 9
    0xe0, 0x32, 0x3a, 0x0a, 0x49, 0x06, 0x24, 0x5c, 0xc2, 0xd3, 0xac, 0x62, 0x91, 0x95, 0xe4, 0x79,  # a
    0xe7, 0xc8, 0x37, 0x6d, 0x8d, 0xd5, 0x4e, 0xa9, 0x6c, 0x56, 0xf4, 0xea, 0x65, 0x7a, 0xae, 0x08,  # b
    0xba, 0x78, 0x25, 0x2e, 0x1c, 0xa6, 0xb4, 0xc6, 0xe8, 0xdd, 0x74, 0x1f, 0x4b, 0xbd, 0x8b, 0x8a,  # c
    0x70, 0x3e, 0xb5, 0x66, 0x48, 0x03, 0xf6, 0x0e, 0x61, 0x35, 0x57, 0xb9, 0x86, 0xc1, 0x1d, 0x9e,  # d
    0xe1, 0xf8, 0x98, 0x11, 0x69, 0xd9, 0x8e, 0x94, 0x9b, 0x1e, 0x87, 0xe9, 0xce, 0x55, 0x28, 0xdf,  # e
    0x8c, 0xa1, 0x89, 0x0d, 0xbf, 0xe6, 0x42, 0x68, 0x41, 0x99, 0x2d, 0x0f, 0xb0, 0x54, 0xbb, 0x16  # f
]


def aes_internal(inputdata, key):
    return sbox[inputdata ^ key]

#Simple test vectors - if you get the check-mark printed all OK.
assert(aes_internal(0xAB, 0xEF) == 0x1B)
assert(aes_internal(0x22, 0x01) == 0x26)
print("✔️ OK to continue!")

def aes_secret(inputdata):
    secret_key = 0xEF
    return aes_internal(secret_key, inputdata)


#************************AES Watcher************************
random.randint(0, 255)

# List comprehension can be used to shovel data through a function
def somefunc(a):
    return a + 4

input_data = [1, 2, 5, 6]
output_data = [somefunc(a) for a in input_data]

# You can use this while ignoring the index variable too
output_data = [somefunc(random.randint(0, 255)) for _ in range(0, 1000)]
input_data = [random.randint(0, 255) for _ in range(0, 1000)]

#Simple test vectors - if you get the check-mark printed all OK.
assert(len(input_data) == 1000)
# Possibly not true for random variables (re-run if you get an error)
assert(max(input_data) == 0xFF)
# Possibly not true for random variables (re-run if you get an error)
assert(min(input_data) == 0x00)
print("✔️ OK to continue!")

leaked_data = [(aes_secret(a) & 0x01) for a in input_data]
print(leaked_data)

plt.figure(1)
plt.plot(leaked_data[0:200])
plt.show()
#************************End AES Watcher************************


#*************************AES Guesser*************************
def num_same(a, b):

    if len(a) != len(b):
        raise ValueError("Arrays must be same length!")

    if max(a) != max(b):
        raise ValueError("Arrays max() should be the same!")

    #Count how many list items match up
    same = 0
    for i, _ in enumerate(a):
        if a[i] == b[i]:
            same += 1

    return same

#Simple test vectors - if you get the check-mark printed all OK.
assert(num_same([0, 1, 0, 1, 1, 1, 1, 0], [0, 1, 0, 1, 1, 1, 1, 0]) == 8)
assert(num_same([1, 1, 1, 0, 0, 0, 0, 0], [0, 1, 0, 1, 1, 1, 1, 0]) == 2)
assert(num_same([1, 0], [0, 1]) == 0)
print("✔️ OK to continue!")

#Guessing loop
for guess in range(0, 256):

    #Get a hypothetical leakage list - use aes_internal(guess, input_byte) and mask off to only get value of lowest bit
    hypothetical_leakage = [aes_internal(
        guess, input_byte) & 0x01 for input_byte in input_data]

    #Use our function
    same_count = num_same(hypothetical_leakage, leaked_data)

    #Print for debug
    print("Guess {:02X}: {:4d} bits same".format(guess, same_count))
guess_list = [0] * 256

#Guessing loop with sort
for guess in range(0, 256):

    #Get a hypothetical leakage list - use aes_internal(guess, input_byte) and mask off to only get value of lowest bit
    hypothetical_leakage = [aes_internal(
        guess, input_byte) & 0x01 for input_byte in input_data]

    #Use our function
    same_count = num_same(hypothetical_leakage, leaked_data)

    #Track the number of correct bits
    guess_list[guess] = same_count

#Use np.argsort to generate a list of indicies from low to high, then [::-1] to reverse the list to get high to low.
sorted_list = np.argsort(guess_list)[::-1]

#Print top 5 only
for guess in sorted_list[0:5]:
        print("Key Guess {:02X} = {:04d} matches".format(
            guess, guess_list[guess]))

def get_bit(data, bit):
    if data & (1 << bit):
        return 1
    else:
        return 0

assert(get_bit(0xAA, 7) == 1)
assert(get_bit(0xAA, 0) == 0)
assert(get_bit(0x00, 7) == 0)
print("✔️ OK to continue!")

def aes_leakage_guess(keyguess, inputdata, bit):
    return get_bit(aes_internal(keyguess, inputdata), bit)

assert(aes_leakage_guess(0xAB, 0x22, 4) == 0)
assert(aes_leakage_guess(0xAB, 0x22, 3) == 0)
assert(aes_leakage_guess(0xAB, 0x22, 2) == 1)
assert(aes_leakage_guess(0xAB, 0x22, 1) == 1)
assert(aes_leakage_guess(0xAB, 0x22, 0) == 1)
print("✔️ OK to continue!")

#Bitwise guessing loop
for bit_guess in range(0, 8):
    guess_list = [0] * 256
    print("Checking bit {:d}".format(bit_guess))
    for guess in range(0, 256):

        #Get a hypothetical leakage for guessed bit (ensure returns 1/0 only)
        #Use bit_guess as the bit number, guess as the key guess, and data from input_data
        hypothetical_leakage = [aes_leakage_guess(
            guess, input_byte, bit_guess) for input_byte in input_data]

        #Use our function
        same_count = num_same(hypothetical_leakage, leaked_data)

        #Track the number of correct bits
        guess_list[guess] = same_count

    sorted_list = np.argsort(guess_list)[::-1]

    #Print top 5 only
    for guess in sorted_list[0:5]:
            print("Key Guess {:02X} = {:04d} matches".format(
                guess, guess_list[guess]))
