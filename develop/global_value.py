import pymongo, json

def init():
    global server_volume_of_traffic_collection, local_volume_of_traffic_collection, local_volume_of_traffic_backup_collection
    global count_dict, json_data, server_db_is_offline, server_mongodb_client, local_mongodb_client, document_date_dict

    config_file = open('config.json', encoding = 'utf-8')
    json_data = json.load(config_file)
    
    if json_data['mongo_db']['server_db_username'] and json_data['mongo_db']['server_db_password']:
        server_mongodb_client = pymongo.MongoClient(f"mongodb://{json_data['mongo_db']['server_db_username']}:{json_data['mongo_db']['server_db_password']}@{json_data['mongo_db']['server_db_ip']}", port = json_data['mongo_db']['server_db_port'], serverSelectionTimeoutMS = 5)
    else:
        server_mongodb_client = pymongo.MongoClient(json_data['mongo_db']['server_db_ip'], port = json_data['mongo_db']['server_db_port'], serverSelectionTimeoutMS = 5)
    #local_mongodb_client = pymongo.MongoClient(json_data['mongo_db']['local_db_ip'], port = json_data['mongo_db']['local_db_port'],serverSelectionTimeoutMS = 5)
    local_mongodb_client = pymongo.MongoClient(f"mongodb://{json_data['mongo_db']['local_db_username']}:{json_data['mongo_db']['local_db_password']}@{json_data['mongo_db']['local_db_ip']}", port = json_data['mongo_db']['local_db_port'],serverSelectionTimeoutMS = 5)

    server_db = server_mongodb_client['TC_DB']
    local_db = local_mongodb_client['Highway']
    
    server_volume_of_traffic_collection = server_db[f'{json_data["mac"]}_volume_of_traffic']
    local_volume_of_traffic_collection = local_db['volume_of_traffic']
    local_volume_of_traffic_backup_collection = local_db['volume_of_traffic_backup']
    count_dict = {
        0:"volume_of_traffic_00_01",
        1:"volume_of_traffic_01_02",
        2:"volume_of_traffic_02_03",
        3:"volume_of_traffic_03_04",
        4:"volume_of_traffic_04_05",
        5:"volume_of_traffic_05_06",
        6:"volume_of_traffic_06_07",
        7:"volume_of_traffic_07_08",
        8:"volume_of_traffic_08_09",
        9:"volume_of_traffic_09_10",
        10:"volume_of_traffic_10_11",
        11:"volume_of_traffic_11_12",
        12:"volume_of_traffic_12_13",
        13:"volume_of_traffic_13_14",
        14:"volume_of_traffic_14_15",
        15:"volume_of_traffic_15_16",
        16:"volume_of_traffic_16_17",
        17:"volume_of_traffic_17_18",
        18:"volume_of_traffic_18_19",
        19:"volume_of_traffic_19_20",
        20:"volume_of_traffic_20_21",
        21:"volume_of_traffic_21_22",
        22:"volume_of_traffic_22_23",
        23:"volume_of_traffic_23_00",
    }
    server_db_is_offline = False
    document_date_dict = {'server':[], 'local':[]}