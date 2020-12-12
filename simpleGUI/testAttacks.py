import chipwhisperer as cw
import chipwhisperer.analyzer as cwa
import guiUtils as utils
import time

def basicCPA(scope, traceAmount):
    target = cw.target(scope)
    
    #capturing some traces
    ktp = cw.ktp.Basic()
    trace_array = []
    textin_array = []

    proj = cw.create_project("Lab 4_3", overwrite=True)

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
    #utils.plotTraces(proj.waves)

    traceSring = 'Trace key: ' + str(trace.key).replace('CWbytearray', '') + '\n\n'
    i = 1
    for trace in proj.traces:
        temp = ('Trace ' + str(i) + '\nTrace wave: ' + str(trace.wave[0])+'\n' + 'Text in: ' + str(trace.textin)+'\n' +
                'Text out: ' + str(trace.textout)+'\n')
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
    return(str(results), round(time2-time1, 3), traceSring)
