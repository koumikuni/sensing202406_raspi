import time
import csv
from pythonosc import udp_client
import sys
import signal

# コマンドラインから設定を取得
ip = sys.argv[1]
port = int(sys.argv[2])
csv_file_path = sys.argv[3]

client = udp_client.SimpleUDPClient(ip, port)

def signal_handler(sig, frame):
    print('Ctrl+Cが押されました。処理を終了前にこの処理を実行します。')
    # 必要な処理をここに追加
    client.send_message("/playStatus", 0)
    exit(0)  # プログラムを終了

# シグナルハンドラを設定
signal.signal(signal.SIGINT, signal_handler)

def read_csv_and_send_osc(csv_path):
    try:
        with open(csv_path, 'r') as file:
            reader = list(csv.reader(file))
            # next(reader)  # ヘッダー行をスキップ
            start_time = time.time()
            initial_timestamp = float(reader[1][0])  # 最初のデータ行のタイムスタンプ
            client.send_message("/playStatus", 0)

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
                client.send_message("/playStatus", 1)
            client.send_message("/playStatus", 0)

    except FileNotFoundError:
        print(f"指定されたファイルが見つかりません: {csv_path}")
        client.send_message("/playStatus", 0)
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        client.send_message("/playStatus", 0)

def send_osc_data(address, data):
    float_data = [float(d) for d in data]
    client.send_message(address, float_data)

read_csv_and_send_osc(csv_file_path)


