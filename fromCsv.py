import time
import csv
from pythonosc import udp_client
import sys

# コマンドラインから設定を取得
ip = sys.argv[1]
port = int(sys.argv[2])
csv_file_path = sys.argv[3]

client = udp_client.SimpleUDPClient(ip, port)

def read_csv_and_send_osc(csv_path):
    try:
        with open(csv_path, 'r') as file:
            reader = list(csv.reader(file))
            # next(reader)  # ヘッダー行をスキップ
            start_time = time.time()
            initial_timestamp = float(reader[1][0])  # 最初のデータ行のタイムスタンプ

            for row in reader[1:]:
                current_timestamp = float(row[0])
                elapsed_time_from_start = (current_timestamp - initial_timestamp) / 1000.0  # タイムスタンプ差を秒に変換
                while (time.time() - start_time) < elapsed_time_from_start:
                    time.sleep(0.006)  # 経過時間に達するまで待機

                # データの送信
                send_osc_data("/raspi/L/accel", row[1:4])
                send_osc_data("/raspi/L/mag", row[4:7])
                send_osc_data("/raspi/L/gyro", row[7:10])
                send_osc_data("/raspi/R/accel", row[10:13])
                send_osc_data("/raspi/R/mag", row[13:16])
                send_osc_data("/raspi/R/gyro", row[16:19])
                client.send_message("/filename", csv_file_path.split('/')[-1])
                client.send_message("/current_timestamp", current_timestamp)

    except FileNotFoundError:
        print(f"指定されたファイルが見つかりません: {csv_path}")
    except Exception as e:
        print(f"エラーが発生しました: {e}")

def send_osc_data(address, data):
    float_data = [float(d) for d in data]
    client.send_message(address, float_data)

read_csv_and_send_osc(csv_file_path)


