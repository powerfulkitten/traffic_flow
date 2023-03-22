from pydantic import BaseModel
from datetime import datetime

class volume_of_traffic(BaseModel):
    group_name : str
    date: str
    channel_uuid : str
    inference_camera_uuid : str = ''
    camera_id : str
    camera_name : str
    camera_alias : str = ''
    volume_of_traffic_00_01 : int = 0
    volume_of_traffic_01_02 : int = 0
    volume_of_traffic_02_03 : int = 0
    volume_of_traffic_03_04 : int = 0
    volume_of_traffic_04_05 : int = 0
    volume_of_traffic_05_06 : int = 0
    volume_of_traffic_06_07 : int = 0
    volume_of_traffic_07_08 : int = 0
    volume_of_traffic_08_09 : int = 0
    volume_of_traffic_09_10 : int = 0
    volume_of_traffic_10_11 : int = 0
    volume_of_traffic_11_12 : int = 0
    volume_of_traffic_12_13 : int = 0
    volume_of_traffic_13_14 : int = 0
    volume_of_traffic_14_15 : int = 0
    volume_of_traffic_15_16 : int = 0
    volume_of_traffic_16_17 : int = 0
    volume_of_traffic_17_18 : int = 0
    volume_of_traffic_18_19 : int = 0
    volume_of_traffic_19_20 : int = 0
    volume_of_traffic_20_21 : int = 0
    volume_of_traffic_21_22 : int = 0
    volume_of_traffic_22_23 : int = 0
    volume_of_traffic_23_00 : int = 0
    total_volume_of_traffic: int = 0
    latest_update_timestamp : int

class backup(BaseModel):
	creation_date: datetime
	record_disconnect_start_time : datetime = None
	record_disconnect_recovery_time : datetime = None
	replenishment_status : bool
	latest_save_timestamp : int