import time
import board
import adafruit_lsm9ds1
from pythonosc import udp_client
import csv
from datetime import datetime
import threading

# このラズベリーパイが使用するポート番号
port = 11001

# OSCクライアントの設定
ip = "169.254.179.100"  # 送信先のIPアドレス
client = udp_client.SimpleUDPClient(ip, port)

# I2C接続の初期化
i2c = board.I2C()  # SCL、SDAに接続

# センサー初期化を試みる関数
def try_init_sensor(xg_address, mag_address, retries=5):
    attempt = 0
    while attempt < retries:
        try:
            return adafruit_lsm9ds1.LSM9DS1_I2C(i2c, mag_address=mag_address, xg_address=xg_address)
        except ValueError:
            print(f"センサーアドレス {xg_address}/{mag_address} が見つかりませんでした。再試行 {attempt+1}/{retries}")
            time.sleep(1)  # 1秒待つ
            attempt += 1
    print(f"センサーの初期化に{retries}回試みましたが、接続できませんでした。")
    return None

# センサーオブジェクトの初期化
print("L")
sensorL = try_init_sensor(0x6A, 0x1C, retries=10)
print("R")
sensorR = try_init_sensor(0x6B, 0x1E, retries=10)

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

# キャリブレーションの処理
def calibrate(sensor, duration=5):
    global gyro_biasL, gyro_biasR, isCalibrating
    isCalibrating = 1
    start_time = time.perf_counter()
    gyro_data = []
    while (time.perf_counter() - start_time) < duration:
        dataL = read_sensor_data(sensorL, start_time)
        dataR = read_sensor_data(sensorR, start_time)
        if dataL != [0.0] * 9:
            gyro_data.append(dataL[6:])
        if dataR != [0.0] * 9:
            gyro_data.append(dataR[6:])
        time.sleep(0.01)
    
    if gyro_data:
        gyro_biasL = [sum(d[0] for d in gyro_data) / len(gyro_data), 
                      sum(d[1] for d in gyro_data) / len(gyro_data), 
                      sum(d[2] for d in gyro_data) / len(gyro_data)]
        gyro_biasR = [sum(d[3] for d in gyro_data) / len(gyro_data), 
                      sum(d[4] for d in gyro_data) / len(gyro_data), 
                      sum(d[5] for d in gyro_data) / len(gyro_data)]
    isCalibrating = 0

# メインループ
def main_loop():
    global isCalibrating
    total_attempts = 0
    successful_reads = 0
    start_time = time.perf_counter()
    gyro_biasL = [0.0, 0.0, 0.0]
    gyro_biasR = [0.0, 0.0, 0.0]

    while True:
        total_attempts += 2  # LとRの両方の試みをカウント
        dataL = read_sensor_data(sensorL, start_time)
        dataR = read_sensor_data(sensorR, start_time)

        # 成功回数を更新
        if dataL != [0.0] * 9:
            successful_reads += 1
        if dataR != [0.0] * 9:   
            successful_reads += 1

        # ゼロ点補正
        dataL[6:] = [dataL[i] - gyro_biasL[i-6] for i in range(6, 9)]
        dataR[6:] = [dataR[i] - gyro_biasR[i-6] for i in range(6, 9)]

        current_time = (time.perf_counter() - start_time) * 1000  # 経過時間（ミリ秒）

        # OSCで送信
        client.send_message("/raspi/L/accel", dataL[:3])
        client.send_message("/raspi/L/mag", dataL[3:6])
        client.send_message("/raspi/L/gyro", dataL[6:])
        client.send_message("/raspi/R/accel", dataR[:3])   
        client.send_message("/raspi/R/mag", dataR[3:6])
        client.send_message("/raspi/R/gyro", dataR[6:])
        client.send_message("/I2C/connection/L", 1 if sensorL else 0)
        client.send_message("/I2C/connection/R", 1 if sensorR else 0)
        client.send_message("/calibrating", isCalibrating)
        client.send_message("/current_timestamp", current_time)
        client.send_message("/playStatus", 1)

        # CSVにデータを書き込み
        with open(filename, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([current_time] + dataL + dataR)

        time.sleep(0.01)

# コマンドラインオプション処理
def handle_input():
    global isCalibrating
    while True:
        user_input = input("オプション: c: キャリブレーション, s: 成功率の表示: ")
        if user_input == 'c' and isCalibrating == 0:
            print("キャリブレーション開始...")
            calibrate_thread = threading.Thread(target=calibrate, args=(sensorL, 5))
            calibrate_thread.start()
        elif user_input == 's':
            success_rate = (successful_reads / total_attempts) * 100
            print(f"成功率: {success_rate:.2f}%")

# シグナルハンドラ
def signal_handler(sig, frame):
    print('Ctrl+Cが押されました。処理を終了前にこの処理を実行します。')
    client.send_message("/playStatus", 0)
    sys.exit(0)  # プログラムを終了

if __name__ == "__main__":
    input_thread = threading.Thread(target=handle_input)
    input_thread.start()
    main_loop()
