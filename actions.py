from loguru import logger
from time import sleep
import sys
import kasa
import asyncio
import threading

kasa_devices = {}

def volume_up():
    logger.info("volume up")
def volume_down():
    logger.info("volume down")
def volume_mute():
    logger.info("mute")
def tv_on():
    logger.info("TV ON")
    asyncio.run(kasa_devices["the amp"].turn_on())

def tv_off():
    logger.info("TV OFF")
    asyncio.run(kasa_devices["the amp"].turn_off())


async def findKasaDevices():
    searchTimeout = 5
    found_devices = await kasa.Discover.discover(timeout=searchTimeout)
    for devStr in found_devices:
        dev = await kasa.Discover.discover_single(devStr)
        logger.info("KASA - Found device " + dev.alias)
        kasa_devices[dev.alias] =  dev

my_thread = threading.Thread(target=lambda: asyncio.run(findKasaDevices()))

my_thread.start()

if __name__ == "__main__":
    print("waiting", end = '')
    sys.stdout.flush();
    while True:
        if not my_thread.is_alive():
            tv_on()
            sleep(5)
            tv_off()

        sleep(0.5)
        print(".", end = '')
        sys.stdout.flush();


