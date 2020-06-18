
#strings

a = """Lorem ipsum dolor sit amet,
consectetur adipiscing elit,
sed do eiusmod tempor incididunt
ut labore et dolore magna aliqua."""
print(a)

#string as array
a = "Hello, World!"
print(len(a))
print(a[1])
print(a[2:5])
print(a[-5:-2])
print("  sss s sss s  ".strip())
print(a.lower())
print(a.upper())
print(a.replace("H", "J"))
print(a.split(","))
print("ell" in a)
print("jgjhgjhg" in a)
print(a.count("l"))

txt = "We are the so-called \"Vikings\" from the north."



# format

price = 49
#txt = "The price is {} dollars"
txt = "The price is {:.2f} dollars"
print(txt.format(price))

quantity = 3
itemno = 567
price = 49
myorder = "I want {} pieces of item number {} for {:.2f} dollars."
print(myorder.format(quantity, itemno, price))

quantity = 3
itemno = 567
price = 49
myorder = "I want {0} pieces of item number {1} for {2:.2f} dollars."
print(myorder.format(quantity, itemno, price))

age = 36
name = "John"
txt = "His name is {1}. {1} is {0} years old."
print(txt.format(age, name))

myorder = "I have a {carname}, it is a {model}."
print(myorder.format(carname = "Ford", model = "Mustang"))

