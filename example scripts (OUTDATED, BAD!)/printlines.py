# you can ignore this file, it's just so I don't have to write the word `print` over and over again
# in the example scripts.

def printlines(lines, every=1):
    out = []
    c = 0
    for l in lines:
        if c < every:
            out.append(l)
            c += 1
        if c == every:
            print(*out)
            out = []
            c = 0