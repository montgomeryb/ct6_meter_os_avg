import struct
import socket
import select
import utime
import json
import sys
import uio
from machine import RTC
from constants import Constants


def get_json_stats(statsDict):
    calcStatsAverage(statsDict)
    json_str = json.dumps(statsDict)
    return json_str


def calcStatsAverage(statsDict):
    num = statsDict.get(Constants.CNTREADINGS, 0)
    for ct in Constants.VALID_CT_ID_LIST:
        ct_name = "CT{}".format(ct)
        sensor_dict = statsDict.get(ct_name, {})

        if num > 0:
            iav = sensor_dict.pop(Constants.IAVGSUM, 0) / num
            vav = sensor_dict.pop(Constants.VAVGSUM, 0) / num
        else:
            iav = 0
            vav = 0
        sensor_dict[Constants.IAVG] = iav
        sensor_dict[Constants.VAVG] = vav
        statsDict[ct_name] = sensor_dict
    statsDict[Constants.NUMREADINGS] = statsDict.pop(Constants.CNTREADINGS, None)

    statsDict[Constants.TIMESENT] = utime.time()


def set_time(out, wdt=None):
    NTP_DELTA = 2208988800
    host = "pool.ntp.org"
    NTP_QUERY = bytearray(48)
    NTP_QUERY[0] = 0x1B
    addr = socket.getaddrinfo(host, 123)[0][-1]
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        poller = select.poll()
        poller.register(s, select.POLLIN)
        s.sendto(NTP_QUERY, addr)
        if poller.poll(2000):  # time in milliseconds
            if wdt:
                wdt.feed()
            msg = s.recv(48)
            val = struct.unpack("!I", msg[40:44])[0]
            t = val - NTP_DELTA
            tm = utime.gmtime(t)
            out.info("Setting time to: {}".format(tm))
            RTC().datetime((tm[0], tm[1], tm[2], tm[6] + 1, tm[3], tm[4], tm[5], 0))
            return t
    except Exception as e:
        buf = uio.StringIO()
        sys.print_exception(e, buf)
        m = buf.getvalue()
        out.info("failed: {}".format(m))
    finally:
        s.close()
    out.info("Leaving set time")
    return 0
