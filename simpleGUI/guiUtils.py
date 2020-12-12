import matplotlib.pyplot as plt
import pandas as pd

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
