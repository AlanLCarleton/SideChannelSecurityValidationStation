import PySimpleGUI as sg
import boardSetup
import testAttacks
import time


VALID_OPTIONS = ["OPENADCCWLITEARMTINYAES128CCPA",  # OPENADC-CWLITEARM-TINYAES128C-CPA
                 "OPENADCCWLITEXMEGATINYAES128CCPA",  # OPENADC-CWLITEXMEGA-TINYAES128C-CPA
                 "OPENADCCWLITEARMTINYAES128CDPA",  # OPENADC-CWLITEARM-TINYAES128C-DPA
                 "OPENADCCWLITEXMEGATINYAES128CDPA"]  # OPENADC-CWLITEXMEGA-TINYAES128C-DPA


sg.theme('reddit')

layout = [[sg.Text('Scope Type:', font='Any 18'), sg.Combo(['OPENADC', 'CWNANO'], font='Any 12', key = 'SCOPE'),
           sg.Text('Target Platform:', font='Any 18'), sg.Combo(['CWLITEARM', 'CWLITEXMEGA', 'CWNANO'], font='Any 12', key = 'TARGET')],
          [sg.Text('Cryptography Algorithim:', font='Any 18'),
           sg.Combo(['AES128', 'DES', 'RSA'], font='Any 12', key='CRYPTO')],
          [sg.Checkbox('CPA', default=True, enable_events=True, key='cpa'),
           sg.Checkbox('DPA', enable_events=True, key='dpa')],
          [sg.Text('\nAttack Progress:', font = 'Any 12')],
          [sg.ProgressBar(1000, orientation='h',
                          size=(25, 15), key='progbar'), sg.Text(size=(30, 1), font='Any 12', key = 'status')],
          [sg.Button('Run'), sg.Button('Exit')]]

window = sg.Window('Pattern 2B', layout)

while True:  # Event Loop
    event, values = window.read()
    #print(event, values)
    if event == sg.WIN_CLOSED or event == 'Exit':  # Exit program
        break
    elif event == 'dpa': # Set 'cpa' radio button to oposite of 'dpa' (only one can be selected at a time)
        window['cpa'].update(not(values['dpa']))
    elif event == 'cpa':  # Set 'dpa' radio button to oposite of 'cpa'
        window['dpa'].update(not(values['cpa']))
    elif event == 'Run': #run attack
        Scope = values['SCOPE']
        Target = values['TARGET']
        Crypto = 'TINYAES128C' if values['CRYPTO'] == 'AES128' else values['CRYPTO']
        Type = 'CPA' if values['cpa'] else 'DPA'
        '''
        print(Scope)
        print(Target)
        print(Crypto)
        print(Type)
        '''
        if (Scope+Target+Crypto+Type) in VALID_OPTIONS: # check if user slected options are valid first
            window['status'].update(text_color = 'green')
            window['status'].update('Initiallizing boards')
            window['progbar'].update(20)
            # Intialize ChipWhisperer and Target board 
            scope = boardSetup.runInitSetup(Scope, Target, Crypto)

            if scope is not None:
                window['status'].update('Boards Initialized')
                window['progbar'].update(150)
                time.sleep(1)
                
                if Type == 'CPA':
                    window['status'].update('Running CPA Attack')
                    window['progbar'].update(350)
                    
                    attackResult = testAttacks.basicCPA(scope)
                    window['progbar'].update(1000)
                    window['status'].update('CPA Attack Complete!')

                    if attackResult is not None:
                        sg.popup(attackResult, font='Any 12')
                elif Type == 'DPA':
                    print("Insert code here")
            else:
                window['status'].update(text_color='red')
                window['status'].update('Board Initialization Failed')
        else:
            window['status'].update(text_color='red')
            window['status'].update('Selected options are not supported')

window.close()
