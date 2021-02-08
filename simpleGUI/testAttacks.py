import chipwhisperer as cw
import chipwhisperer.analyzer as cwa
import guiUtils as utils
import time
import numpy as np
from scipy.stats import ttest_ind
import matplotlib.pyplot as plt
from tqdm import trange


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


#Predetermined AES Model:
sbox = [
    # 0    1    2    3    4    5    6    7    8    9    a    b    c    d    e    f
    0x63, 0x7c, 0x77, 0x7b, 0xf2, 0x6b, 0x6f, 0xc5, 0x30, 0x01, 0x67, 0x2b, 0xfe, 0xd7, 0xab, 0x76,  # 0
    0xca, 0x82, 0xc9, 0x7d, 0xfa, 0x59, 0x47, 0xf0, 0xad, 0xd4, 0xa2, 0xaf, 0x9c, 0xa4, 0x72, 0xc0,  # 1
    0xb7, 0xfd, 0x93, 0x26, 0x36, 0x3f, 0xf7, 0xcc, 0x34, 0xa5, 0xe5, 0xf1, 0x71, 0xd8, 0x31, 0x15,  # 2
    0x04, 0xc7, 0x23, 0xc3, 0x18, 0x96, 0x05, 0x9a, 0x07, 0x12, 0x80, 0xe2, 0xeb, 0x27, 0xb2, 0x75,  # 3
    0x09, 0x83, 0x2c, 0x1a, 0x1b, 0x6e, 0x5a, 0xa0, 0x52, 0x3b, 0xd6, 0xb3, 0x29, 0xe3, 0x2f, 0x84,  # 4
    0x53, 0xd1, 0x00, 0xed, 0x20, 0xfc, 0xb1, 0x5b, 0x6a, 0xcb, 0xbe, 0x39, 0x4a, 0x4c, 0x58, 0xcf,  # 5
    0xd0, 0xef, 0xaa, 0xfb, 0x43, 0x4d, 0x33, 0x85, 0x45, 0xf9, 0x02, 0x7f, 0x50, 0x3c, 0x9f, 0xa8,  # 6
    0x51, 0xa3, 0x40, 0x8f, 0x92, 0x9d, 0x38, 0xf5, 0xbc, 0xb6, 0xda, 0x21, 0x10, 0xff, 0xf3, 0xd2,  # 7
    0xcd, 0x0c, 0x13, 0xec, 0x5f, 0x97, 0x44, 0x17, 0xc4, 0xa7, 0x7e, 0x3d, 0x64, 0x5d, 0x19, 0x73,  # 8
    0x60, 0x81, 0x4f, 0xdc, 0x22, 0x2a, 0x90, 0x88, 0x46, 0xee, 0xb8, 0x14, 0xde, 0x5e, 0x0b, 0xdb,  # 9
    0xe0, 0x32, 0x3a, 0x0a, 0x49, 0x06, 0x24, 0x5c, 0xc2, 0xd3, 0xac, 0x62, 0x91, 0x95, 0xe4, 0x79,  # a
    0xe7, 0xc8, 0x37, 0x6d, 0x8d, 0xd5, 0x4e, 0xa9, 0x6c, 0x56, 0xf4, 0xea, 0x65, 0x7a, 0xae, 0x08,  # b
    0xba, 0x78, 0x25, 0x2e, 0x1c, 0xa6, 0xb4, 0xc6, 0xe8, 0xdd, 0x74, 0x1f, 0x4b, 0xbd, 0x8b, 0x8a,  # c
    0x70, 0x3e, 0xb5, 0x66, 0x48, 0x03, 0xf6, 0x0e, 0x61, 0x35, 0x57, 0xb9, 0x86, 0xc1, 0x1d, 0x9e,  # d
    0xe1, 0xf8, 0x98, 0x11, 0x69, 0xd9, 0x8e, 0x94, 0x9b, 0x1e, 0x87, 0xe9, 0xce, 0x55, 0x28, 0xdf,  # e
    0x8c, 0xa1, 0x89, 0x0d, 0xbf, 0xe6, 0x42, 0x68, 0x41, 0x99, 0x2d, 0x0f, 0xb0, 0x54, 0xbb, 0x16  # f
]


def aes_internal(inputdata, key):
    return sbox[inputdata ^ key]


def calculate_diffs(guess, numtraces, textin_array, trace_array, byteindex=0, bitnum=0):
    """Perform a simple DPA on two traces """
    one_list = []
    zero_list = []

    for trace_index in range(numtraces):
        hypothetical_leakage = aes_internal(
            guess, textin_array[trace_index][byteindex])

        #Mask off the requested bit
        if hypothetical_leakage & (1 << bitnum):
            one_list.append(trace_array[trace_index])
        else:
            zero_list.append(trace_array[trace_index])

    one_avg = np.asarray(one_list).mean(axis=0)
    zero_avg = np.asarray(zero_list).mean(axis=0)
    return abs(one_avg - zero_avg)


def basicCWDPA(scope, N):

    #Store your key_guess here, compare to known_key
    key_guess = []
    known_key = [0x2b, 0x7e, 0x15, 0x16, 0x28, 0xae, 0xd2,
                 0xa6, 0xab, 0xf7, 0x15, 0x88, 0x09, 0xcf, 0x4f, 0x3c]
    #Which bit to target
    bitnum = 0

    full_diffs_list = []
    #Init scope and key text pairs:
    target = cw.target(scope)
    ktp = cw.ktp.Basic()
    trace_array = []
    textin_array = []
    key, text = ktp.next()
    #target.set_key(key)
    target.simpleserial_write('k', key)

    #Collect N Traces:
    for i in trange(N, desc='Capturing traces'):
        scope.arm()

        target.simpleserial_write('p', text)

        ret = scope.capture()
        if ret:
            print("Target timed out!")
            continue

        response = target.simpleserial_read('r', 16)

        trace_array.append(scope.get_last_trace())
        textin_array.append(text)

        key, text = ktp.next()

    scope.dis()
    target.dis()  # post-trace routine
    print("scope and target de-initialized")

    resultString = ''
    #execute DPA-AES Attack
    for subkey in trange(0, 16, desc="Attacking Subkey"):

        max_diffs = [0]*256
        full_diffs = [0]*256

        for guess in range(0, 256):
            full_diff_trace = calculate_diffs(guess, np.shape(
                trace_array)[0], textin_array, trace_array, subkey, bitnum)
            full_diff_trace = full_diff_trace[(0 + subkey*0):]
            max_diffs[guess] = np.max(full_diff_trace)
            full_diffs[guess] = full_diff_trace

        #Make copy of the list
        full_diffs_list.append(full_diffs[:])

        #Get argument sort, as each index is the actual key guess.
        sorted_args = np.argsort(max_diffs)[::-1]

        #Keep most likely
        key_guess.append(sorted_args[0])

        #Print results
        resultString += ("Subkey %2d - most likely %02X (actual %02X)" % (subkey, key_guess[subkey], known_key[subkey]))

        #Print other top guesses
        resultString += ("\nTop 5 guesses: ")
        for i in range(0, 5):
            g = sorted_args[i]
            resultString += ("   %02X - Diff = %f" % (g, max_diffs[g]))

        resultString += ("\n\n")

    return resultString
