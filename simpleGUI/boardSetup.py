import time
import chipwhisperer as cw
import chipwhisperer.analyzer as cwa
import subprocess

SCOPETYPE = 'OPENADC'
PLATFORM = 'CWLITEXMEGA'
CRYPTO_TARGET = 'TINYAES128C'

#*********************BEGIN SETUP***********************

def subprocessCmd(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    processStdOut = process.communicate()[0].strip()
    print(processStdOut)

#***********************ONLY WORKS WITH AES128***********************
def runInitSetup(scopeType, platForm, cryptoTarget):
    #build target board firmware
    command = '-s "$platForm" "$cryptoTarget"; cd ../requiredFiles/hardware/victims/firmware/simpleserial-aes; make platForm=$1 cryptoTarget=$2'
    subprocessCmd(command)

    #Start of board setup
    try:
        if not scope.connectStatus:
            scope.con()
    except NameError:
        scope = cw.scope()

    try:
        target = cw.target(scope)
    except IOError:
        print("INFO: Caught exception on reconnecting to target - attempting to reconnect to scope first.")
        print("INFO: This is a work-around when USB has died without Python knowing. Ignore errors above this line.")
        scope = cw.scope()
        target = cw.target(scope)

    print("INFO: Found ChipWhisperer😍")

    if "STM" in platForm or platForm == "CWLITEARM" or platForm == "CWNANO":
        prog = cw.programmers.STM32FProgrammer
    elif platForm == "CW303" or platForm == "CWLITEXMEGA":
        prog = cw.programmers.XMEGAProgrammer
    else:
        prog = None

    time.sleep(0.05)
    scope.default_setup()

    #programming target
    cw.program_target(
        scope, prog, "../requiredFiles/hardware/victims/firmware/simpleserial-aes/simpleserial-aes-{}.hex".format(platForm))

    return scope

def reset_target(scope, platForm):
    if platForm == "CW303" or platForm == "CWLITEXMEGA":
        scope.io.pdic = 'low'
        time.sleep(0.1)
        scope.io.pdic = 'high_z'  # XMEGA doesn't like pdic driven high
        time.sleep(0.1)  # xmega needs more startup time
    else:
        scope.io.nrst = 'low'
        time.sleep(0.05)
        scope.io.nrst = 'high_z'
        time.sleep(0.05)
#end of board setup
