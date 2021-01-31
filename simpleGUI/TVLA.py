#TVLA.py
#For Group 43 of SYSC4907A
#Building an Integrated Station for Implementation Security Validation
#Supervisor: Professor Mostafa Taha, PhD.
# Version 1 (Brannon)

#This python module performs First Order Test Vector Leak Assesment in a Fixed Vs. Random (FVR) test.
#The default significance threshold for the Welch T-Test will be 4.5.


#Revise imports (remove unused)
import chipwhisperer as cw
import chipwhisperer.analyzer as cwa
import guiUtils as utils
import boardSetup
import time
import numpy as np
from scipy.stats import ttest_ind
import holoviews as hv
import matplotlib.pyplot as plt

#User defined AES keys/data (for basicTVLA):
#I_fixed = string for fixed test plaintext (hex)
#K_dev = string for AES device key (hex)
#K_gen = string for AES ciphertext generation (hex)
#I_rand = initial string for AES random test plaintext (hex)

SCOPETYPE = 'OPENADC'
PLATFORM = 'CWLITEXMEGA'
#PLATFORM = 'CWLITEARM'
CRYPTO_TARGET = 'TINYAES128C'
#CRYPTO_TARGET = 'AVRCRYPTOLIB'

def basicCWTVLA(N): #N number of traces as args
    #replicates ChipWhisperer's SCA203 Intro to TVLA tutorial
    #Based on CW SCA203 TVLA & CWTVLA Untitled.ipynb
    scope = boardSetup.runInitSetup(SCOPETYPE, PLATFORM, CRYPTO_TARGET)
    target = cw.target(scope)  # Handled by SimpleGUI?
    
    #init & capture some traces
    ktp = cw.ktp.TVLATTest()
    ktp.init(N)
    fixed_text_arr = []
    rand_text_arr = []

    #collect traces for both fixed and random sets
    for i in range(2*N):
        key, text = ktp.next() #I think cwtvla switches ktp's between both randomly
        if CRYPTO_TARGET == 'TINYAES128C':
            trace = cw.capture_trace(scope, target, text, key)
        #TEMPORARY IMPLEMENTATION FOR DES
        elif CRYPTO_TARGET == 'AVRCRYPTOLIB':
            trace = cw.capture_trace(scope, target, text, key, False)
        if not trace:
            print("[Trace: %d]: No trace captured.\n", i)
            continue
        if trace.textin == bytearray([0xda, 0x39, 0xa3, 0xee, 0x5e, 0x6b, 0x4b, 0x0d, 0x32, 0x55, 0xbf, 0xef, 0x95, 0x60, 0x18, 0x90]):
            fixed_text_arr.append(trace.wave) #Check if this ktp trace matches I_fixed
        else:
            rand_text_arr.append(trace.wave)
        
    scope.dis()
    target.dis() #post-trace routine
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
    plt.plot(rand_text_mean)
    plt.plot(fixed_text_mean)
    plt.show()

    #show differences in Fixed Vs Random plots
    #cw.plot(fixed_text_mean - rand_text_mean)
    plt.figure(2)
    plt.plot(fixed_text_mean - rand_text_mean)
    plt.show()

    #actually perform & plot t-test (idk if its welch)
    t_val = ttest_ind(fixed_text_mean, rand_text_arr,
                      axis=0, equal_var=False)[0]
    #cw.plot(t_val)
    plt.figure(3)
    plt.plot(t_val)
    plt.show()

    #Plot last comprehensive graph from SCA203 Tutorial
    t_val = [ttest_ind(fixed_text_arr[:N//2], rand_text_arr[:N//2], axis=0, equal_var=False)[0], ttest_ind(fixed_text_arr[N//2:], rand_text_arr[N//2:], axis=0, equal_var=False)[0]]
    #cv = cw.plot(t_val[0]) * cw.plot(t_val[1]) * cw.plot([4.5]*len(fixed_text_arr[0])) * cw.plot([-4.5]*len(fixed_text_arr[0]))
    #cv
    plt.figure(4)
    plt.plot(t_val[0])
    plt.plot(t_val[1])
    plt.plot([4.5]*len(fixed_text_arr[0]))
    plt.plot([-4.5]*len(fixed_text_arr[0]))
    plt.show()

    
    #EXAMPLE OF PLOTTING TRACE, NOT SURE IF plotTraces IS PLOTTING CORRECT VALUES YET
    #utils.plotTraces(proj.waves)

    # traceSring = 'Trace key: ' + str(trace.key).replace('CWbytearray', '') + '\n\n'
    # i = 1
    # for trace in proj.traces:
        # temp = ('Trace ' + str(i) + '\nTrace wave: ' + str(trace.wave[0])+'\n' + 'Text in: ' + str(trace.textin)+'\n' +
                # 'Text out: ' + str(trace.textout)+'\n')
        # traceSring += str(temp).replace('CWbytearray', '') + '\n'
        # i += 1

    # we can access wave, textin, etc as a whole with proj.traces
    '''
    for trace in proj.traces:
        print(trace.wave[0], trace.textin, trace.textout, trace.key)
    # can also access individually with proj.waves, proj.textins, etc.
    for wave in proj.waves:
        print(wave[0])
    '''
    #END OF FILE (EOF)
    

if __name__ == "__main__":
    basicCWTVLA(25)
