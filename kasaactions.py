from loguru import logger
import traceback
import kasa
import asyncio
import threading

import sys
from time import sleep

def _start_async():
    loop = asyncio.new_event_loop()
    threading.Thread(target=loop.run_forever).start()
    return loop

_loop = _start_async()

# Submits awaitable to the event loop, but *doesn't* wait for it to
# complete. Returns a concurrent.futures.Future which *may* be used to
# wait for and retrieve the result (or exception, if one was raised)
def submit_async(awaitable):
    return asyncio.run_coroutine_threadsafe(awaitable, _loop)

def stop_async():
    _loop.call_soon_threadsafe(_loop.stop())


kasa_devices = {}

async def findKasaDevices():
    searchTimeout = 5
    found_devices = await kasa.Discover.discover(timeout=searchTimeout)
    for devStr in found_devices:
        dev = await kasa.Discover.discover_single(devStr)
        logger.info("KASA - Found device " + dev.alias)
        kasa_devices[dev.alias] =  dev

async def turnoff_async(devalias):
    logger.debug("turnoff_async: " + devalias)
    try:
        await kasa_devices[devalias].turn_off()
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        logger.exception(e)

async def turnon_async(devalias):
    logger.debug("turnon_async: " + devalias)
    try:
        await kasa_devices[devalias].turn_on()
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        logger.exception(e)

async def update_async(devalias):
    logger.debug("update_async: " + devalias)
    try:
        await kasa_devices[devalias].update()
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        logger.exception(e)



def turnoff(devalias):
    return submit_async(turnoff_async(devalias))

def turnon(devalias):
    return submit_async(turnon_async(devalias))

def update(devalias):
    return submit_async(update_async(devalias)) 


_future = submit_async(findKasaDevices())

def wait(seconds, exit_condition=None):
    print('waiting', end='', flush=True)
    i = 0
    while True:
        if (seconds!= 0 and i >= seconds) or (exit_condition is not None and exit_condition()):
            print()
            return
        sleep(0.5)
        print('.', end='', flush=True)
        i += 0.5


def test(devalias):
    wait(0, lambda: _future.done()) #wait for findKasaDevices to complete
    assert devalias in kasa_devices #check for devalias in kasa_devices

    future = turnon(devalias) #turn on the device
    wait(0, lambda: future.done()) #wait for device to complete turning on
    
    future = update(devalias) #update device, get current info
    wait(0, lambda: future.done()) #war
    assert kasa_devices[devalias].is_on is True

    wait(5) #leave it on for 5 seconds

    future = turnoff(devalias) #turn off the device
    wait(0, lambda: future.done()) #wait for the device to complete turning off

    future = update(devalias) #update device, get current info
    wait(0, lambda: future.done()) #wait for device to complete turning on
    assert kasa_devices[devalias].is_on is False

    try:
        stop_async() #not sure why this errors out. But it doesn't really matter?
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    test("the amp") #Replace with your device alias name.
