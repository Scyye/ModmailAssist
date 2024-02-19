# Get the contents of cog/admin.py
with open(r"cogs/admin.py", "r") as file:
    contents = file.readlines()

start = False

for i in range(len(contents)):
    if contents[i].startswith("class"):
        start = True

    if contents[i] == "" or not start:
        continue

    contents[i] = contents[i].replace("\n", "\n\t")


contents = "".join(contents)

with open("cogs/admin.py", "w") as file:
    file.write(contents)