from zk import ZK
# from attendance_module.zk_device.zk_detail.base import ZK

from datetime import datetime
import os
import logging
from logging.handlers import TimedRotatingFileHandler
import time

# Device data
device_ip = "182.180.85.13"
device_port = 4370

# Get the directory where this script is located and define the log file path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE_PATH = os.path.join(SCRIPT_DIR, "device_log.txt")


logger = logging.getLogger("ZKDeviceLogger")
logger.setLevel(logging.INFO)

# Rotate logs every week (when='W0' means rotate every Monday, backupCount=4 keeps last 4 weeks)
handler = TimedRotatingFileHandler(
    LOG_FILE_PATH, when="W0", interval=1, backupCount=4, encoding="utf-8"
)

formatter = logging.Formatter("[%(asctime)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
handler.setFormatter(formatter)
logger.addHandler(handler)


# Helper function to log message
def log(msg):
    logger.info(msg)


# Main loop: Keep trying to connect to the device
while True:
    conn = None
    try:
        '''
            UDP Mode (when force_udp=True)
            nc -vu 182.180.85.13 4370
            
            2. UDP Mode

            The device listens on the same port (4370), but expects UDP datagrams instead of TCP.

            Only certain firmware models (mostly older or embedded) support UDP mode.

            UDP is connectionless, so zk.connect() must send a “ping” packet and wait for a binary reply.
            If no reply — timeout.
        '''
        '''
            TCP Mode (default, force_udp=False)
            nc -vz 182.180.85.13 4370
            
            1. TCP Mode

            The device listens on port 4370 for TCP connections.

            When a connection is made, it performs a handshake and exchanges binary packets.

            This is the mode used by 95% of ZKTeco devices (iFace, K40, MB2000, etc.).
        '''
        zk = ZK(device_ip, port=device_port, timeout=10, password=786786, force_udp=False, ommit_ping=False)
        log("TRYING TO CONNECT")
        # print("TRYING TO CONNECT...")
        conn = zk.connect()
        log("DEVICE ONLINE")
        # print("DEVICE ONLINE")
        # print(conn.live_capture())
        # Process live attendance
        for attendance in conn.live_capture():
            # print("looping")
            try:
                if attendance is None:
                    # log("No Attendance")
                    # print("empty")
                    pass
                else:
                    # print(f"ATTENDANCE: {attendance}")
                    # logger.info(attendance)
                    attendanceSplit = str(attendance).split()
                    device_id = attendanceSplit[1]
                    device_date = str(attendanceSplit[3])
                    device_time = str(attendanceSplit[4])
                    args = {
                        "device_id": device_id,
                        "device_ip": device_ip, 
                        "device_port": device_port,
                        "attendance_date": device_date,
                        "log": device_date + " " + device_time
                    }
                    
                    import subprocess, os, json
        
                    os.chdir('/home/xpertadmin/frappe-hashu/')

                    # Convert args to JSON string
                    args_json = json.dumps(args)
                
                    command = ["bench", "--site", "hf.xperterp.net", 
                            "execute", "attendance_module.zk_device.services.live_capture.biometric_attendance.create_akfp.create_attendance_log",
                            "--kwargs", args_json  # Use --kwargs to pass JSON-formatted arguments
                            ]
                    # Run the command
                    output = subprocess.run(command, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    # Print the output
                    # print("Command Output:", output.stdout)
            except Exception as e:
                log(f"ATTENDANCE ERROR: {e}")
                # print(f"ATTENDANCE ERROR: {e}")
                break

    except Exception as e:
        log(f"CONNECTION ERROR: {e}")
        # print(f"CONNECTION ERROR: {e}")

    finally:
        if conn:
            try:
                conn.disconnect()
                log("DEVICE DISCONNECTED")
            except Exception as e:
                log(f"DISCONNECT ERROR: {e}")

    # Wait before retrying connection to avoid busy loop
    time.sleep(5)

