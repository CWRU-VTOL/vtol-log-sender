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
        logs = [
            entry for entry in ftp.list_result
            if not entry.is_dir and entry.name.upper().endswith(".BIN")
        ]

        if not logs: 
            print("No logs found")
            return None
        else:
            '''
            logs are usually numbered 00000001.BIN, 00000002.BIN, etc.
            gets the largest one from the stem 
            '''
            latest = max(logs, key=lambda x: int(Path(x.name).stem))
            print(f"Latest log: {latest.name}")

        remote_path = f"/APM/LOGS/{latest.name}"
        local_path = LOG_DIR / latest.name

        # if exists already, don't upload it 
        marker = local_path.with_suffix(".uploaded")

        if marker.exists():
            print("Latest log already uploaded")
            return None
        
        ftp.cmd_get([remote_path, str(local_path)])
        ftp.process_ftp_reply("OpenFileRO", timeout=15)

        return local_path
    else:
        print("Error with requesting log list")
        return None


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
    if api_key is not None:
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
    path_of_log = connect_to_pixhawk()
    if (path_of_log):
        code = upload_log(path_of_log, 
                          UPLOAD_URL,
                          "log-reader-deploy/1.0",
                          INGEST_API_KEY)
        if code is not None:
            marker = path_of_log.with_suffix(".uploaded")
            marker.touch()
            print("Upload successful")
        print(code)