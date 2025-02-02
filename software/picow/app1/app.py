#from lib.umqttsimple import MQTTClient

import uasyncio as asyncio
import sys
import uio

from machine import WDT

from constants import Constants
from lib.util import set_time
from project import ThisMachine
from lib.uo import UO

async def start(configFile, activeAppKey, activeApp):
    """@brief The app entry point
       @param configFile The config file that holds all machine config including the active application ID.
       @param activeAppKey The key in the config dict that details which app (1 or 2) we are running from.
       @param activeApp The active app. Either 1 or 2."""
    
    if Constants.SHOW_MESSAGES_ON_STDOUT:
        uo = UO(enabled=True, debug_enabled=True)
        uo.info("Started app")
        uo.info("Running app{}".format(activeApp))
    else:
        uo = None

    wdt = WDT(timeout=Constants.WDT_TIMEOUT_MSECS)  # Enable watchdog timer here.
                                                    # If the WiFi goes down then we can
                                                    # drop out to the REPL prompt.
                                                    # The WDT will then trigger a reboot.      

    # Contains the machine specific code in here.
    thisMachine = ThisMachine(uo, configFile, activeAppKey, activeApp, wdt)
    # If in WiFi setup mode, block here until the WiFi is setup.
    if thisMachine.isWifiSetupModeActive():
        # Hold here until the user sets up the WiFi
        while True:
            thisMachine.serviceWiFiSetupMode()
            if wdt:
                wdt.feed()
            await asyncio.sleep(0.1)

    # Wait for a WiFi network connection
    else:
        while True:
            ipAddress = thisMachine.serviceWiFiConnecting()
            if ipAddress:
                break
            if wdt:
                wdt.feed()
            await asyncio.sleep(1)

    set_time(uo, wdt)
    asyncio.create_task(sync_time(uo))

    while True:
        delaySeconds = thisMachine.serviceRunningMode()
        if wdt:
            wdt.feed()
        await asyncio.sleep(delaySeconds)


async def sync_time(uo):
    uo.info("calling sync time")
    while True:
        try:
            await asyncio.sleep(21600)
            uo.info("post sleep")
            set_time(uo)
            uo.info("post set_time")
        except Exception as e:
            buf = uio.StringIO()
            sys.print_exception(e, buf)
            uo.error(buf.getvalue())
            uo.error("Failed to sync time")
