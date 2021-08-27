#!/usr/bin/env python3                                                                        # -*- coding: utf-8 -*-
import mysql.connector
import datetime
import os
import csv
import sys
import time
import configparser

UNIXTIME = int(time.time())
DATETIME = datetime.datetime.now().strftime("%Y/%m/%d_%H:%M") 
DATE     = datetime.datetime.now().strftime("%Y%m%d")

# configの読み込み
config_path = "./config.ini"
config = configparser.ConfigParser()
config.read(config_path, encoding='utf-8')

if config == None:
    print("先にconfig.iniを作成してください")
    print("必要なパラメータ:")
    print("[MySQL] user")
    print("[MySQL] password")
    print("[MySQL] host")
    print("[MySQL] database")
    print("[Path] CSV_DIR")
    sys.exit("1")

CSV_DIR=config["Path"]["CSV_DIR"]
CSV_PATH=CSV_DIR + DATE + "/"
os.system("mkdir -p " + CSV_PATH)
LATEST_TOTAL_CSV_PATH=CSV_PATH + "man10_server_loan_total.csv"
connection = None

loan_data = {}
total_borrow_amount = 0
total_borrow_amount_total_list = []
total_body += "<H3>ユーザー別ローン残高</H3><BR><BR>"

# DBからデータを読み出す
try:
    connection = mysql.connector.connect(
        user=config["MySQL"]["user"],
        password=config["MySQL"]["password"],
        host=config["MySQL"]["host"],
        database="man10_bank"
    )
    cursor = connection.cursor()
    # StatzのDBから、プレイヤー毎のローン残高（降順）を取得するSQL
    sql = ('''select player, borrow_amount from server_loan_tbl order by borrow_amount desc''')
    cursor.execute(sql)
    for player, borrow_amount in cursor:
        loan_data[player] = borrow_amount
        total_borrow_amount += borrow_amount
        # ローン残高がある場合は、グラフの下に書き込むユーザ別のリンクを作る
        if int(borrow_amount) > 0:
            total_body += "<LI><a href = \"{}.html\">{: >16s}</a>: {: >9,d}<br>".format(player, player, int(borrow_amount))

except Exception as e:
    print("[ERROR]: ", e)

finally:
    if connection and connection.is_connected():
        connection.close()


def output_html(output_path, name, label, data, body_str):
    # チャートのスタイル指定文字列
    chart_style_str = "#borrow_amount_line_chart {max-width:1920px;max-height:480px;}"
    # グラフ用のラベルリスト
    label_str = '"' + '","'.join(label) + '"'
    # グラフにする値のリスト
    data_str = ','.join(map(str,data))
    # y軸の最大値
    max_str = str(max(map(float,data)) * 1.2)
    

    print(label_str, data_str)

    # HTML出力
    html_template = '''
    <html>
    <head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    </head>

    <body>
    <style>
    {chart_style_str}
    </style>

    <canvas id="borrow_amount_line_chart"></canvas>

    <script>
    var ctx = document.getElementById('borrow_amount_line_chart');

    var data = {{
        labels: [{labels}],
        datasets: [{{
            label: '{name} borrow_amount transition',
            data: [{data}],
            borderColor: 'rgba(255, 100, 100, 1)'
        }}]
    }};

    var options = {{
        title: {{display: true, text:"{name} amount"}},
        scales: {{ y: {{suggestedMin: 0, suggestedMax: {max}}}}}
    }};

    var ex_chart = new Chart(ctx, {{
        type: 'line',
        data: data,
        options: options
    }});
    </script>

    {body_str}
    </body>
    </html>
    '''.format(name = name, chart_style_str = chart_style_str, labels = label_str, data = data_str, max = max_str, body_str = body_str)

    with open(output_path, "w") as f:
        f.write(html_template)
    

loan_data_count_history = {}
header = ""
total_data = ""
# 1つ前のCSVファイルをリネームしてから読み込み、今回MySQLから取得したデータを追記
if os.path.exists(LATEST_TOTAL_CSV_PATH):
    rename_filepath =  CSV_PATH + "man10_server_loan_total" + str(UNIXTIME) + ".csv"
    os.rename(LATEST_TOTAL_CSV_PATH, rename_filepath)
    with open(rename_filepath, "r") as f:
        csv_r = csv.reader(f, delimiter=",", doublequote=True, lineterminator="\r\n", quotechar='"', skipinitialspace=True)
        header = next(csv_r)
        header.append(DATETIME)
        total_data = next(csv_r)
        total_data.append(str(total_borrow_amount))            
    os.remove(rename_filepath)

# CSVファイルを作って保存
with open(LATEST_TOTAL_CSV_PATH, "w") as f:
    csv_w = csv.writer(f)
    if not header:
        header = [DATETIME]
    csv_w.writerow(header)
    csv_w.writerow(total_data)

# index 出力
output_html("./loan/index.html", "total", header, total_data, total_body)

for playername, value in loan_data.items():
    PLAYER_CSV_PATH=CSV_DIR + "/loan/" + playername + ".csv"
    header = []
    player_borrow_data = []

    if os.path.exists(PLAYER_CSV_PATH):
        rename_filepath =  PLAYER_CSV_PATH + str(UNIXTIME) + ".csv"
        os.rename(PLAYER_CSV_PATH, rename_filepath)
        with open(rename_filepath, "r") as f:
            csv_r = csv.reader(f, delimiter=",", doublequote=True, lineterminator="\r\n", quotechar='"', skipinitialspace=True)
            header = next(csv_r)
            player_borrow_data = next(csv_r)
            # 前回と値が異なる場合のみ追記する
            if player_borrow_data[-1] != str(loan_data[playername]):
                header.append(DATETIME)
                player_borrow_data.append(str(loan_data[playername])) 
        os.remove(rename_filepath)
    else:
        header = [DATETIME]
        player_borrow_data = [str(loan_data[playername])]

    # CSVファイルを作って保存
    with open(PLAYER_CSV_PATH, "w") as f:
        csv_w = csv.writer(f)
        csv_w.writerow(header)
        csv_w.writerow(player_borrow_data)


    output_html("./loan/" + playername + ".html", playername, header, player_borrow_data, "")