import time
import cec
import inspect

def get_int_constants(module):
    constants = {}
    for name, value in inspect.getmembers(module):
        if isinstance(value, int) and name.isupper():
            constants[name] = value
    return constants

int_constants = get_int_constants(cec)

DEVICES = {}
ALERTS = {}
DEVICE_TYPE_VALUES = {}
OPCODES = {}
EVENTS = {}

for key, value in int_constants.items():
    if key.startswith('CECDEVICE_'):
        DEVICES[value] = key[len('CECDEVICE_'):]
    elif key.startswith('CEC_ALERT'):
        ALERTS[value] = key[len('CEC_ALERT'):]
    elif key.startswith('CEC_DEVICE_TYPE_'):
        DEVICE_TYPE_VALUES[value] = key[len('CEC_DEVICE_TYPE_'):]
    elif key.startswith('CEC_OPCODE_'):
        OPCODES[value] = key[len('CEC_OPCODE_'):]
    elif key.startswith('EVENT_'):
        EVENTS[value] = key[len('EVENT_'):]

LOGLEVELS = {
    1: 'ERROR',
    2: 'WARNING',
    4: 'NOTICE',
    8: 'TRAFFIC',
    16: 'DEBUG',
    31: 'ALL'
}

#https://github.com/simons-public/cecdaemon/blob/master/cecdaemon/const.py
#https://storage.googleapis.com/google-code-archive-downloads/v2/code.google.com/xtreamerdev/CEC_Specs.pdf


def printCommand(command):
    print(
        f'COMMAND {{'
        f'initiator: {DEVICES.get(command["initiator"], command["initiator"])}, '
        f'destination: {DEVICES.get(command["destination"], command["destination"])}, '
        f'ack: {command["ack"]}, '
        f'opcode: {OPCODES.get(command["opcode"], command["opcode"])}, '
        f'parameters: {command["parameters"]}, '
        f'opcode_set: {command["opcode_set"]}, '
        f'transmit_timeout: {command["transmit_timeout"]}'
        f'}}'
    )
    sys.stdout.flush()


LOGLEVEL = 31
def printLog(argv):
    level, time, msg = argv
    if level <= LOGLEVEL:
        print(
            f'LOG {{'
            f'level: {LOGLEVELS.get(level, level)}, '
            f'time: {time}, '
            f'msg: {msg} '
            f'}}'
        )
    sys.stdout.flush()

# Replace as necessary with your own HA entity and services for volume
def volume_up():
    pass
def volume_down():
    pass
def volume_mute():
    pass

def callback(event, *argv):
    if event == cec.EVENT_COMMAND:
        command = argv[0]
        printCommand(command)
        if command['opcode'] == cec.CEC_OPCODE_REQUEST_ARC_START:
            print("Reporting ARC started")
            cec.transmit(cec.CECDEVICE_TV, cec.CEC_OPCODE_REPORT_ARC_STARTED, '', cec.CECDEVICE_AUDIOSYSTEM)
    elif event == cec.EVENT_KEYPRESS:
        code, duration = argv
        print("keypress", code, duration)
        if code == 65 and duration == 0:
            volume_up()
            print("volume up")
        elif code == 66 and duration == 0:
            volume_down()
            print("volume down")
        elif code == 67 and duration == 0:
            volume_mute()            
            print("mute")
    elif event == cec.EVENT_LOG:
        printLog(argv)
    else:
        print("event: ", event, "argv: ", argv)


#cec.add_callback(callback, cec.EVENT_ALL & ~cec.EVENT_LOG)
cec.add_callback(callback, cec.EVENT_ALL)
cec.init()
print("initilized")


# Sleep forever (CEC stuff will run in the background)
while True:
    time.sleep(100)
