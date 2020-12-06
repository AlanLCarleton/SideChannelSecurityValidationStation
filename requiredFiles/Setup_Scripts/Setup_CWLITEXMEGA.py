import time
import chipwhisperer as cw
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

prog = cw.programmers.XMEGAProgrammer

time.sleep(0.05)
scope.default_setup()


def reset_target(scope):
    scope.io.pdic = 'low'
    time.sleep(0.1)
    scope.io.pdic = 'high_z'  # XMEGA doesn't like pdic driven high
    time.sleep(0.1)  # xmega needs more startup time
