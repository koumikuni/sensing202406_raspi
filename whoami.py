import smbus
import time

# I2Cバスを初期化（Raspberry Piの場合、通常は1）
bus = smbus.SMBus(1)

# センサーのI2Cアドレス
sensor_address = 0x6A  # 加速度・ジャイロスコープのアドレス
who_am_i_register = 0x0F
expected_who_am_i = 0x68  # LSM9DS1の場合

# WHO_AM_I レジスターからデータを読み出す
try:
    who_am_i = bus.read_byte_data(sensor_address, who_am_i_register)
    print(f"Read WHO_AM_I: {who_am_i:#02x}")

    # 期待される値と比較
    if who_am_i == expected_who_am_i:
        print("Sensor is responding correctly.")
    else:
        print("Sensor is not responding correctly. Check wiring and sensor address.")

except Exception as e:
    print(f"Failed to read from sensor: {e}")

# I2Cバスをクローズ
bus.close()
