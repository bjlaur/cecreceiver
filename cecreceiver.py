import os

CEC_DEVICE_TYPE_AUDIO_SYSTEM = 5

os.environ["PYTHONCEC_DEVICE_NAME"] = "rpi3"
os.environ["PYTHONCEC_DEVICE_TYPE"] = str(CEC_DEVICE_TYPE_AUDIO_SYSTEM)

import sys
from loguru import logger
logger.add("output.log", rotation="500 MB", level="INFO", colorize=True)  # Add a file handler
logger.add(sys.stdout, level="INFO", colorize=True)  # Add a stdout handler
logger.level("COMMAND", no=21, color="<yellow>")
logger.level("NOTICE", no=19, color="<green>")
logger.level("TRAFFIC", no=15, color="<cyan>")

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
    logger.log("COMMAND",
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


def printLog(argv):
    level, time, msg = argv
    logger.log(LOGLEVELS[level],
            f'LOG {{'
            f'level: {LOGLEVELS.get(level, level)}, '
            f'time: {time}, '
            f'msg: {msg} '
            f'}}'
        )

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
            logger.success('Reporting ARC Started')
            cec.transmit(cec.CECDEVICE_TV, cec.CEC_OPCODE_REPORT_ARC_STARTED, '', cec.CECDEVICE_AUDIOSYSTEM)
    elif event == cec.EVENT_KEYPRESS:
        code, duration = argv
        logger.info("keypress", code, duration)
        if code == 65 and duration == 0:
            volume_up()
            logger.info("volume up")
        elif code == 66 and duration == 0:
            volume_down()
            logger.info("volume down")
        elif code == 67 and duration == 0:
            volume_mute()            
            logger.info("mute")
    elif event == cec.EVENT_LOG:
        printLog(argv)
    else:
        logger.warning("uncategorized event", "event: ", event, "argv: ", argv)


cec.add_callback(callback, cec.EVENT_ALL)
cec.init()
logger.success("initilized")


# Sleep forever (CEC stuff will run in the background)
while True:
    time.sleep(100)
