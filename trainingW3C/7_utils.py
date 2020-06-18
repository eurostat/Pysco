import datetime


# datetime

x = datetime.datetime.now()
print(x)
print(x.year)
print(x.strftime("%A"))

x = datetime.datetime(2020, 5, 17)
print(x)
print(x.strftime("%B"))


# math

print(min(5, 10, 25))
print(max(5, 10, 25))
print(abs(-7.25))
print(pow(2, 10))

import math

print(math.sqrt(64))
print(math.ceil(1.4)) # returns 2
print(math.floor(1.4)) # returns 1
print(math.pi)

