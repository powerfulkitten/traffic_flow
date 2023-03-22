import time, requests

while True:
    date = {
        "license_plate":"ABC-123",
        "timestamp":int(time.time()*1000),
        "channel_uuid":"CH-1",
        "camera_id" : "e3e9a385-7fe0-3ba5-5482-a86cde7faf48",
        "camera_name" : "TestCameraLive-enter"
    }
    requests.post("http://192.168.2.60:4444/receive_aisense", json = date)
    time.sleep(3)