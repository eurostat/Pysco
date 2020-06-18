import re

txt = "The rain in Spain"
print(txt)

x = re.search("^The.*Spain$", txt)
print(x)

x = re.findall("ai", txt)
print(x)

x = re.findall("Portugal", txt)
print(x)

x = re.search("\s", txt)
print("The first white-space character is located in position:", x.start())

x = re.search("Portugal", txt)
print(x)

x = re.split("\s", txt)
print(x)

x = re.split("\s", txt, 1)
print(x)

x = re.sub("\s", "9", txt)
print(x)

x = re.sub("\s", "9", txt, 2)
print(x)



x = re.search(r"\bS\w+", txt)
print(x.span())

x = re.search(r"\bS\w+", txt)
print(x.string)

x = re.search(r"\bS\w+", txt)
print(x.group())

