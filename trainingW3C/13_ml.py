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

import pandas

df = pandas.read_csv("trainingW3C/cars.csv")
#print(df)
X = df[['Weight', 'Volume']]
y = df['CO2']

from sklearn import linear_model
regr = linear_model.LinearRegression()
regr.fit(X, y)

print(regr.coef_)

#predict the CO2 emission of a car where the weight is 2300kg, and the volume is 1300ccm:
predictedCO2 = regr.predict([[2300, 1300]])

print(predictedCO2)





# train/test

numpy.random.seed(2)

x = numpy.random.normal(3, 1, 100)
y = numpy.random.normal(150, 40, 100) / x
#plt.scatter(x, y)
#plt.show()


train_x = x[:80]
train_y = y[:80]
#plt.scatter(train_x, train_y)
#plt.show()

test_x = x[80:]
test_y = y[80:]
#plt.scatter(test_x, test_y)
#plt.show()


mymodel = numpy.poly1d(numpy.polyfit(train_x, train_y, 4))

#plt.scatter(train_x, train_y)
#myline = numpy.linspace(0, 6, 100)
#plt.plot(myline, mymodel(myline))
#plt.show()

r2 = r2_score(train_y, mymodel(train_x))
print(r2)

r2 = r2_score(test_y, mymodel(test_x))
print(r2)







# Decision Tree



import pandas
from sklearn import tree
import pydotplus
from sklearn.tree import DecisionTreeClassifier
import matplotlib.pyplot as plt
import matplotlib.image as pltimg

df = pandas.read_csv("trainingW3C/shows.csv")
#print(df)

d = {'UK': 0, 'USA': 1, 'N': 2}
df['Nationality'] = df['Nationality'].map(d)
d = {'YES': 1, 'NO': 0}
df['Go'] = df['Go'].map(d)

#print(df)


features = ['Age', 'Experience', 'Rank', 'Nationality']
X = df[features]
y = df['Go']
#print(X)
#print(y)


dtree = DecisionTreeClassifier()
dtree = dtree.fit(X, y)
data = tree.export_graphviz(dtree, out_file=None, feature_names=features)
graph = pydotplus.graph_from_dot_data(data)
graph.write_png('trainingW3C/mydecisiontree.png')

img = pltimg.imread('trainingW3C/mydecisiontree.png')
imgplot = plt.imshow(img)
plt.show()


