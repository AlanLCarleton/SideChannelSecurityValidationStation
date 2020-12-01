import chipwhisperer as cw
import chipwhisperer.analyzer as cwa
import guiUtils as utils
import time

def basicCPA(scope):
    target = cw.target(scope)
    
    #capturing some traces
    ktp = cw.ktp.Basic()
    trace_array = []
    textin_array = []

    proj = cw.create_project("Lab 4_3", overwrite=True)

    N = 50
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
    return(str(results) + '\n\nAttack took: ' + str(round(time2-time1, 3)) + 'secs.')
