from typing import Optional
from datetime import datetime
import subprocess

from ovshell import protocol

TIME_OFF_TOLERANCE = 5  # seconds
SETDATE_BINARY = "//usr/bin/date"


async def gps_time_sync(shell: protocol.OpenVarioShell) -> None:
    """Service to set system time from GPS NMEA stream

    Only change system time if it differs considerable (say, 5 seconds off) and
    stop synching once we've set time once (until the next restart).

    Be cautious, because there might be other services to sync time (e.g. NTP)
    around, and these should be trusted more than this naive sync.
    """
    with shell.devices.open_nmea() as nmea_stream:
        async for nmea in nmea_stream:
            dt = parse_gps_datetime(nmea)
            if dt is not None:
                set_system_time(dt, binpath=shell.os.path(SETDATE_BINARY))
                break


def parse_gps_datetime(nmea: protocol.NMEA) -> Optional[datetime]:
    if nmea.datatype != "GPRMC":
        return None

    rawtime = nmea.fields[0]
    rawdate = nmea.fields[8]
    if len(rawtime) != 6 or len(rawdate) != 6:
        return None

    year2 = int(rawdate[4:6])
    month = int(rawdate[2:4])
    day = int(rawdate[0:2])
    hour = int(rawtime[0:2])
    minute = int(rawtime[2:4])
    second = int(rawtime[4:6])

    year4 = year2 + 1900 if year2 > 90 else year2 + 2000
    return datetime(year4, month, day, hour, minute, second)


def set_system_time(dt: datetime, now: datetime = None, binpath: str = "date") -> bool:
    now = now or datetime.utcnow()
    delta = dt - now
    if abs(delta.total_seconds()) < TIME_OFF_TOLERANCE:
        # Time is off for not that much. Don't bother syncing
        return False

    # Actually set time
    cmd = [binpath, "+%F %H:%M:%S", "-s", dt.strftime("%F %H:%M:%S")]
    subprocess.run(cmd, check=True)
    return True
