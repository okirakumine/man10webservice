#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import mysql.connector
import datetime
import configparser

# config読み込み
config_path = "./config.ini"
config = configparser.ConfigParser()
config.read(config_path, encoding='utf-8')

if config == None:
    print("先にconfig.iniを作成してください")
    print("必要なパラメータ:")
    print("[MySQL] user")
    print("[MySQL] password")
    print("[MySQL] host")
    sys.exit("1")

connection = None
total_money_label_list = []
total_money_total_list = []

# DBに問い合わせてserverのトータル金額の推移を得る
try:
    connection = mysql.connector.connect(
        user=config["MySQL"]["user"],
        password=config["MySQL"]["password"],
        host=config["MySQL"]["host"],
        database='man10_bank'
    )
    
    cursor = connection.cursor()
    sql = ('''SELECT total, date FROM server_estate_history''')
    # sql = ('''SELECT total, date FROM server_estate_history where date >= (NOW() - INTERVAL 3 MONTH)''')

    cursor.execute(sql)

    for total, date in cursor:
        total_money_label_list.append(date.strftime('%Y/%m/%d_%H:%M'))
        total_money_total_list.append(str(int(total)))

except Exception as e:
    print("[ERROR]: ", e)

finally:
    if connection and connection.is_connected():
        connection.close()
        print("close")

# チャートのスタイル指定文字列
total_chart_style_str = "#total_money_line_chart {max-width:1920px;max-height:480px;}"
last_month_chart_style_str = "#last_month_money_line_chart {max-width:1920px;max-height:480px;}"
# グラフ用のラベルリスト
total_money_label_list_str = '"' + '","'.join(total_money_label_list) + '"'
last_month_money_label_list_str = '"' + '","'.join(total_money_label_list[-30*24:]) + '"'
# グラフにする値のリスト
total_money_total_list_str = ','.join(total_money_total_list)
last_month_money_total_list_str = ','.join(total_money_total_list[-30*24:])

# HTML出力
html_template = '''
<html>
<head>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>

<body>
<style>
{total_chart_style_str}
</style>
<canvas id="total_money_line_chart"></canvas>

<br>

<style>
{last_month_chart_style_str}
</style>
<canvas id="last_month_money_line_chart"></canvas>

<script>
var ctxa = document.getElementById('total_money_line_chart');
var ctxm = document.getElementById('last_month_money_line_chart');

var total_data = {{
    labels: [{total_labels}],
    datasets: [{{
        label: 'man10 total money transition',
        data: [{total_data}],
        borderColor: 'rgba(255, 100, 100, 1)'
    }}]
}};

var last_month_data = {{
    labels: [{last_month_labels}],
    datasets: [{{
        label: 'man10 last month money transition',
        data: [{last_month_data}],
        borderColor: 'rgba(100, 100, 255, 1)'
    }}]
}};

var options ={{}};

var ex_chart = new Chart(ctxa, {{
    type: 'line',
    data: total_data,
    options: options
}});

var ex_chart = new Chart(ctxm, {{
    type: 'line',
    data: last_month_data,
    options: options
}});

</script>
</body>
</html>
'''.format(total_chart_style_str = total_chart_style_str, last_month_chart_style_str = last_month_chart_style_str, total_labels = total_money_label_list_str, last_month_labels = last_month_money_label_list_str, total_data = total_money_total_list_str, last_month_data = last_month_money_total_list_str)
with open("./index.html", "w") as f:
    f.write(html_template)

print("total_money write success!", datetime.datetime.now()) 
