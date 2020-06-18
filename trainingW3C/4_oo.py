
class Person:
  def __init__(self, name, age):
    self.name = name
    self.age = age

  def myfunc(self):
    print("Hello my name is " + self.name + " - I am " + str(self.age))

p1 = Person("John", 36)

print(p1)
print(p1.name)
print(p1.age)
p1.myfunc()

p1.age = 40
p1.myfunc()

del p1.age
#NO: p1.eee = "sss"
del p1







class Person2:
  def __init__(self, fname, lname):
    self.firstname = fname
    self.lastname = lname

  def printname(self):
    print(self.firstname, self.lastname)



class Student(Person2):
  def __init__(self, fname, lname, year):
    super().__init__(fname, lname)
    self.graduationyear = year

  def welcome(self):
    print("Welcome", self.firstname, self.lastname, "to the class of", self.graduationyear)

x = Student("Mike", "Olsen", 2020)
x.printname()
x.welcome()

