'''
Created on Aug 30, 2018
Tree-Based Classifier Methods
@author: Jelliy
'''
from numpy import *
from collections import Counter
from sklearn import datasets
from sklearn import tree
from sklearn.cross_validation import train_test_split
import matplotlib.pyplot as plt

# 给定特征和特征值，划分数据集
def binSplitDataSet(dataSet, feature, value):
    mat0 = dataSet[nonzero(dataSet[:, feature] > value)[0], :]
    mat1 = dataSet[nonzero(dataSet[:, feature] <= value)[0], :]
    return mat0, mat1


# 返回子叶点的平均数
def regLeaf(dataSet):  # returns the value used for each leaf
    return mean(dataSet[:, -1])

# 返回子叶点 标签最多的
def clfLeaf(dataSet):
    return Counter(dataSet[:, -1]).most_common(1)[0][0]

# 返回子叶点总方差
def regErr(dataSet):
    return var(dataSet[:, -1]) * shape(dataSet)[0]

def calcGini(target):
    length = len(target)
    gini = 1.
    for key,value in Counter(target).items():
        prob = value / float(length)
        gini -= prob * prob
    return gini

def linearSolve(dataSet):  # helper function used in two places
    m, n = shape(dataSet)
    X = mat(ones((m, n)));
    Y = mat(ones((m, 1)))  # create a copy of data with 1 in 0th postion
    X[:, 1:n] = dataSet[:, 0:n - 1];
    Y = dataSet[:, -1]  # and strip out Y
    xTx = X.T * X
    if linalg.det(xTx) == 0.0:
        raise NameError('This matrix is singular, cannot do inverse,\n\
        try increasing the second value of ops')
    ws = xTx.I * (X.T * Y)
    return ws, X, Y


def modelLeaf(dataSet):  # create linear model and return coeficients
    ws, X, Y = linearSolve(dataSet)
    return ws


def modelErr(dataSet):
    ws, X, Y = linearSolve(dataSet)
    yHat = X * ws
    return sum(power(Y - yHat, 2))


def chooseBestSplit(dataSet, leafType=regLeaf, errType=regErr, ops=(1, 4)):
    #容许的误差下降值
    tolS = ops[0]

    #切分的最少样本数
    tolN = ops[1]

    # if all the target variables are the same value: quit and return value
    if len(set(dataSet[:, -1])) == 1:  # exit cond 1
        return None, leafType(dataSet)
    m, n = shape(dataSet)
    # the choice of the best feature is driven by Reduction in RSS error from mean
    S = calcGini(dataSet[:,-1])
    bestS = inf;
    bestIndex = 0;
    bestValue = 0
    for featIndex in range(n - 1):
        for splitVal in set(dataSet[:, featIndex]):
            mat0, mat1 = binSplitDataSet(dataSet, featIndex, splitVal)
            if (shape(mat0)[0] < tolN) or (shape(mat1)[0] < tolN): continue
            prob0 = len(mat0) / float(len(dataSet))
            prob1 = len(mat1) / float(len(dataSet))
            newS = prob0*calcGini(mat0[:,-1]) + prob1*calcGini(mat1[:,-1])
            if newS < bestS:
                bestIndex = featIndex
                bestValue = splitVal
                bestS = newS
    # if the decrease (S-bestS) is less than a threshold don't do the split
    if (S - bestS) < tolS:
        return None, leafType(dataSet)  # exit cond 2
    mat0, mat1 = binSplitDataSet(dataSet, bestIndex, bestValue)
    if (shape(mat0)[0] < tolN) or (shape(mat1)[0] < tolN):  # exit cond 3
        return None, leafType(dataSet)
    return bestIndex, bestValue  # returns the best feature to split on
    # and the value used for that split


def createTree(dataSet, leafType=regLeaf, errType=regErr,
               ops=(1, 4)):  # assume dataSet is NumPy Mat so we can array filtering
    feat, val = chooseBestSplit(dataSet, leafType, errType, ops)  # choose the best split
    if feat == None: return val  # if the splitting hit a stop condition return val
    retTree = {}
    retTree['spInd'] = feat
    retTree['spVal'] = val
    # 根据特征和特征值，二分数据集
    lSet, rSet = binSplitDataSet(dataSet, feat, val)
    retTree['right'] = createTree(rSet, leafType, errType, ops)
    retTree['left'] = createTree(lSet, leafType, errType, ops)
    return retTree


def isTree(obj):
    return (type(obj).__name__ == 'dict')


def getMean(tree):
    if isTree(tree['right']): tree['right'] = getMean(tree['right'])
    if isTree(tree['left']): tree['left'] = getMean(tree['left'])
    return (tree['left'] + tree['right']) / 2.0


def prune(tree, testData):
    if shape(testData)[0] == 0: return getMean(tree)  # if we have no test data collapse the tree
    if (isTree(tree['right']) or isTree(tree['left'])):  # if the branches are not trees try to prune them
        lSet, rSet = binSplitDataSet(testData, tree['spInd'], tree['spVal'])
    if isTree(tree['left']): tree['left'] = prune(tree['left'], lSet)
    if isTree(tree['right']): tree['right'] = prune(tree['right'], rSet)
    # if they are now both leafs, see if we can merge them
    if not isTree(tree['left']) and not isTree(tree['right']):
        lSet, rSet = binSplitDataSet(testData, tree['spInd'], tree['spVal'])
        errorNoMerge = sum(power(lSet[:, -1] - tree['left'], 2)) + \
                       sum(power(rSet[:, -1] - tree['right'], 2))
        treeMean = (tree['left'] + tree['right']) / 2.0
        errorMerge = sum(power(testData[:, -1] - treeMean, 2))
        if errorMerge < errorNoMerge:
            print("merging")
            return treeMean
        else:
            return tree
    else:
        return tree


def regTreeEval(model, inDat):
    return float(model)

def clfTreeEval(model, inDat):
    return int(model)

def modelTreeEval(model, inDat):
    n = shape(inDat)[1]
    X = mat(ones((1, n + 1)))
    X[:, 1:n + 1] = inDat
    return float(X * model)


def treeForeCast(tree, inData, modelEval=regTreeEval):
    if not isTree(tree):
        return modelEval(tree, inData)
    if inData[tree['spInd']] > tree['spVal']:
        if isTree(tree['left']):
            return treeForeCast(tree['left'], inData, modelEval)
        else:
            return modelEval(tree['left'], inData)
    else:
        if isTree(tree['right']):
            return treeForeCast(tree['right'], inData, modelEval)
        else:
            return modelEval(tree['right'], inData)


def createForeCast(tree, testData, modelEval=regTreeEval):
    m = len(testData)
    yHat = np.zeros(m)
    for i in range(m):
        yHat[i] = treeForeCast(tree, np.array(testData[i]).flatten(), modelEval)
    return yHat



import numpy as np



if __name__ == '__main__':
    iris = datasets.load_iris()
    X_train, X_test, y_train, y_test = train_test_split(iris.data, iris.target, random_state=1)
    dataSet = np.hstack((X_train,y_train.reshape((-1,1))))
    myTree = createTree(dataSet, leafType=clfLeaf,ops=(0.1, 5))
    yHat = createForeCast(myTree, X_test, modelEval=clfTreeEval)
    acc = (yHat == y_test).sum()/float(len(yHat))
    print(acc)
    print(myTree)

    # 使用sklearn 决策树去预测
    clf = tree.DecisionTreeClassifier()
    clf.fit(X_train,y_train)
    yHat1 = clf.predict(X_test)
    acc1 = (yHat1 == y_test).sum()/float(len(yHat1))
    print(acc1)
    #plt.scatter(X_train[:, 0], X_train[:, 1])
    #plt.show()