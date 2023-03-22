from logging.config import dictConfig
import logging, requests
import collection_fotmat, global_value
import uvicorn, time, uuid
from pymongo.errors import ServerSelectionTimeoutError, OperationFailure
from fastapi import FastAPI, Body
from typing import Any, Dict
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from requests.auth import HTTPBasicAuth

volume_of_traffic_api = FastAPI(docs_url="/docs", openapi_url="/openapi.json")

def set_logger():
    dictConfig({
        'version': 1,
        'formatters': {'default': {
            'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
        }},
        'handlers': {'console': {
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',
            'formatter': 'default'
        }, 'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'default',
            'filename': "logs/volume.log",
            'maxBytes': 300*1024*1024,
            'backupCount': 3,
        }},
        'root': {
            'level': 'INFO',
            'handlers': ['console', 'file']
        }
    })

def add_new_date_documents_to_collection(group_name, date, channel_uuid, camera_id, camera_name, collection, camera_alias = '', inference_camera_uuid = ''):
    payload = collection_fotmat.volume_of_traffic(
        group_name = group_name,
        date = date,
        channel_uuid = channel_uuid,
        inference_camera_uuid = inference_camera_uuid,
        camera_id = camera_id,
        camera_name = camera_name,
        camera_alias = camera_alias,
        latest_update_timestamp = int(time.time()*1000)
        ).dict()
    collection.insert_one(payload)

def check_server_db_connect(retry_connect_count = 0):
    try:
        global_value.server_volume_of_traffic_collection.find_one({"test" : "test"})
        return True
    except ServerSelectionTimeoutError:
        if retry_connect_count < 3:
            retry_connect_count += 1
            logging.warning(f'Server Check > Retry connect server db > {retry_connect_count}')
            check_server_db_connect(retry_connect_count = retry_connect_count)
        else:
            try:
                for row in global_value.local_volume_of_traffic_backup_collection.find():
                    if not row['record_disconnect_recovery_time'] and not row['replenishment_status']:
                        global_value.server_db_is_offline = True
                        return False
                global_value.local_volume_of_traffic_backup_collection.insert_one(collection_fotmat.backup(
                        creation_date = datetime.now(),
                        record_disconnect_start_time = datetime.now(),
                        replenishment_status = False,
                        latest_save_timestamp = int(time.time()*1000)
                    ).dict())
            except ServerSelectionTimeoutError:
                logging.error(f'Server Check > Retry connect server db > {retry_connect_count}')
            except OperationFailure as msg:
                logging.error(f"Server Check > {msg.details['codeName']}")
            global_value.server_db_is_offline = True
            return False
    except OperationFailure as msg:
            logging.error(f"Server Check > {msg.details['codeName']}")

def check_document():
    today = datetime.today().date().strftime("%Y/%m/%d")
    for group_name, group_payload in global_value.json_data['group'].items():
        try:
            if not global_value.local_volume_of_traffic_collection.find_one({"group_name":group_name, "date":today}):
                add_new_date_documents_to_collection(
                    group_name = group_name,
                    date = today,
                    channel_uuid = group_payload['channel_uuid'],
                    #inference_camera_uuid = group_payload['inference_camera_uuid'],
                    camera_id = group_payload['camera_id'],
                    camera_name = group_payload['camera_name'],
                    #camera_alias = group_payload['camera_alias'],
                    collection = global_value.local_volume_of_traffic_collection
                    )
        except ServerSelectionTimeoutError as msg:
            logging.error("INIT > Local DB disconnect")
        except OperationFailure as msg:
            logging.error(f"INIT > {msg.details['codeName']}")
        except KeyError as msg:
            logging.error(f"Not found key '{msg}'")
        try:
            if not global_value.server_volume_of_traffic_collection.find_one({"group_name":group_name, "date":today}):
                add_new_date_documents_to_collection(
                    group_name = group_name,
                    date = today,
                    channel_uuid = group_payload['channel_uuid'],
                    #inference_camera_uuid = group_payload['inference_camera_uuid'],
                    camera_id = group_payload['camera_id'],
                    camera_name = group_payload['camera_name'],
                    #camera_alias = group_payload['camera_alias'],
                    collection = global_value.server_volume_of_traffic_collection
                    )
        except ServerSelectionTimeoutError as msg:
            if check_server_db_connect():
                check_document()
            else:
                logging.error('INIT > Server DB disconnect')
        except OperationFailure as msg:
            logging.error(f"INIT > {msg.details['codeName']}")
        except KeyError as msg:
            logging.error(f"Not found key '{msg}'")
    add_tomorrow_document()

def add_tomorrow_document():
    if (datetime.today() + timedelta(days = 1)).date().strftime("%Y/%m/%d") not in global_value.document_date_dict['server']:
        global_value.document_date_dict['server'].append((datetime.today() + timedelta(days = 1)).date().strftime("%Y/%m/%d"))
    if (datetime.today() + timedelta(days = 1)).date().strftime("%Y/%m/%d") not in global_value.document_date_dict['local']:
        global_value.document_date_dict['local'].append((datetime.today() + timedelta(days = 1)).date().strftime("%Y/%m/%d"))
    for group_name, group_payload in global_value.json_data['group'].items():
        for date in global_value.document_date_dict['local']:
            try:
                if global_value.local_volume_of_traffic_collection.find_one({"group_name":group_name, "date":date}):
                    global_value.document_date_dict['local'].remove(date)
                else:
                    add_new_date_documents_to_collection(
                        group_name = group_name,
                        date = date,
                        channel_uuid = group_payload['channel_uuid'],
                        #inference_camera_uuid = group_payload['inference_camera_uuid'],
                        camera_id = group_payload['camera_id'],
                        camera_name = group_payload['camera_name'],
                        #camera_alias = group_payload['camera_alias'],
                        collection = global_value.local_volume_of_traffic_collection
                        )
            except ServerSelectionTimeoutError:
                logging.error('Tomorrow > Local DB disconnect')
            except OperationFailure as msg:
                logging.error(f"Tomorrow > {msg.details['codeName']}")
        for date in global_value.document_date_dict['server']:
            try:
                if global_value.server_volume_of_traffic_collection.find_one({"group_name":group_name, "date":date}):
                    global_value.document_date_dict['server'].remove(date)
                else:
                    add_new_date_documents_to_collection(
                        group_name = group_name,
                        date = date,
                        channel_uuid = group_payload['channel_uuid'],
                        #inference_camera_uuid = group_payload['inference_camera_uuid'],
                        camera_id = group_payload['camera_id'],
                        camera_name = group_payload['camera_name'],
                        #camera_alias = group_payload['camera_alias'],
                        collection = global_value.server_volume_of_traffic_collection
                        )
                    if global_value.server_db_is_offline:
                        try:
                            global_value.local_volume_of_traffic_backup_collection.find_one_and_update({"record_disconnect_recovery_time" : None}, {"$set":{"record_disconnect_recovery_time":datetime.now(), "latest_save_timestamp": int(time.time()*1000)}})
                        except ServerSelectionTimeoutError:
                            logging.error('Tomorrow > Backup fail > Local DB disconnent')
                        except OperationFailure as msg:
                            logging.error(f"Tomorrow > {msg.details['codeName']}")
                        global_value.server_db_is_offline = False
            except ServerSelectionTimeoutError:
                if check_server_db_connect():
                    add_tomorrow_document()
                else:
                  logging.error('Tomorrow > Server DB disconnect')
            except OperationFailure as msg:
                logging.error(f"Tomorrow > {msg.details['codeName']}")

def init_check_backup():
    try:
        for rows in global_value.local_volume_of_traffic_backup_collection.find():
            if not rows['record_disconnect_recovery_time'] and check_server_db_connect():
                try:
                    global_value.local_volume_of_traffic_backup_collection.find_one_and_update({"record_disconnect_recovery_time" : None}, {"$set":{"record_disconnect_recovery_time":datetime.now(), "latest_save_timestamp": int(time.time()*1000)}})
                except ServerSelectionTimeoutError:
                    logging.error('Tomorrow > Backup fail > Local DB disconnent')
                except OperationFailure as msg:
                    logging.error(f"Tomorrow > {msg.details['codeName']}")
                return
    except ServerSelectionTimeoutError:
        logging.error('Tomorrow > Backup fail > Local DB disconnent')
    except OperationFailure as msg:
        logging.error(f"Tomorrow > {msg.details['codeName']}")

@volume_of_traffic_api.post('/receive_aisense')
def volume_of_traffic(data: Dict[str, Any] = Body(...), local_db_loss_collection = False, server_db_loss_collection = False):
    try:
        receive_date = datetime.fromtimestamp(data['timestamp']/1000)
        receive_hour = time.localtime(data['timestamp']/1000).tm_hour
        for group_payload in global_value.json_data['group'].values():
            if data['camera_id'] == group_payload['camera_id']:
                if group_payload['bookmark'] == "True":
                    caption_payload = f"{data['camera_name']}\n{receive_date.strftime('%Y/%m/%d %H:%M:%S')}\n{data['license_plate']}"
                    respond = requests.get(f"http://{group_payload['nx_server_host']}:7001/ec2/bookmarks/add?guid={str(uuid.uuid4())}&cameraId={data['camera_id']}&name={data['license_plate']}&description={caption_payload}&startTimeMs={str(data['timestamp'])}&durationMs=3000", auth = HTTPBasicAuth(group_payload['nx_server_username'], group_payload['nx_server_password']))
                    logging.info(f"Bookmarks > {respond.text}")
                if group_payload['overlay'] == "True":
                    caption_payload = f"{data['camera_name']}\n{receive_date.strftime('%Y/%m/%d %H:%M:%S')}\n{data['license_plate']}"
                    respond = requests.get(f"http://{group_payload['nx_server_host']}:7001/api/createEvent?caption={caption_payload}&source={group_payload['camera_id']}", auth = HTTPBasicAuth(group_payload['nx_server_username'], group_payload['nx_server_password']))
                    logging.info(f"Overlay > {respond.text}")
        if receive_date.strftime("%Y/%m/%d") == datetime.now().strftime("%Y/%m/%d"):
            receive_date = receive_date.strftime("%Y/%m/%d")
            for group_name in global_value.json_data['group']:
                try:
                    if global_value.local_volume_of_traffic_collection.find_one({"group_name":group_name, "date":receive_date}):
                        current_config = global_value.local_volume_of_traffic_collection.find_one({"group_name":group_name, "date":receive_date})
                        if (local_db_loss_collection or server_db_loss_collection) and not local_db_loss_collection:
                            pass
                        elif current_config['channel_uuid'] == data['channel_uuid'] and current_config['camera_id'] == data['camera_id'] and current_config['camera_name'] == data['camera_name']:
                            current_config[global_value.count_dict[receive_hour]] += 1
                            current_config['total_volume_of_traffic'] += 1
                            current_config['latest_update_timestamp'] = int(time.time()*1000)
                            global_value.local_volume_of_traffic_collection.update_one({"group_name":group_name, "date":receive_date}, {"$set": current_config})
                        local_db_loss_collection = False
                    else:
                        check_document()
                        local_db_loss_collection = True
                        volume_of_traffic(data = data, local_db_loss_collection = local_db_loss_collection, server_db_loss_collection = server_db_loss_collection)
                        break
                except ServerSelectionTimeoutError:
                    logging.error('Receive AIsense > Local DB disconnect')
                except OperationFailure as msg:
                    logging.error(f"Receive AIsense > {msg.details['codeName']}")
                try:
                    if global_value.server_volume_of_traffic_collection.find_one({"group_name":group_name, "date":receive_date}):
                        current_config = global_value.server_volume_of_traffic_collection.find_one({"group_name":group_name, "date":receive_date})
                        if (local_db_loss_collection or server_db_loss_collection) and not server_db_loss_collection:
                            pass
                        elif current_config['channel_uuid'] == data['channel_uuid'] and current_config['camera_id'] == data['camera_id'] and current_config['camera_name'] == data['camera_name']:
                            current_config[global_value.count_dict[receive_hour]] += 1
                            current_config['total_volume_of_traffic'] += 1
                            current_config['latest_update_timestamp'] = int(time.time()*1000)
                            global_value.server_volume_of_traffic_collection.update_one({"group_name":group_name, "date":receive_date}, {"$set": current_config})
                        server_db_loss_collection = False
                        if global_value.server_db_is_offline:
                            try:
                                global_value.local_volume_of_traffic_backup_collection.find_one_and_update({"record_disconnect_recovery_time" : None}, {"$set":{"record_disconnect_recovery_time":datetime.now(), "latest_save_timestamp": int(time.time()*1000)}})
                            except ServerSelectionTimeoutError:
                                logging.error('Receive AIsense > Backup fail > Local DB disconnent')
                            except OperationFailure as msg:
                                logging.error(f"Receive AIsense > {msg.details['codeName']}")
                            global_value.server_db_is_offline = False
                    else:
                        check_document()
                        server_db_loss_collection = True
                        volume_of_traffic(data = data, local_db_loss_collection = local_db_loss_collection, server_db_loss_collection = server_db_loss_collection)
                        break
                except ServerSelectionTimeoutError:
                    if check_server_db_connect():
                        volume_of_traffic(data = data)
                    else:
                        logging.error('Receive AIsense > Server DB disconnect')
                except OperationFailure as msg:
                    logging.error(f"Receive AIsense > {msg.details['codeName']}")
        else:
            logging.error('Invali Date!!!')
    except KeyError as msg:
        logging.error(f"Not found key '{msg}'")

@volume_of_traffic_api.post('/backup')
def backup():
    try:
        if check_server_db_connect():
            check_document()
            for backup_row in global_value.local_volume_of_traffic_backup_collection.find({"replenishment_status":False}):
                if backup_row['record_disconnect_start_time'] and backup_row['record_disconnect_recovery_time']:
                    start_time = datetime(backup_row['record_disconnect_start_time'].year, backup_row['record_disconnect_start_time'].month, backup_row['record_disconnect_start_time'].day, backup_row['record_disconnect_start_time'].hour)
                    end_time = backup_row['record_disconnect_recovery_time']
                    while start_time < end_time:
                        date = start_time.strftime("%Y/%m/%d")
                        try:
                            for rows in global_value.server_volume_of_traffic_collection.find({"date":date}):
                                if rows[global_value.count_dict[start_time.hour]] < global_value.local_volume_of_traffic_collection.find_one({"group_name":rows['group_name'], "date":date})[global_value.count_dict[start_time.hour]]:
                                    rows[global_value.count_dict[start_time.hour]] = global_value.local_volume_of_traffic_collection.find_one({"group_name":rows['group_name'], "date":date})[global_value.count_dict[start_time.hour]]
                                    rows['total_volume_of_traffic'] = rows['total_volume_of_traffic'] + global_value.local_volume_of_traffic_collection.find_one({"group_name":rows['group_name'], "date":date})[global_value.count_dict[start_time.hour]] - global_value.server_volume_of_traffic_collection.find_one({"group_name":rows['group_name'], "date":date})[global_value.count_dict[start_time.hour]]
                                    rows['latest_update_timestamp'] = int(time.time()*1000)
                                    global_value.server_volume_of_traffic_collection.update_one({"group_name":rows['group_name'], "date":date}, {"$set": rows})
                        except ServerSelectionTimeoutError:
                            return {"Result":"Fail", "Message":"Server MongoDB > disconnect"}
                        except OperationFailure as msg:
                            return {"Result":"Fail", "Message":f"Server MongoDB > {msg.details['codeName']}"}
                        start_time = start_time + timedelta(hours = 1)
                    backup_row['replenishment_status'] = True
                    backup_row['latest_save_timestamp'] = int(time.time()*1000)
                    global_value.local_volume_of_traffic_backup_collection.update_one({"replenishment_status":False}, {"$set": backup_row})
            return {"Result":"Succee", "Message":"Replenishment done"}
        else:
            return {"Result":"Fail", "Message":"Server DB disconnect!!!"}
    except ServerSelectionTimeoutError:
        return {"Result":"Fail", "Message":"Local MongoDB > disconnect"}
    except OperationFailure as msg:
        return {"Result":"Fail", "Message":f"Local MongoDB > {msg.details['codeName']}"}

@volume_of_traffic_api.post('/range_backup')
def range_backup(data: Dict[str, Any] = Body(...)):
    try:
        range_backup_start_time = datetime.strptime(data['start_time'], '%Y/%m/%d %H:%M')
        range_backup_end_time = datetime.strptime(data['end_time'], '%Y/%m/%d %H:%M')
        try:
            if check_server_db_connect():
                check_document()
                for backup_row in global_value.local_volume_of_traffic_backup_collection.find({"replenishment_status":False}):
                    if backup_row['record_disconnect_start_time'] and backup_row['record_disconnect_recovery_time']:
                        backup_start_time = datetime(backup_row['record_disconnect_start_time'].year, backup_row['record_disconnect_start_time'].month, backup_row['record_disconnect_start_time'].day, backup_row['record_disconnect_start_time'].hour)
                        backup_end_time = backup_row['record_disconnect_recovery_time']
                        while backup_start_time < backup_end_time:
                            if range_backup_start_time <= backup_start_time < range_backup_end_time:
                                date = backup_start_time.strftime("%Y/%m/%d")
                                try:
                                    for rows in global_value.server_volume_of_traffic_collection.find({"date":date}):
                                        if rows[global_value.count_dict[backup_start_time.hour]] < global_value.local_volume_of_traffic_collection.find_one({"group_name":rows['group_name'], "date":date})[global_value.count_dict[backup_start_time.hour]]:
                                            rows[global_value.count_dict[backup_start_time.hour]] = global_value.local_volume_of_traffic_collection.find_one({"group_name":rows['group_name'], "date":date})[global_value.count_dict[backup_start_time.hour]]
                                            rows['total_volume_of_traffic'] = rows['total_volume_of_traffic'] + global_value.local_volume_of_traffic_collection.find_one({"group_name":rows['group_name'], "date":date})[global_value.count_dict[start_time.hour]] - global_value.server_volume_of_traffic_collection.find_one({"group_name":rows['group_name'], "date":date})[global_value.count_dict[start_time.hour]]
                                            rows['latest_update_timestamp'] = int(time.time()*1000)
                                            global_value.server_volume_of_traffic_collection.update_one({"group_name":rows['group_name'], "date":date}, {"$set": rows})
                                except ServerSelectionTimeoutError:
                                    return {"Result":"Fail", "Message":"Server MongoDB > disconnect"}
                                except OperationFailure as msg:
                                    return {"Result":"Fail", "Message":f"Server MongoDB > {msg.details['codeName']}"}
                            backup_start_time = backup_start_time + timedelta(hours = 1)
                return {"Result":"Succee", "Message":"Replenishment done"}
            else:
                return {"Result":"Fail", "Message":"Server DB disconnect!!!"}
        except ServerSelectionTimeoutError:
            return {"Result":"Fail", "Message":"Local MongoDB > disconnect"}
        except OperationFailure as msg:
            return {"Result":"Fail", "Message":f"Local MongoDB > {msg.details['codeName']}"}
    except KeyError as msg:
        logging.error(f"Not found key '{msg}'")

@volume_of_traffic_api.post('/total')
def total(data: Dict[str, Any] = Body(...)):
    try:
        total_volume_of_traffic = 0
        if check_server_db_connect():
            check_document()
            for row in global_value.server_volume_of_traffic_collection.find({"date":datetime.strptime(data['date'], '%Y/%m/%d').strftime("%Y/%m/%d")}):
                print(f"{row['group_name']} > {row['total_volume_of_traffic']}")
                total_volume_of_traffic += row['total_volume_of_traffic']
            return {"Result":"Succee", "total":total_volume_of_traffic}
        else:
            return {"Result":"Fail", "Message":"Server DB disconnect!!!"}
    except KeyError as msg:
        logging.error(f"Not found key '{msg}'")

@volume_of_traffic_api.get('/args')
def get_args():
    return global_value.json_data, {"server_db_is_offline":global_value.server_db_is_offline, "document_date_dict":global_value.document_date_dict}

@volume_of_traffic_api.get('/serverdb_check')
def serverdb_connect_check():
    try:
        global_value.server_volume_of_traffic_collection.find_one({"test" : "test"})
        if global_value.server_db_is_offline:
            try:
                global_value.local_volume_of_traffic_backup_collection.find_one_and_update({"record_disconnect_recovery_time" : None}, {"$set":{"record_disconnect_recovery_time":datetime.now(), "latest_save_timestamp": int(time.time()*1000)}})
            except ServerSelectionTimeoutError:
                logging.error('Receive AIsense > Backup fail > Local DB disconnent')
            except OperationFailure as msg:
                logging.error(f"Receive AIsense > {msg.details['codeName']}")
            global_value.server_db_is_offline = False
        return {"Message":"Server MongoDB is connect"}
    except ServerSelectionTimeoutError:
        if check_server_db_connect():
            global_value.server_db_is_offline = True
            return {"Message":"Server MongoDB is connect"}
        else:
            return {"Message":"Server MongoDB is disconnect"}
    except OperationFailure as msg:
        return {"Message":f"Server MongoDB > {msg.details['codeName']}"}

@volume_of_traffic_api.get('/localdb_check')
def localdb_connect_check():
    try:
        global_value.local_volume_of_traffic_collection.find_one({"test" : "test"})
        return {"Message":"Local MongoDB is Connect"}
    except ServerSelectionTimeoutError:
        return {"Message":"Local MongoDB is disconnect"}
    except OperationFailure as msg:
        return {"Message":f"Local MongoDB > {msg.details['codeName']}"}

def nx_overlay():
    for group_payload in global_value.json_data['group'].values():
         group_total_volume_of_traffic = global_value.server_volume_of_traffic_collection.find_one({"date":datetime.now().strftime("%Y/%m/%d"), "camera_name":group_payload['camera_name']})['total_volume_of_traffic']
         respond = requests.get(f"http://{group_payload['nx_server_host']}:7001/api/createEvent?caption=Total:{group_total_volume_of_traffic}&source={group_payload['camera_name']}", auth = HTTPBasicAuth(global_value.json_data['nx']['username'], global_value.json_data['nx']['password']))
         print(respond.text)

if __name__ == "__main__":
    set_logger()
    logging.info('Wait MongoDB Building')
    time.sleep(10)
    global_value.init()
    init_check_backup()
    check_document()
    add_schedule_task = BackgroundScheduler()
    add_schedule_task.add_job(func = add_tomorrow_document, trigger='cron', hour = 12)
    add_schedule_task.add_job(func = nx_overlay, trigger='cron', hour = 00)
    add_schedule_task.add_job(func = nx_overlay, trigger='cron', hour = 1)
    add_schedule_task.add_job(func = nx_overlay, trigger='cron', hour = 2)
    add_schedule_task.add_job(func = nx_overlay, trigger='cron', hour = 3)
    add_schedule_task.add_job(func = nx_overlay, trigger='cron', hour = 4)
    add_schedule_task.add_job(func = nx_overlay, trigger='cron', hour = 5)
    add_schedule_task.add_job(func = nx_overlay, trigger='cron', hour = 6)
    add_schedule_task.add_job(func = nx_overlay, trigger='cron', hour = 7)
    add_schedule_task.add_job(func = nx_overlay, trigger='cron', hour = 8)
    add_schedule_task.add_job(func = nx_overlay, trigger='cron', hour = 9)
    add_schedule_task.add_job(func = nx_overlay, trigger='cron', hour = 10)
    add_schedule_task.add_job(func = nx_overlay, trigger='cron', hour = 11)
    add_schedule_task.add_job(func = nx_overlay, trigger='cron', hour = 12)
    add_schedule_task.add_job(func = nx_overlay, trigger='cron', hour = 13)
    add_schedule_task.add_job(func = nx_overlay, trigger='cron', hour = 14)
    add_schedule_task.add_job(func = nx_overlay, trigger='cron', hour = 15)
    add_schedule_task.add_job(func = nx_overlay, trigger='cron', hour = 16)
    add_schedule_task.add_job(func = nx_overlay, trigger='cron', hour = 17)
    add_schedule_task.add_job(func = nx_overlay, trigger='cron', hour = 18)
    add_schedule_task.add_job(func = nx_overlay, trigger='cron', hour = 19)
    add_schedule_task.add_job(func = nx_overlay, trigger='cron', hour = 20)
    add_schedule_task.add_job(func = nx_overlay, trigger='cron', hour = 21)
    add_schedule_task.add_job(func = nx_overlay, trigger='cron', hour = 22)
    add_schedule_task.add_job(func = nx_overlay, trigger='cron', hour = 23)
    add_schedule_task.start()
    uvicorn.run(app = 'volume_of_traffic:volume_of_traffic_api', host = global_value.json_data['fastapi']['volume_of_traffic_fastapi_host'], port = global_value.json_data['fastapi']['volume_of_traffic_fastapi_port'])