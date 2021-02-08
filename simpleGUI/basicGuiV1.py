import PySimpleGUI as sg
import boardSetup
import testAttacks
import guiUtils as utils
import time


VALID_OPTIONS = ["OPENADCCWLITEARMTINYAES128CCPA",  # OPENADC-CWLITEARM-TINYAES128C-CPA
                 "OPENADCCWLITEXMEGATINYAES128CCPA",  # OPENADC-CWLITEXMEGA-TINYAES128C-CPA
                 "OPENADCCWLITEARMTINYAES128CDPA",  # OPENADC-CWLITEARM-TINYAES128C-DPA
                 "OPENADCCWLITEXMEGATINYAES128CDPA",  # OPENADC-CWLITEXMEGA-TINYAES128C-DPA
                 "OPENADCCWLITEARMTINYAES128CTVLA",  # OPENADC-CWLITEARM-TINYAES128C-TVLA
                 "OPENADCCWLITEXMEGATINYAES128CTVLA",  # OPENADC-CWLITEXMEGA-TINYAES128C-TVLA
                 "OPENADCCWLITEARMAVRCRYPTOLIBTVLA",  # OPENADC-CWLITEARM-AVRCRYPTOLIB-TVLA
                 "OPENADCCWLITEXMEGAAVRCRYPTOLIBTVLA"]  # OPENADC-CWLITEXMEGA-TINYAES128C-TVLA
MAXTRACES = 100

sg.theme('reddit')

layout = [[sg.Text('Scope Type:', font='Any 18'), sg.Combo(['OPENADC', 'CWNANO'], font='Any 12', key = 'SCOPE'),
           sg.Text('Target Platform:', font='Any 18'), sg.Combo(['CWLITEARM', 'CWLITEXMEGA', 'CWNANO'], font='Any 12', key = 'TARGET')],
          [sg.Text('Cryptography Algorithim:', font='Any 18'),
           sg.Combo(['AES128', 'DES', 'RSA'], font='Any 12', key='CRYPTO')],
          [sg.Checkbox('CPA', default=True, enable_events=True, disabled=True, key='cpa'),
           sg.Checkbox('DPA', enable_events=True, key='dpa'),
           sg.Checkbox('TVLA', enable_events=True, key='tvla')],
          [sg.Text('Initial Number of Traces:'), sg.InputText(key='TRACENUMBER', default_text='15', size=(9, 2)), sg.Text(
              'Trace Increment Amount:'), sg.InputText(key='TRACEINCREMENT', default_text='2', size=(9, 2))],
          [sg.Text('\nAttack Progress:', font = 'Any 12')],
          [sg.ProgressBar(1000, orientation='h',
                          size=(25, 15), key='progbar'), sg.Text(size=(30, 1), font='Any 12', key = 'status')],
          [sg.Button('Run'), sg.Button('View Trace'), sg.Button('Exit')]]

window = sg.Window('Power Analysis Security Tool', layout)
traceData = None

while True:  # Event Loop
    event, values = window.read()
    #print(event, values)
    if event == sg.WIN_CLOSED or event == 'Exit':  # Exit program
        break
    elif event == 'dpa': # Set 'cpa' and 'tvla' radio button to oposite of 'dpa' (only one can be selected at a time)
        window['cpa'].update(disabled=False)
        window['cpa'].update(not(values['dpa']))
        window['tvla'].update(disabled=False)
        window['tvla'].update(not(values['dpa']))
        window['dpa'].update(disabled=True)
        window['TRACENUMBER'].update(2000)
        window['TRACEINCREMENT'].update(0)
        MAXTRACES = 3000
    elif event == 'cpa':  # Set 'dpa' radio button to oposite of 'cpa'
        window['dpa'].update(disabled=False)
        window['dpa'].update(not(values['cpa']))
        window['tvla'].update(disabled=False)
        window['tvla'].update(not(values['cpa']))
        window['cpa'].update(disabled=True)
    elif event == 'tvla':  # Set 'dpa' radio button to oposite of 'cpa'
        window['cpa'].update(disabled=False)
        window['cpa'].update(not(values['tvla']))
        window['dpa'].update(disabled=False)
        window['dpa'].update(not(values['tvla']))
        window['tvla'].update(disabled=True)
        window['TRACENUMBER'].update(25)
        window['TRACEINCREMENT'].update(0)
    elif event == 'Run': #run attack
        Scope = values['SCOPE']
        Target = values['TARGET']
        Crypto = ''
        if values['CRYPTO'] == 'AES128':
            Crypto = 'TINYAES128C'
        elif values['CRYPTO'] == 'DES':
            Crypto = 'AVRCRYPTOLIB'
        else:
            Crypto = values['CRYPTO']
        Type = ''
        if values['cpa']:
            Type = 'CPA'
        elif values['dpa']:
            Type = 'DPA'
        else: Type = 'TVLA'
        '''
        print(Scope)
        print(Target)
        print(Crypto)
        print(Type)
        '''
        traceAmount = None
        traceIncrement = None
        try:
            traceAmount = int(values['TRACENUMBER'])
            traceIncrement = int(values['TRACEINCREMENT'])
        except:
            print("Entered value for Number of Traces or Increment must be a number")

        boardInitialized = True
        # check if user slected options are valid first
        if (Scope+Target+Crypto+Type) in VALID_OPTIONS and traceAmount is not None and traceIncrement is not None:
            window['status'].update(text_color = 'green')
            window['status'].update('Initiallizing boards')
            window['progbar'].update(20)

            attackTime = 0
            cpaAttackResult = None
            dpaAttackResult = None
            tvlaResults = None
            sucess = False
            while not sucess and traceAmount <= MAXTRACES and boardInitialized:
                # Intialize ChipWhisperer and Target board 
                scope = boardSetup.runInitSetup(Scope, Target, Crypto)
                boardInitialized = scope is not None

                if boardInitialized:
                    window['status'].update('Boards Initialized')
                    window['progbar'].update(150)
                    time.sleep(1)
                    
                    if Type == 'CPA':
                        window['status'].update('Running CPA Attack')
                        window['progbar'].update(350)

                        cpaAttackResult, attackTime, traceData = testAttacks.basicCPA(
                            scope, traceAmount)
                        window['progbar'].update(1000)
                        window['status'].update('CPA Attack Complete!')
                        #wtite results to CSV
                        utils.writeResultsToCSV(cpaAttackResult)
                        if not(utils.checkZeroCorrelation()):
                            sucess = True

                    elif Type == 'DPA':
                        window['status'].update('Running DPA Attack')
                        window['progbar'].update(350)
                        dpaAttackResult = testAttacks.basicCWDPA(
                            scope, traceAmount)
                        window['progbar'].update(1000)
                        window['status'].update('CPA Attack Complete!')
                        #wtite results to CSV
                        #utils.writeResultsToCSV(dpaAttackResult)
                        sucess = True

                    # ROUGH IMPLEMENTATION OF TVLA
                    #STILL NEED TO INCORPORATE THE INCREMENTAL FEATURE
                    elif Type == 'TVLA':
                        window['status'].update(
                            'Running TVLA T-test on ' + values['CRYPTO'])
                        window['progbar'].update(350)

                        tvlaResults, resultStr = testAttacks.basicCWTVLA(
                            scope, Crypto, traceAmount)
                        window['progbar'].update(1000)
                        window['status'].update('TLVA Complete!')
                        #wtite results to CSV
                        #utils.writeResultsToCSV(tvlaResults)
                        sucess = True
                else:
                    boardInitialized = False
                
                traceAmount += traceIncrement
            
            if not(boardInitialized):
                window['status'].update(text_color='red')
                window['status'].update('Board Initialization Failed')
            else:
                if cpaAttackResult is not None:
                    window['progbar'].update(1000)
                    window['status'].update('CPA Attack Complete!')
                    resultPrint = cpaAttackResult + "\nSucessful attack required: " + \
                        str(traceAmount - traceIncrement) + \
                        " traces\nand took: " + str(attackTime) + " seconds"
                    sg.popup(resultPrint, font='Any 12')
                    cpaAttackResult = None
                elif dpaAttackResult is not None:
                    window['progbar'].update(1000)
                    window['status'].update('DPA Attack Complete!')
                    #resultPrint = dpaAttackResult + "\nSucessful attack required: " + \
                    #    str(traceAmount - traceIncrement) + \
                    #    " traces\nand took: " + str(attackTime) + " seconds"
                    sg.popup(dpaAttackResult, font='Any 12')
                    dpaAttackResult = None
                elif tvlaResults is not None:
                    window['progbar'].update(1000)
                    window['status'].update('TVLA Test Complete!')
                    sg.popup(resultStr, font='Any 12')
                    tvlaResults = None
                else:
                    window['status'].update(text_color='red')
                    msgStr = 'Encryption tested with ' + str(MAXTRACES) + ' traces without recoering the key'
                    window['status'].update(msgStr)
        else:
            window['status'].update(text_color='red')
            window['status'].update('Selected options are not supported')
    elif event == 'View Trace':  # view raw trace data
        if traceData is not None:
            sg.popup_scrolled(traceData, font='10')
        else:
            window['status'].update(text_color='red')
            window['status'].update('No traces found! Please run program first')

window.close()
