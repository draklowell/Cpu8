from parser import parse

with open("netlists/interface.frp", "r") as f:
    data = f.read()

print(parse(data))
