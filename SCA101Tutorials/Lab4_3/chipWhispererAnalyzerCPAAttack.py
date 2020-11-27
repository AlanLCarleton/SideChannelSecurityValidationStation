import holoviews as hv
from holoviews.operation import decimate
from holoviews.operation.datashader import datashade, shade, dynspread, rasterize
from IPython.display import clear_output
from IPython.display import display
import pandas as pd
import matplotlib.pylab as plt
import time
import numpy as np
from tqdm import tnrange
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

#build target board firmware
command = '-s "$PLATFORM" "$CRYPTO_TARGET"; cd ../../requiredFiles/hardware/victims/firmware/simpleserial-aes; make PLATFORM=$1 CRYPTO_TARGET=$2'
subprocessCmd(command)

#create project
proj = cw.create_project("Lab 4_3", overwrite=True)

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

proj = cw.create_project("Lab 4_3", overwrite=True)

N = 50
for i in tnrange(N, desc='Capturing traces'):
    key, text = ktp.next()
    trace = cw.capture_trace(scope, target, text, key)
    if not trace:
        continue

    proj.traces.append(trace)

scope.dis()
target.dis()

# we can access wave, textin, etc as a whole with proj.traces
for trace in proj.traces:
    print(trace.wave[0], trace.textin, trace.textout, trace.key)

# can also access individually with proj.waves, proj.textins, etc.
for wave in proj.waves:
    print(wave[0])


#************************ChipWhisperer Analyzer*******************
leak_model = cwa.leakage_models.sbox_output
attack = cwa.cpa(proj, leak_model)
print(attack)

results = attack.run()
print(results)
"""
stat_data = results.find_maximums()
df = pd.DataFrame(stat_data).transpose()
#nicely displaying with "point location of the max"
key = proj.keys[0]

def format_stat(stat):
    return str("{:02X}<br>{:.3f}".format(stat[0], stat[2]))

def color_corr_key(row):
    global key
    ret = [""] * 16
    for i, bnum in enumerate(row):
        if bnum[0] == key[i]:
            ret[i] = "color: red"
        else:
            ret[i] = ""
    return ret

df.head().style.format(format_stat).apply(color_corr_key, axis=1)
#************************End ChipWhisperer Analyzer*******************

#*********************Reporting Intervals (Live Updates during Attack)**************************
def stats_callback():
    results = attack.results
    results.set_known_key(key)
    stat_data = results.find_maximums()
    df = pd.DataFrame(stat_data).transpose()
    clear_output(wait=True)
    display(df.head().style.format(format_stat).apply(color_corr_key, axis=1))

results = attack.run(stats_callback, 10)
#*********************End Reporting Intervals (Live Updates during Attack)**************************

#***********************Plot Data*************************
plot_data = cwa.analyzer_plots(results)

def byte_to_color(idx):
    return hv.Palette.colormaps['Category20'](idx/16.0)

a = []
b = []
hv.extension('bokeh')
for i in range(0, 16):
    data = plot_data.output_vs_time(i)
    a.append(np.array(data[1]))
    b.append(np.array(data[2]))
    b.append(np.array(data[3]))

pda = pd.DataFrame(a).transpose().rename(str, axis='columns')
pdb = pd.DataFrame(b).transpose().rename(str, axis='columns')
curve = hv.Curve(pdb['0'], "Sample").options(color='black')
for i in range(1, 16):
    curve *= hv.Curve(pdb[str(i)]).options(color='black')

for i in range(0, 16):
    curve *= hv.Curve(pda[str(i)]).options(color=byte_to_color(i))
decimate(curve.opts(width=900, height=600))
#***********************End Plot Data*************************

#*************************PGE vs. Trace*************************
#Plot of partial guessing entropy vs. the number of traces. PGE is just how many spots away from the top the actual subkey is in our table of guesses
#For example, if there are 7 subkey guesses that have a higher correlation than the actual subkey, the subkey has a PGE of 7
#Useful for seeing how many traces were needed to actually break the AES implementation
ret = plot_data.pge_vs_trace(0)
curve = hv.Curve((ret[0], ret[1]), "Traces Used in Calculation",
                 "Partial Guessing Entrop of Byte")
for bnum in range(1, 16):
    ret = plot_data.pge_vs_trace(bnum)
    curve *= hv.Curve((ret[0], ret[1])).opts(color=byte_to_color(bnum))
curve.opts(width=900, height=600)
#*************************End PGE vs. Trace*************************

#**********************Correlation vs. Traces************************
a = []
b = []
for bnum in range(0, 16):
    data = plot_data.corr_vs_trace(bnum)
    best = [0] * len(data[1][0])
    for i in range(256):
        if i == key[bnum]:
            a.append(np.array(data[1][i]))
        else:
            if max(best) < max(data[1][i]):
                best = data[1][i]
    b.append(np.array(best))

pda = pd.DataFrame(a).transpose().rename(str, axis='columns')
pdb = pd.DataFrame(b).transpose().rename(str, axis='columns')
curve = hv.Curve(pdb['0'].tolist(), "Iteration Number",
                 "Max Correlation").options(color='black')
for i in range(1, len(pdb.columns)):
    curve *= hv.Curve(pdb[str(i)]).options(color='black')

for i in range(len(pda.columns)):
    curve *= hv.Curve(pda[str(i)]).options(color=byte_to_color(i))

curve.opts(width=900, height=600)
"""