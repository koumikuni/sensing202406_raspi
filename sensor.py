import time
import board
import adafruit_lsm9ds1
from pythonosc import udp_client
import csv
from datetime import datetime

# このラズベリーパイが使用するポート番号
port = 11001

# OSCクライアントの設定
ip = "172.23.129.128"  # 送信先のIPアドレス
client = udp_client.SimpleUDPClient(ip, port)

# I2C接続の初期化
i2c = board.I2C()  # SCL、SDAに接続

# センサー初期化を試みる関数
def try_init_sensor(xg_address, mag_address):
    try:
        return adafruit_lsm9ds1.LSM9DS1_I2C(i2c, mag_address=mag_address, xg_address=xg_address)
    except ValueError:
        print(f"センサーアドレス {xg_address}/{mag_address} が見つかりませんでした。")
        return None

# センサーオブジェクトの初期化
sensorL = try_init_sensor(0x6A, 0x1C)
sensorR = try_init_sensor(0x6B, 0x1E)

# スケールの選択（見つかったセンサーのみ）
for sensor in [sensorL, sensorR]:
    if sensor is not None:
        sensor.accel_range = adafruit_lsm9ds1.ACCELRANGE_4G
        sensor.mag_gain = adafruit_lsm9ds1.MAGGAIN_12GAUSS
        sensor.gyro_scale = adafruit_lsm9ds1.GYROSCALE_500DPS

# CSVファイルの準備
directory_path = '/home/sense/sensor_data'
filename = f"{directory_path}/sensordata_{datetime.now().strftime('%Y%m%d-%H-%M-%S')}.csv"
with open(filename, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(["Time (ms)", "Accel LX", "Accel LY", "Accel LZ", "Mag LX", "Mag LY", "Mag LZ", "Gyro LX", "Gyro LY", "Gyro LZ",
                     "Accel RX", "Accel RY", "Accel RZ", "Mag RX", "Mag RY", "Mag RZ", "Gyro RX", "Gyro RY", "Gyro RZ"])

# センサーデータの読み取り関数
def read_sensor_data(sensor, start_time):
    if sensor is None:
        return [0.0] * 9
    try:
        accel_x, accel_y, accel_z = sensor.acceleration
        mag_x, mag_y, mag_z = sensor.magnetic
        gyro_x, gyro_y, gyro_z = sensor.gyro
        return [accel_x, accel_y, accel_z, mag_x, mag_y, mag_z, gyro_x, gyro_y, gyro_z]
    except Exception as e:
        print("読み取りエラー:", e)
        return [0.0] * 9

# 成功と失敗のカウント
total_attempts = 0
successful_reads = 0

start_time = time.perf_counter()

while True:
    total_attempts += 2  # LとRの両方の試みをカウント

    # センサーLとRからデータを読み取り
    dataL = read_sensor_data(sensorL, start_time)
    dataR = read_sensor_data(sensorR, start_time)

    # 成功回数を更新
    if dataL != [0.0] * 9:
        successful_reads += 1
    if dataR != [0.0] * 9:
        successful_reads += 1

    current_time = (time.perf_counter() - start_time) * 1000  # 経過時間（ミリ秒）

    # OSCで送信
    client.send_message("/raspi/L/accel", dataL[:3])
    client.send_message("/raspi/L/mag", dataL[3:6])
    client.send_message("/raspi/L/gyro", dataL[6:])
    client.send_message("/raspi/R/accel", dataR[:3])
    client.send_message("/raspi/R/mag", dataR[3:6])
    client.send_message("/raspi/R/gyro", dataR[6:])

    # CSVにデータを書き込み
    with open(filename, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([current_time] + dataL + dataR)

    # 成功率を表示
    success_rate = (successful_reads / total_attempts) * 100
    print(f"成功率: {success_rate:.2f}%")

    time.sleep(0.01)
