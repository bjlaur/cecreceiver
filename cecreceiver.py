import os

CEC_DEVICE_TYPE_AUDIO_SYSTEM = 5

os.environ["PYTHONCEC_DEVICE_NAME"] = "rpi3"
os.environ["PYTHONCEC_DEVICE_TYPE"] = str(CEC_DEVICE_TYPE_AUDIO_SYSTEM)

import sys
from loguru import logger
logger.remove()
logger.add("output.log", rotation="500 MB", level="DEBUG") 
logger.add(sys.stdout, level="INFO", colorize=True) 
logger.level("COMMAND", no=21, color="<yellow>")
logger.level("NOTICE", no=19, color="<green>")
logger.level("TRAFFIC", no=15, color="<cyan>")
logger.success("Logging initilized.")

import time
import cec
import actions
import inspect
import re

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
    if key.startswith('CECDEVICE_') and key != 'CECDEVICE_UNREGISTERED':
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

opcode_re = re.compile(r'opcode=([a-fA-F0-9]+)')

def printLog(argv):
    level, time, msg = argv
    matches = opcode_re.findall(msg)

    # Check if matches is non-empty before accessing its elements
    opcode = int(matches[0], 16) if matches else None

    logger.log(LOGLEVELS.get(level, level),
               f'LOG {{'
               f'level: {LOGLEVELS.get(level, level)}, '
               f'time: {time}, '
               f'msg: {{{msg}}}' +
               (f', opcode: {OPCODES.get(opcode, opcode)}' if opcode is not None and opcode in OPCODES else '') + 
               f'}}'
    )



def callback(event, *argv):
    try:
        if event == cec.EVENT_COMMAND:
            command = argv[0]
            printCommand(command)
            if command['opcode'] == cec.CEC_OPCODE_REQUEST_ARC_START:
                logger.success('Reporting ARC Started')
                cec.transmit(cec.CECDEVICE_TV, cec.CEC_OPCODE_REPORT_ARC_STARTED, '', cec.CECDEVICE_AUDIOSYSTEM)
                actions.tv_on()
            if command['opcode'] == cec.CEC_OPCODE_STANDBY and command['destination'] == cec.CECDEVICE_BROADCAST:
                #A device has requested all go to standby.
                logger.info("STANDBY Broadcast sent by " + DEVICES.get(command["initiator"], command["initiator"]))
                actions.tv_off()

        elif event == cec.EVENT_KEYPRESS:
            code, duration = argv
            logger.info(f'keypress {code} {duration}')
            if code == 65 and duration == 0:
                actions.volume_up()
            elif code == 66 and duration == 0:
                actions.volume_down()
            elif code == 67 and duration == 0:
                actions.volume_mute()            
        elif event == cec.EVENT_LOG:
            printLog(argv)
            level, time, msg = argv
            if msg == "TV (0): power status changed from 'standby' to 'in transition from standby to on'":
                actions.tv_on()
        else:
            logger.warning(f'uncategorized event. event: {event}, argv: {argv}')
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        logger.exception(e)


cec.add_callback(callback, cec.EVENT_ALL)
cec.init()
logger.success("initilized")


# Sleep forever (CEC stuff will run in the background)
while True:
    time.sleep(100)
