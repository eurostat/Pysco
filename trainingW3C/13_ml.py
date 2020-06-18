import numpy
from scipy import stats
import matplotlib.pyplot as plt

speed = [99,86,87,88,111,86,103,87,94,78,77,85,86]

print(numpy.mean(speed))
print(numpy.median(speed))
print( numpy.median([99,86,87,88,86,103,87,94,78,77,85,86]) )
print(stats.mode(speed))
print(numpy.std(speed))
print(numpy.var(speed))
print(numpy.percentile(speed, 75))
print(numpy.percentile(speed, 90))




x = numpy.random.uniform(0.0, 5.0, 1000000)
#print(x)
#plt.hist(x, 100)
#plt.show()


#x = numpy.random.normal(5.0, 1.0, 10000000)
#plt.hist(x, 1000)
#plt.show()


x = [5,7,8,7,2,17,2,9,4,11,12,9,6]
y = [99,86,87,88,111,86,103,87,94,78,77,85,86]
#plt.scatter(x, y)
#plt.show()

x = numpy.random.normal(5.0, 1.0, 1000)
y = numpy.random.normal(10.0, 2.0, 1000)
#plt.scatter(x, y)
#plt.show()





# linear regression

x = [5,7,8,7,2,17,2,9,4,11,12,9,6]
y = [99,86,87,88,111,86,103,87,94,78,77,85,86]

slope, intercept, r, p, std_err = stats.linregress(x, y)
def myfunc(x):
  return slope * x + intercept

mymodel = list(map(myfunc, x))

#plt.scatter(x, y)
#plt.plot(x, mymodel)
#plt.show()

print(r)





# Polynomial Regression

import matplotlib.pyplot as plt

x = [1,2,3,5,6,7,8,9,10,12,13,14,15,16,18,19,21,22]
y = [100,90,80,60,60,55,60,65,70,70,75,76,78,79,90,99,99,100]

mymodel = numpy.poly1d(numpy.polyfit(x, y, 3))
myline = numpy.linspace(1, 22, 100)

#plt.scatter(x, y)
#plt.plot(myline, mymodel(myline))
#plt.show()

from sklearn.metrics import r2_score
print(r2_score(y, mymodel(x)))






# Multiple Regression



