import PySimpleGUI as sg
import boardSetup
import testAttacks

sg.theme('reddit')

layout = [#[sg.Text('TEST TEXT INPUT:', font='Any 15'), sg.Text(size = (15, 1), key = '-OUTPUT-')],
          #[sg.Input(key='-IN1-', font = 'Any 12')],
          [sg.Text('Scope Type:', font='Any 18'), sg.Combo(['OPENADC', 'CWNANO'], font='Any 12', key = 'SCOPE'),
           sg.Text('Target Platform:', font='Any 18'), sg.Combo(['CWLITEARM', 'CWLITEXMEGA', 'CWNANO'], font='Any 12', key = 'TARGET')],
          [sg.Text('Cryptography Algorithim:', font='Any 18'),
           sg.Combo(['TINYAES128C', 'DES', 'RSA'], font='Any 12', key='CRYPTO')],
          [sg.Text('\nAttack Progress:', font = 'Any 12')],
          [sg.ProgressBar(1000, orientation='h',
                          size=(25, 15), key='progbar')],
          #sg.Button('Show'),
          [sg.Button('Run'), sg.Button('Exit')]]

window = sg.Window('Pattern 2B', layout)

while True:  # Event Loop
    event, values = window.read()
    print(event, values)
    if event == sg.WIN_CLOSED or event == 'Exit':
        break
    #if event == 'Show':
        # Update the "output" text element to be the value of "input" element
        #window['-OUTPUT-'].update(values['-IN1-'])
    if event == 'Run':
        Scope = values['SCOPE']
        Target = values['TARGET']
        Crypto = values['CRYPTO']
        print(Scope)
        print(Target)
        print(Crypto)

        scope = boardSetup.runInitSetup(Scope, Target, Crypto)
        window['progbar'].update(250)
        attackResult = testAttacks.basicCPA(scope)
        window['progbar'].update(1000)
        if attackResult is not None:
            sg.popup(attackResult, font='Any 12')

window.close()
