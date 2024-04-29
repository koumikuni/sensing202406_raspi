import time
import board
import adafruit_lsm9ds1
from pythonosc import udp_client
import os

# ポート番号のリスト
ports = [11001, 11002, 11003, 11004, 11005]

# ラズパイのルートディレクトリに「raspi_id.txt」ファイルを用意して、その中にそのラズパイが何番目のラズパイかを０〜４の数字半角で書いておく。
try:
    with open(os.path.expanduser('~/raspi_id.txt'), 'r') as file:
        port_index = int(file.read().strip())  # Strip is used to remove any whitespace and newline characters
        # Ensure the port_index is within the valid range
        if port_index not in range(5):
            raise ValueError("ラズパイの番号を0~4番目で「raspi_id.txt」に記入してや！")
except (FileNotFoundError, ValueError) as e:
    print(f"ポート番号の指定のエラーやで。とりあえず0番目ってことにしとくわ: {e}")
    port_index = 0  # Default to 0 if there's an error

# このラズベリーパイが使用するポート番号
port = ports[port_index]

# OSCクライアントの設定
ip = "192.168.10.112"  # 送信先のIPアドレス
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

# センサーデータの読み取り関数
def read_sensor_data(sensor):
    if sensor is None:
        return (0.0, 0.0, 0.0), (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)
    accel_x, accel_y, accel_z = sensor.acceleration
    mag_x, mag_y, mag_z = sensor.magnetic
    gyro_x, gyro_y, gyro_z = sensor.gyro
    return (accel_x, accel_y, accel_z), (mag_x, mag_y, mag_z), (gyro_x, gyro_y, gyro_z)

while True:
    # センサーLからのデータ読み取りと送信
    accelL, magL, gyroL = read_sensor_data(sensorL)
    client.send_message("/raspi/L/accel", accelL)
    client.send_message("/raspi/L/mag", magL)
    client.send_message("/raspi/L/gyro", gyroL)

    # センサーRからのデータ読み取りと送信
    accelR, magR, gyroR = read_sensor_data(sensorR)
    client.send_message("/raspi/R/accel", accelR)
    client.send_message("/raspi/R/mag", magR)
    client.send_message("/raspi/R/gyro", gyroR)

    # データの表示と送信ポートの確認
    print(f'送信先ipアドレス:{ip}')
    print(f'ポート {port}: センサーL - 加速度: X={accelL[0]:.2f}, Y={accelL[1]:.2f}, Z={accelL[2]:.2f}, 磁気: X={magL[0]:.2f}, Y={magL[1]:.2f}, Z={magL[2]:.2f}, ジャイロ: X={gyroL[0]:.2f}, Y={gyroL[1]:.2f}, Z={gyroL[2]:.2f}')
    print(f'ポート {port}: センサーR - 加速度: X={accelR[0]:.2f}, Y={accelR[1]:.2f}, Z={accelR[2]:.2f}, 磁気: X={magR[0]:.2f}, Y={magR[1]:.2f}, Z={magR[2]:.2f}, ジャイロ: X={gyroR[0]:.2f}, Y={gyroR[1]:.2f}, Z={gyroR[2]:.2f}')

    time.sleep(0.01)
