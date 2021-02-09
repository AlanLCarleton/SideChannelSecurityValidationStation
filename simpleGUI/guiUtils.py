import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from numpy import array, asarray, ma


def plotTraces(traces):
    plt.figure(1)
    plt.plot(traces[0], 'r')
    plt.plot(traces[1], 'g')
    plt.plot(traces[2], 'b')
    plt.plot(traces[3], 'c')
    plt.plot(traces[4], 'm')
    plt.ion()
    plt.show()
    plt.pause(.001)

def writeResultsToCSV(attackResults):
    '''
    Write attack results to a csv file
    '''
    with open('attackResults.csv', 'w') as file:
        for line in attackResults:
            file.write(line)

def checkZeroCorrelation():
    '''
    Check if the correlation colum of 'attackResults.csv' contains any zero correlation

    Return True if one of the 'Correlation' value is zero, False if all correlation is non zero
    '''
    df = pd.read_csv('attackResults.csv', sep='\s{1,}')
    df.columns = ['Subkey', 'KGuess', 'Correlation']
    for correlation in df['Correlation']:
        if float(correlation) == 0.0:
            return True
    
    return False

def tTestCalculation(a, b):
    '''
    Calculates Welch T-test values

    param   a       Array of values
            b       Array of values
    return  t-tst   Array of T-values      
    '''
    #convert plain array to numpy masked array
    a = ma.asarray(a)
    b = ma.asarray(b)
    if a.size == 0 or b.size == 0:
        return (np.nan, np.nan)

    (x1, x2) = (a.mean(axis=0), b.mean(axis=0))
    (s1, s2) = (a.std(axis=0), b.std(axis=0))
    (n1, n2) = (a.count(axis=0), b.count(axis=0))

    
    vn1 = (s1**2)/n1
    vn2 = (s2**2)/n2
    
    denom = ma.sqrt(vn1 + vn2)

    #ignore division errors i.e. x/0
    with np.errstate(divide='ignore', invalid='ignore'):
        t = (x1-x2) / denom

    return t
