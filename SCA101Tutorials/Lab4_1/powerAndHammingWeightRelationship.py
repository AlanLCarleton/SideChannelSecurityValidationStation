from bokeh.palettes import brewer
#from bokeh.io import output_notebook
from bokeh.plotting import figure, show
import matplotlib.pylab as plt
import time
import numpy as np
from tqdm import tnrange
import chipwhisperer as cw
import subprocess

SCOPETYPE = 'OPENADC'
PLATFORM = 'CWLITEXMEGA'
CRYPTO_TARGET = 'TINYAES128C'

#*********************BEGIN SETUP***********************
def subprocessCmd(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    processStdOut = process.communicate()[0].strip()
    print(processStdOut)

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
#*********************SETUP COMPLETED***********************

#capturing some traces
ktp = cw.ktp.Basic()
trace_array = []
textin_array = []

key, text = ktp.next()

target.simpleserial_write('k', key)

N = 1000
for i in tnrange(N, desc='Capturing traces'):
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
target.dis()

plt.figure(1)
plt.plot(trace_array[0], 'r')
plt.plot(trace_array[1], 'g')
plt.show()

numtraces = np.shape(trace_array)[0]  # total number of traces
numpoints = np.shape(trace_array)[1]  # samples per trace

#AES Model
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

#Simple test vectors - if you get the check-mark printed all OK.
assert(aes_internal(0xAB, 0xEF) == 0x1B)
assert(aes_internal(0x22, 0x01) == 0x26)
print("✔️ OK to continue!")


#**************************Haming Weight***************************
def calc_hamming_weight(n):
    return bin(n).count("1")

HW = [bin(n).count("1") for n in range(0, 256)]

assert HW[0x53] == 4
print("✔️ OK to continue!")

#output_notebook()
p = figure()

plot_start = 0
plot_end = 2000
xrange = range(len(trace_array[0]))[plot_start:plot_end]
bnum = 0
color_mapper = brewer['PRGn'][9]

for tnum in range(len(trace_array)):
    hw_of_byte = HW[aes_internal(textin_array[tnum][bnum], key[bnum])]
    p.line(xrange, trace_array[tnum][plot_start:plot_end],
           line_color=color_mapper[hw_of_byte])

show(p)

p = figure()

hw_groups = [[], [], [], [], [], [], [], [], []]
for tnum in range(len(trace_array)):
    hw_of_byte = HW[aes_internal(textin_array[tnum][bnum], key[bnum])]
    hw_groups[hw_of_byte].append(trace_array[tnum])
hw_averages = np.array([np.average(hw_groups[hw], axis=0) for hw in range(9)])
avg_trace = np.average(hw_averages, axis=0)

xrange = range(len(trace_array[0]))[plot_start:plot_end]
color_mapper = brewer['PRGn'][9]
for hw in range(9):
    p.line(xrange, (hw_averages[hw]-avg_trace)
           [plot_start:plot_end], line_color=color_mapper[hw])

show(p)

sbox_loc = np.argmax(abs(hw_averages[0]-avg_trace))

p = figure(title="HW vs Voltage Measurement")
p.line(range(0, 9), hw_averages[:, sbox_loc], line_color="red")
p.xaxis.axis_label = "Hamming Weight of Intermediate Value"
p.yaxis.axis_label = "Average Value of Measurement"
show(p)