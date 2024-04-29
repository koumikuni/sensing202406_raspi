import time
import board
import adafruit_lsm9ds1
from pythonosc import udp_client

# ポート番号のリスト
ports = [11001, 11002, 11003, 11004, 11005]

# このラズパイが使用するポート番号
port_index = 0  # 0から始まるインデックスで指定
port = ports[port_index]

# OSCクライアントをセットアップ
ip = "192.168.10.112"  # 送信先のIPアドレス
client = udp_client.SimpleUDPClient(ip, port)

# I2C接続を初期化
i2c = board.I2C()  # SCL, SDAに接続

# センサー初期化を試みる関数
def try_init_sensor(xg_address, mag_address):
    try:
        return adafruit_lsm9ds1.LSM9DS1_I2C(i2c, mag_address=mag_address, xg_address=xg_address)
    except ValueError:
        print(f"センサーアドレス {xg_address}/{mag_address} が見つかりませんでした。")
        return None

# センサーオブジェクトの初期化
sensor1 = try_init_sensor(0x6A, 0x1C)
sensor2 = try_init_sensor(0x6B, 0x1E)

# スケールを選択（見つかったセンサーのみ）
for sensor in [sensor1, sensor2]:
    if sensor is not None:
        sensor.accel_range = adafruit_lsm9ds1.ACCELRANGE_4G
        sensor.mag_gain = adafruit_lsm9ds1.MAGGAIN_12GAUSS
        sensor.gyro_scale = adafruit_lsm9ds1.GYROSCALE_500DPS

def read_sensor_data(sensor):
    if sensor is None:
        return (0.0, 0.0, 0.0), (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)
    accel_x, accel_y, accel_z = sensor.acceleration
    mag_x, mag_y, mag_z = sensor.magnetic
    gyro_x, gyro_y, gyro_z = sensor.gyro
    return (accel_x, accel_y, accel_z), (mag_x, mag_y, mag_z), (gyro_x, gyro_y, gyro_z)

while True:
    # センサー1のデータ読み取りと送信
    accel1, mag1, gyro1 = read_sensor_data(sensor1)
    client.send_message("/raspi/1/accel", accel1)
    client.send_message("/raspi/1/mag", mag1)
    client.send_message("/raspi/1/gyro", gyro1)

    # センサー2のデータ読み取りと送信
    accel2, mag2, gyro2 = read_sensor_data(sensor2)
    client.send_message("/raspi/2/accel", accel2)
    client.send_message("/raspi/2/mag", mag2)
    client.send_message("/raspi/2/gyro", gyro2)

    # データ表示と送信ポートの確認
    print(f'ポート {port}: センサー1 - 加速度: X={accel1[0]:.2f}, Y={accel1[1]:.2f}, Z={accel1[2]:.2f}, 磁気: X={mag1[0]:.2f}, Y={mag1[1]:.2f}, Z={mag1[2]:.2f}, ジャイロ: X={gyro1[0]:.2f}, Y={gyro1[1]:.2f}, Z={gyro1[2]:.2f}')
    print(f'ポート {port}: センサー2 - 加速度: X={accel2[0]:.2f}, Y={accel2[1]:.2f}, Z={accel2[2]:.2f}, 磁気: X={mag2[0]:.2f}, Y={mag2[1]:.2f}, Z={mag2[2]:.2f}, ジャイロ: X={gyro2[0]:.2f}, Y={gyro2[1]:.2f}, Z={gyro2[2]:.2f}')

    time.sleep(0.01)
