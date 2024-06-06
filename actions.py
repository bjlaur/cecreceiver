from loguru import logger
import kasaactions

def volume_up():
    logger.info("volume up")
def volume_down():
    logger.info("volume down")
def volume_mute():
    logger.info("mute")
def tv_on():
    logger.info("TV ON")
    kasaactions.turnon('the amp')
def tv_off():
    logger.info("TV OFF")
    kasaactions.turnoff('the amp')



if __name__ == "__main__":
    kasaactions.test('the amp')
