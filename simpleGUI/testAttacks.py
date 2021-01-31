import chipwhisperer as cw
import chipwhisperer.analyzer as cwa
import guiUtils as utils
import time
import numpy as np
from scipy.stats import ttest_ind
import matplotlib.pyplot as plt


def basicCPA(scope, traceAmount):
    target = cw.target(scope)
    
    #capturing some traces
    ktp = cw.ktp.Basic()
    trace_array = []
    textin_array = []

    proj = cw.create_project("Lab Test", overwrite=True)


    print(proj.location)

    N = traceAmount
    for i in range(N):
        key, text = ktp.next()
        trace = cw.capture_trace(scope, target, text, key)
        if not trace:
            continue

        proj.traces.append(trace)

    scope.dis()
    target.dis()

    #EXAMPLE OF PLOTTING TRACE, NOT SURE IF plotTraces IS PLOTTING CORRECT VALUES YET
    utils.plotTraces(proj.waves)

    traceSring = 'Trace key: ' + str(trace.key).replace('CWbytearray', '') + '\n\n'
    i = 1
    for trace in proj.traces:
        temp = ('Trace ' + str(i) + '\nTrace wave: ')
        #for x in trace.wave:
            #temp += str(x)
        
        temp += '\n' + 'Text in: ' + str(trace.textin)+'\n' + 'Text out: ' + str(trace.textout)+'\n'
        traceSring += str(temp).replace('CWbytearray', '') + '\n'
        i += 1

    # we can access wave, textin, etc as a whole with proj.traces
    '''
    for trace in proj.traces:
        print(trace.wave[0], trace.textin, trace.textout, trace.key)

    # can also access individually with proj.waves, proj.textins, etc.
    for wave in proj.waves:
        print(wave[0])
    '''

    #************************ChipWhisperer Analyzer*******************
    leak_model = cwa.leakage_models.sbox_output
    attack = cwa.cpa(proj, leak_model)
    #print(attack)

    time1 = time.perf_counter()    
    results = attack.run()
    time2 = time.perf_counter()
    proj.close(save=True)
    return(str(results), round(time2-time1, 3), traceSring)


def basicCWTVLA(scope, cryptoTarget, N):  # N number of traces as args
    #replicates ChipWhisperer's SCA203 Intro to TVLA tutorial
    #Based on CW SCA203 TVLA & CWTVLA Untitled.ipynb
    target = cw.target(scope)  # Handled by SimpleGUI?

    #init & capture some traces
    ktp = cw.ktp.TVLATTest()
    ktp.init(N)
    fixed_text_arr = []
    rand_text_arr = []

    #collect traces for both fixed and random sets
    for i in range(2*N):
        key, text = ktp.next()  # I think cwtvla switches ktp's between both randomly
        if cryptoTarget == 'TINYAES128C':
            trace = cw.capture_trace(scope, target, text, key)
        #TEMPORARY IMPLEMENTATION FOR DES
        elif cryptoTarget == 'AVRCRYPTOLIB':
            trace = cw.capture_trace(scope, target, text, key, False)
        if not trace:
            print("[Trace: %d]: No trace captured.\n", i)
            continue
        if trace.textin == bytearray([0xda, 0x39, 0xa3, 0xee, 0x5e, 0x6b, 0x4b, 0x0d, 0x32, 0x55, 0xbf, 0xef, 0x95, 0x60, 0x18, 0x90]):
            # Check if this ktp trace matches I_fixed
            fixed_text_arr.append(trace.wave)
        else:
            rand_text_arr.append(trace.wave)

    scope.dis()
    target.dis()  # post-trace routine
    print("scope and target de-initialized\n")

    fixed_text_arr = np.array(fixed_text_arr)
    fixed_arr_len = len(fixed_text_arr)
    print("reported fixed traces length:%d\n", fixed_arr_len)
    rand_text_arr = np.array(rand_text_arr)
    print("reported random traces length:%d\n", len(rand_text_arr))

    #calculate mean of both fixed and random + plots
    fixed_text_mean = np.mean(fixed_text_arr, axis=0)
    rand_text_mean = np.mean(rand_text_arr, axis=0)
    #cw.plot(rand_text_mean) * cw.plot(fixed_text_mean)
    plt.figure(1)
    plt.title('Mean of fixed and random text traces')
    plt.plot(rand_text_mean, 'r', label='random')
    plt.plot(fixed_text_mean, 'g', label='fixed')
    plt.xlabel('trace')
    plt.ylabel('power')
    plt.legend(loc='upper right')
    plt.show()

    #show differences in Fixed Vs Random plots
    #cw.plot(fixed_text_mean - rand_text_mean)
    plt.figure(2)
    plt.title('Differences in mean fixed and random text traces')
    plt.plot(fixed_text_mean - rand_text_mean)
    plt.xlabel('trace')
    plt.ylabel('power difference')
    plt.show()
    '''
    #actually perform & plot t-test (idk if its welch)
    t_val = ttest_ind(fixed_text_mean, rand_text_arr,
                      axis=0, equal_var=False)[0]
    #cw.plot(t_val)
    plt.figure(3)
    plt.title('T-test results')
    plt.plot(t_val)
    plt.xlabel('trace')
    plt.ylabel('t-value')
    plt.show()
    '''
    #Plot last comprehensive graph from SCA203 Tutorial
    t_val = [ttest_ind(fixed_text_arr[:N//2], rand_text_arr[:N//2], axis=0, equal_var=False)
             [0], ttest_ind(fixed_text_arr[N//2:], rand_text_arr[N//2:], axis=0, equal_var=False)[0]]
    #cv = cw.plot(t_val[0]) * cw.plot(t_val[1]) * cw.plot([4.5]*len(fixed_text_arr[0])) * cw.plot([-4.5]*len(fixed_text_arr[0]))
    #cv
    t_valAbove = [[], []]
    for i in range(2):
        for x in t_val[i]:
            if abs(x) >= 4.5:
                t_valAbove[i].append(x)

    resultStr = ''
    resultStr += (str(len(t_valAbove[0])) +
          ' t-values calculated from first half of traces are >=4.5\n')
    resultStr += (str(len(t_valAbove[1])) +
          ' t-values calculated from second half of traces are >=4.5\n')

    setCompare = len(set(t_valAbove[0]) & set(t_valAbove[1]))
    resultStr += ('\nFrom both >=4.5 T-value sets: ' +
          str(setCompare) + ' values are the same at the same point (trace)\n\n')

    if setCompare > 0:
        resultStr += ('This device can be considered to have failed TVLA T-test (1 or more T-test values were >=4.5 at the same point)\n')
    else:
        resultStr += ('This device can be considered to have passed TVLA T-test\n')

    plt.figure(4)
    plt.title('T-test results with +-4.5 bounds')
    plt.plot(t_val[0], 'r', label='first half of traces used')
    plt.plot(t_val[1], 'b', label='second half of traces used')
    plt.plot([4.5]*len(fixed_text_arr[0]), 'g', label='+4.5')
    plt.plot([-4.5]*len(fixed_text_arr[0]), 'g', label='-4.5')
    plt.xlabel('trace')
    plt.ylabel('t-vaue')
    plt.legend(loc='lower right')
    plt.ion()
    plt.show()
    plt.pause(.001)

    return (t_valAbove, resultStr)
