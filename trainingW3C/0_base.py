#This is a comment.
print("Hello, World!")

if 5 > 2:
  print("Five is greater than two!")

x = 5
st = "Hello!"
print(st, x)

"""
This is a comment
written in
more than just one line
"""

x, y, z = "Orange", "Banana", "Cherry"
print(x)
print(y)
print(z)


x = y = z = "Orange"
print(x)
print(y)
print(z)

x = "Python is "
y = "awesome"
print(x + y)





x = "awesomeXXX"

def myfunc():
  print("Python is " + x)

myfunc()




#types
x = 5
print(type(x))
print(isinstance(x, int))

list_ = ["apple", "banana", "cherry"]
tuple_ = ("apple", "banana", "cherry")
range_ = range(6)
dict_ = {"name" : "John", "age" : 36}
set_ = {"apple", "banana", "cherry"}
bool_ = True



x_ = str("Hello World")
x = int(20)
x = float(20.5)
print(x_ + " ddd " + str(454))


import random
print(random.randrange(1, 100))



#operators
x = ["apple", "banana"]
y = ["apple", "banana"]
z = x

print(x is z)
# returns True because z is the same object as x
print(x is y)
# returns False because x is not the same object as y, even if they have the same content
print(x == y)
# to demonstrate the difference betweeen "is" and "==": this comparison returns True because x is equal to y



x = ["apple", "banana"]
print("banana" in x)








#tests

a = 200
b = 33
if b > a:
  print("b is greater than a")
elif a == b:
  print("a and b are equal")
else:
  print("a is greater than b")


if a > b: print("a is greater than b")


a = 2
b = 330
print("A") if a > b else print("B")

a = 330
b = 330
print("A") if a > b else print("=") if a == b else print("B")




# while loop

i = 1
while i < 6:
  print(i)
  i += 1

i = 1
while i < 6:
  print(i)
  if i == 3: break
  i += 1

i = 0
while i < 6:
  i += 1
  if i == 3: continue
  print(i)

i = 1
while i < 6:
  print(i)
  #if i == 3: break
  i += 1
else:
  print("i is no longer less than 6")



#for loop

fruits = ["apple", "banana", "cherry"]
for x in fruits:
  print(x)

for x in "banana":
  print(x)


fruits = ["apple", "banana", "cherry"]
for x in fruits:
  print(x)
  if x == "banana": break

fruits = ["apple", "banana", "cherry"]
for x in fruits:
  if x == "banana": continue
  print(x)


#range
for x in range(6): print(x)
for x in range(2, 6): print(x)
for x in range(2, 30, 3): print(x)


for x in range(6):
  print(x)
else:
  print("Finally finished!")







# exceptions

try:
  #x = "ahahah"
  del x
  print(x)
except NameError:
  print("Variable x is not defined")
except:
  print("Something else went wrong")
else:
  print("Nothing went wrong")
finally:
  print("The 'try except' is finished")

x = -1
#if x < 0: raise Exception("Sorry, no numbers below zero")

x = "hello"
#if not type(x) is int: raise TypeError("Only integers are allowed")

