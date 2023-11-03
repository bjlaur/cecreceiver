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

from time import sleep
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

#could ask python-cec to expose these?

CEC_POWER_STATUS_ON = 0
CEC_POWER_STATUS_STANDBY = 1
CEC_POWER_STATUS_IN_TRANSITION_STANDBY_TO_ON = 2
CEC_POWER_STATUS_IN_TRANSITION_ON_TO_STANDBY = 3

POWER_STATUSES = {
    CEC_POWER_STATUS_ON: 'CEC_POWER_STATUS_ON',
    CEC_POWER_STATUS_STANDBY: 'CEC_POWER_STATUS_STANDBY',
    CEC_POWER_STATUS_IN_TRANSITION_STANDBY_TO_ON: 'CEC_POWER_STATUS_IN_TRANSITION_STANDBY_TO_ON',
    CEC_POWER_STATUS_IN_TRANSITION_ON_TO_STANDBY: 'CEC_POWER_STATUS_IN_TRANSITION_ON_TO_STANDBY'
    #,CEC_POWER_STATUS_UNKNOWN: 'CEC_POWER_STATUS_UNKNOWN'
}



#https://github.com/simons-public/cecdaemon/blob/master/cecdaemon/const.py
#https://storage.googleapis.com/google-code-archive-downloads/v2/code.google.com/xtreamerdev/CEC_Specs.pdf
#https://searchcode.com/total-file/93523780/
#https://forums.parallax.com/discussion/download/128730/Hdmi-1.4-1000008562-6364143185282736974850538.pdf


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

ffff_re = re.compile(r'^.*CEC_DQEVENT.*CEC_EVENT_STATE_CHANGE.*phys_addr=ffff.*$')
ffff = False

def callback(event, *argv):
    try: #need try otherwise the errors will get swalloed up by python-cec
        global ffff
        if event == cec.EVENT_COMMAND:
            command = argv[0]
            printCommand(command)
            if command['opcode'] == cec.CEC_OPCODE_REQUEST_ARC_START:
                logger.success('Request ARC Start')
                if ffff:
                    logger.info('Request ARC Start while in ffff...')
                    #always respond with this so that the TV doesn't switch to speakers.
                    cec.transmit(cec.CECDEVICE_TV, cec.CEC_OPCODE_START_ARC, '', cec.CECDEVICE_AUDIOSYSTEM)
                    #don't send the GIVE_DEVICE_POWER_STATUS thing because the ffff fuction will do that for us.
                    #although I am not 100% if we can't actually just send it anyways in which case we don't need this ffff variable.
                    cec.transmit(cec.CECDEVICE_TV, cec.CEC_OPCODE_GIVE_DEVICE_POWER_STATUS, '', cec.CECDEVICE_AUDIOSYSTEM)

                else:
                    logger.info('Request ARC start while not in ffff... responding with.....')
                    #always respond with this so that the TV doesn't switch to speakers.
                    cec.transmit(cec.CECDEVICE_TV, cec.CEC_OPCODE_START_ARC, '', cec.CECDEVICE_AUDIOSYSTEM)
                    #are we sure if the tv is actually on at this point? lets double check.
                    cec.transmit(cec.CECDEVICE_TV, cec.CEC_OPCODE_GIVE_DEVICE_POWER_STATUS, '', cec.CECDEVICE_AUDIOSYSTEM)


            if command['opcode'] == cec.CEC_OPCODE_STANDBY and command['destination'] == cec.CECDEVICE_BROADCAST:
                #A device has requested all go to standby.
                logger.info("STANDBY Broadcast sent by " + DEVICES.get(command["initiator"], command["initiator"]))
                actions.tv_off()

            if command['opcode'] == cec.CEC_OPCODE_REPORT_POWER_STATUS and command['initiator'] == cec.CECDEVICE_TV:
                power_status = int.from_bytes(command['parameters'])
                logger.info(f'TV Report Power Status: {POWER_STATUSES.get(power_status, power_status)}')

                if power_status == CEC_POWER_STATUS_ON or power_status == CEC_POWER_STATUS_IN_TRANSITION_STANDBY_TO_ON:
                    #if we get this the tv is absolutely on.
                    logger.info('TV Report Power: TV ON or turning ON')
                    actions.tv_on()
                    #just in case we missed it due to an ffff event.
                    cec.transmit(cec.CECDEVICE_TV, cec.CEC_OPCODE_START_ARC, '', cec.CECDEVICE_AUDIOSYSTEM)

                else:
                    logger.info('TV Report Power: TV OFF or turning OFF')

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
                #does this need to be adjusted? not during fffff or anything?
                actions.tv_on()

            if ffff_re.match(msg):
                logger.warning('ffff - detected.')
                ffff = True
            if msg == "CLinuxCECAdapterCommunication::Process - CEC_DQEVENT - CEC_EVENT_STATE_CHANGE - log_addr_mask=0020 phys_addr=3000":
                logger.info('3000 - detected.')
                if ffff:
                    logger.warning('3000 - detected w/ ffff')
                    logger.info('sleeping 3 seconds for good measure.')
                    sleep(3)
                    cec.transmit(cec.CECDEVICE_TV, cec.CEC_OPCODE_GIVE_DEVICE_POWER_STATUS, '', cec.CECDEVICE_AUDIOSYSTEM)
                    ffff = False
        else:
            logger.warning(f'uncategorized event. event: {event}, argv: {argv}')
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        logger.exception(e)


cec.add_callback(callback, cec.EVENT_ALL)
cec.init()
#seems like python-cec does this automatically, so we don't need it.
#cec.transmit(cec.CECDEVICE_TV, cec.CEC_OPCODE_GIVE_DEVICE_POWER_STATUS, '', cec.CECDEVICE_AUDIOSYSTEM)
logger.success("initilized")
