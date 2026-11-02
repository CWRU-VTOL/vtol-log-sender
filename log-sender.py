from pymavlink import mavutil
import time 
import subprocess
import dotenv

DEVICE = '/dev/ttyACM0'
BAUD = 115200
LOG_DIR = '/home/txn/flight-logs'
UPLOAD_URL = "https://vtollogs.williserdman.com/api/ingest"

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



def upload_log(config_path, file_path, target_url, user_agent):
    cmd = [
        "curl", 
        "--config", config_path, 
        "--user-agent", user_agent, 
        "-F", f"file=@{file_path}", 
        target_url 
    ]

    

def main():
    connect_to_pixhawk()



if __name__ == '__main__':
    main()
