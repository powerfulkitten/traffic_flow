# 國道中區說明文件
## 相關檔案
![](https://i.imgur.com/jsnAXmf.jpg)
***
### compose.yml
![](https://i.imgur.com/tzBqGKd.jpg)
```json=
volume_mongodb:
    environment > 預設mongodb權限
    ports > 設定外部Port(22222 > 需與config內的local_db_port一致)對應容器內部Port(27017 > mongodb預設port號)

volume:
    volumes > 設定外部檔案至容器內部檔案
    ports > 設定外部Port(4444 > 需與config內的volume_of_traffic_fastapi_port一致)對應容器內部Port(4444 > 車流計數server port號)
```
***
### config.json
![](https://i.imgur.com/ZPLGrMQ.jpg)

```json=
{	
	"mac":當前車辨主機的mac address,
	"mongo_db" : {
		"server_db_ip" : Server MongoDB 位置,
		"server_db_port" : Server MongoDB Port號,
		"server_db_username" : Server MongoDB 使用者名稱,
		"server_db_password" : Server MongoDB 密碼,
		"local_db_ip" : Local MongoDB 位置,
		"local_db_port" : Local MongoDB Port號,
		"local_db_username" : Local MongoDB 使用者名稱,
		"local_db_password" : Local MongoDB 密碼
	},
	"fastapi" : {
		"volume_of_traffic_fastapi_host" : Fastapi Host(預設0.0.0.0請勿調整),
		"volume_of_traffic_fastapi_port" : Fastapi Port號
	},
	"group" : {
		"清水服務區入口左側攝影機"(群組名稱:可視為該攝影機的描述) : {
				"channel_uuid" : 核對來源條件之一,
				"camera_id" : 核對來源條件之一,
				"camera_name" : 核對來源條件之一,
				"nx_server_host" : 建構NX"書籤"或"浮水印"功能API的url格式,
				"nx_server_username" : 建構NX"書籤"或"浮水印"功能API的url格式,
				"nx_server_password" : 建構NX"書籤"或"浮水印"功能API的url格式,
				"bookmark" : 是否啟用NX"書籤"功能,
				"overlay" : 是否啟用NX"浮水印"功能
			}
	}
}	
```
***
### setup.sh
```
執行檔
在根目錄下執行:
```
```
1.sudo ./setup.sh
```
![](https://i.imgur.com/pDcahBl.jpg)
### or
```
2.sudo sh setup.sh
```
![](https://i.imgur.com/xFl0ZVd.jpg)
## API格式說明

### 確認ServerDB連線狀態
| Method |      Path       |
| ------ |:---------------:|
| GET    | /serverdb_check |

**連線正常:**
```json=
{
    "Message": "Server MongoDB is connect"
}
```
**連線異常:**
```json=
{
    "Message": "Server MongoDB is disconnect"
}
```
### 確認LocalDB連線狀態
| Method |      Path      |
| ------ |:--------------:|
| GET    | /localdb_check |

**連線正常:**
```json=
{
    "Message": "Local MongoDB is Connect"
}
```
**連線異常:**
```json=
{
    "Message": "Local MongoDB is disconnect"
}
```
### 立即回補
| Method |  Path   |
| ------ |:-------:|
| POST   | /backup |

**回補成功:**
```json=
{
    "Result": "Succee",
    "Message": "Replenishment done"
}
```
**回補失敗(ServerDB連線異常):**
```json=
{
    "Result": "Fail",
    "Message": "Server DB disconnect!!!"
}
```
**回補失敗(LocalDB連線異常):**
```json=
{
    "Result": "Fail",
    "Message": "Local MongoDB > disconnect"
}
```
### 手動回補(需給定回補時段)
| Method |  Path   |
| ------ |:-------:|
| POST   | /range_backup |

**回補時段資料格式:**
```json=
{
    "start_time":"2023/3/2 10:00",
    "end_time":"2023/3/4 04:00"
}
```
**回補成功:**
```json=
{
    "Result": "Succee",
    "Message": "Replenishment done"
}
```
**回補失敗(ServerDB連線異常):**
```json=
{
    "Result": "Fail",
    "Message": "Server DB disconnect!!!"
}
```
**回補失敗(LocalDB連線異常):**
```json=
{
    "Result": "Fail",
    "Message": "Local MongoDB > disconnect"
}
```
### 獲取指定日期總車流量(需給定日期)
| Method |  Path   |
| ------ |:-------:|
| POST   | /total |

**日期資料格式:**
```json=
{
    "date":"2023/3/6"
}
```
**回補成功:**
```json=
{
    "Result": "Succee",
    "total": 156
}
```
**回補失敗(ServerDB連線異常):**
```json=
{
    "Result": "Fail",
    "Message": "Server DB disconnect!!!"
}
```