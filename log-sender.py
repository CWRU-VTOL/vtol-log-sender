from pymavlink import mavutil
from pymavlink import mavftp
from pathlib import Path
import time 
import subprocess
import os 
from dotenv import load_dotenv

# setup 
load_dotenv()
DEVICE = '/dev/ttyACM0'
BAUD = 115200

LOG_DIR = Path(__file__).resolve().parent / "flight-logs"
LOG_DIR.mkdir(parents = True, exist_ok = True)

INGEST_API_KEY = os.getenv("INGEST_API_KEY")
UPLOAD_URL = os.getenv("UPLOAD_URL")


def connect_to_pixhawk():
    master = mavutil.mavlink_connection(DEVICE, BAUD)

    master.wait_heartbeat()

    ftp = mavftp.MAVFTP(master,
			target_system = master.target_system,
			target_component = master.target_component)

    # makes sure it doesn't skip first command 
    time.sleep(1) 
    print("Requesting log list")

    result = ftp.cmd_list(["/APM/LOGS"])

    if result.return_code == mavftp.FtpError.Success:
        for entry in ftp.list_result:
            type_str = "DIR" if entry.is_dir else "FILE"
            print(f"[{type_str}] {entry.name} - {entry.size_b} bytes")
    else:
        print(f"Failed to list logs: {result.return_code}")


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

if __name__ == '__main__':
    connect_to_pixhawk()
