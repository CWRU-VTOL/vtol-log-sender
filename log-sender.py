from pymavlink import mavutil
from pathlib import Path
import time 
import subprocess
import os 
from dotenv import load_dotenv

# setup 
DEVICE = '/dev/ttyACM0'
BAUD = 115200

LOG_DIR = Path(__file__).resolve().parent / "flight-logs"
LOG_DIR.mkdir(parents = True, exist_ok = True)

load_dotenv()
INGEST_API_KEY = os.getenv("INGEST_API_KEY")
UPLOAD_URL = os.getenv("UPLOAD_URL")


def connect_to_pixhawk():
    master = mavutil.mavlink_connection(DEVICE, BAUD)

    master.target_system = 1
    master.target_component = 1

    print("Sending heartbeat")
    master.mav.heartbeat_send(
        mavutil.mavlink.MAV_TYPE_GCS,
        mavutil.mavlink.MAV_AUTOPILOT_INVALID, 0, 0, 0
    )

    # makes sure it doesn't skip first command 
    time.sleep(1) 
    print("Requesting log list")

    master.mav.log_request_list_send(
        master.target_system,
        master.target_component, 
        0, 
        0xFFFF
    )

    while True:
        msg = master.recv_match(type='LOG_ENTRY', blocking = True, timeout = 5)
        if not msg:
            print("No logs found")
            break
        print(f"Log ID: {msg.id}, Size {msg.size} bytes, Time: {msg.time_utc}")



def upload_log(file_path, target_url, user_agent, api_key=None):
    """Uploads a log to a provided server"""
    cmd = [
        "curl", 
        "--config", "-", 
        "--fail-with-body",
        "--user-agent", user_agent, 
        "-F", f"file=@{file_path}", 
        target_url 
    ]
    if api_key != None:
        stdin_config = f'header = "Authorization: Bearer {api_key}"\n'

    result = subprocess.run(
        cmd, 
        input = stdin_config,
        capture_output = True,
        text = True
    )

    if result.returncode == 0:
        return result.stdout
    else:
        print(f"Command failed (Exit code: {result.returncode})")
        print(f"Response Body: {result.stdout}")
        print(f"Stderr Trace: {result.stderr}")
        return None

def main():
    connect_to_pixhawk()



if __name__ == '__main__':
    main()
