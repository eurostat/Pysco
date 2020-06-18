

def my_function(fname):
  print(fname + " Refsnes")

my_function("Emil")
my_function("Tobias")
my_function("Linus")



def my_function2(fname, lname):
  print(fname + " " + lname)

my_function2("Emil", "Refsnes")



def my_function3(*kids):
  print("The youngest child is " + kids[2])

my_function3("Emil", "Tobias", "Linus")




def my_function4(child3, child2, child1):
  print("The youngest child is " + child3)

my_function4(child1 = "Emil", child2 = "Tobias", child3 = "Linus")



def my_function5(**kid):
  print("His last name is " + kid["lname"])

my_function5(fname = "Tobias", lname = "Refsnes")



def my_function6(country = "Norway"):
  print("I am from " + country)

my_function6("Sweden")
my_function6("India")
my_function6()
my_function6("Brazil")




def my_function7(food):
  for x in food: print(x)
my_function7(["apple", "banana", "cherry"])




def my_function8(x):
  return 5 * x

print(my_function8(3))
print(my_function8(5))
print(my_function8(9))



def tri_recursion(k):
  if(k > 0):
    result = k + tri_recursion(k - 1)
    print(result)
  else:
    result = 0
  return result

print("Recursion Example Results")
tri_recursion(6)








#define function internally
def fun(x):
  def fun2(y):
    return y*3
  return fun2(x)*2

print(fun(10000))

#return function
def fun_(x):
  def fun2_(y):
    return y*x
  return fun2_

#print(fun_)
#print(fun_(7))
"""print(fun(7) is fun(7))
print(fun(7) == fun(7))
print(fun(7) is fun(9))
print(fun(7) == fun(9))"""
print(fun_(7)(8))







#lambdas

x = lambda a : a + 10
print(x(50))

x = lambda a, b : a * b
print(x(50, 60))


def myfunc(n):
  return lambda a : a * n
mydoubler = myfunc(2)
#print(myfunc)
#print(mydoubler)
print(mydoubler(1111))
mytripler = myfunc(3)
print(mytripler(1111))

