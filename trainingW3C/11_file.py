
#"r" - Read - Default value. Opens a file for reading, error if the file does not exist
#"a" - Append - Opens a file for appending, creates the file if it does not exist
#"w" - Write - Opens a file for writing, creates the file if it does not exist
#"x" - Create - Creates the specified file, returns an error if the file exists

#"t" - Text - Default value. Text mode
#"b" - Binary - Binary mode (e.g. images)


f = open("trainingW3C/demofile.txt")
# same as f = open("demofile.txt", "rt")


f = open("trainingW3C/demofile.txt", "r")
print(f.read())

f = open("trainingW3C/demofile.txt", "r")
print(f.read(5))

f = open("trainingW3C/demofile.txt", "r")
print(f.readline())

f = open("trainingW3C/demofile.txt", "r")
for x in f:
  print(x)

f.close()


f = open("trainingW3C/demofile2.txt", "a")
f.write("Now the file has more content!")
f.close()

#open and read the file after the appending:
f = open("trainingW3C/demofile2.txt", "r")
print(f.read())



f = open("trainingW3C/demofile3.txt", "w")
f.write("Woops! I have deleted the content!")
f.close()

#open and read the file after the appending:
f = open("trainingW3C/demofile3.txt", "r")
print(f.read())


f = open("trainingW3C/myfile.txt", "x")
f = open("trainingW3C/myfile.txt", "w")

import os
os.remove("trainingW3C/myfile.txt")


import os
if os.path.exists("demofile.txt"):
  os.remove("demofile.txt")
else:
  print("The file does not exist")


import os
#os.rmdir("myfolder")

