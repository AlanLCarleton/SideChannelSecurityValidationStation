import matplotlib.pyplot as plt

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
