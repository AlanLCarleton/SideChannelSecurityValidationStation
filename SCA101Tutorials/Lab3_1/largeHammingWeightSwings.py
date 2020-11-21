import matplotlib.pyplot as plt
from tqdm import tnrange
import numpy as np
import chipwhisperer as cw
import time
import subprocess

SCOPETYPE = 'OPENADC'
PLATFORM = 'CWLITEXMEGA'
CRYPTO_TARGET='TINYAES128C' 


#*********************BEGIN SETUP***********************
def subprocessCmd(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    processStdOut = process.communicate()[0].strip()
    print (processStdOut)

#build target board firmware
command = '-s "$PLATFORM" "$CRYPTO_TARGET"; cd ../../requiredFiles/hardware/victims/firmware/simpleserial-aes; make PLATFORM=$1 CRYPTO_TARGET=$2'
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
#end of board setup

#programming target
cw.program_target(
    scope, prog, "../../requiredFiles/hardware/victims/firmware/simpleserial-aes/simpleserial-aes-{}.hex".format(PLATFORM))

#capturing some traces
ktp = cw.ktp.Basic()
trace_array = []
textin_array = []

key, text = ktp.next()

target.simpleserial_write('k', key)

N = 100
for i in tnrange(N, desc='Capturing traces'):
    scope.arm()
    if text[0] & 0x01:
        text[0] = 0xFF
    else:
        text[0] = 0x00
    target.simpleserial_write('p', text)

    ret = scope.capture()
    if ret:
        print("Target timed out!")
        continue

    response = target.simpleserial_read('r', 16)

    trace_array.append(scope.get_last_trace())
    textin_array.append(text)

    key, text = ktp.next()
#*********************SETUP COMPLETED***********************

#basic sanity check
assert len(trace_array) == 100
print("✔️ OK to continue!")


#*********************Grouping Traces**********************
for i in range(len(trace_array)):
    if textin_array[i][0] == 0x00:
        print("This should be added to 1 list")
    else:
        print("This should be added to 0 list")

one_list = []
zero_list = []

for i in range(len(trace_array)):
    if textin_array[i][0] == 0x00:
        one_list.append(trace_array[i])
    else:
        zero_list.append(trace_array[i])

assert len(one_list) > len(zero_list)/2
assert len(zero_list) > len(one_list)/2

trace_length = len(one_list[0])
print("Traces had original sample length of %d" % trace_length)

one_avg = np.mean(one_list, axis=0)
zero_avg = np.mean(zero_list, axis=0)

if len(one_avg) != trace_length:
    raise ValueError(
        "Average length is only %d - check you did correct dimensions!" % one_avg)

diff = one_avg - zero_avg

plt.figure(1)
plt.plot(diff)
plt.show()
#*********************End Grouping Traces**********************
