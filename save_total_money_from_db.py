#!/usr/bin/env python3                                                                        # -*- coding: utf-8 -*-
import sys
import mysql.connector
import datetime
import configparser

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

try:
    connection = mysql.connector.connect(
        user=config["MySQL"]["user"],
        password=config["MySQL"]["password"],
        host=config["MySQL"]["host"],
        database='man10_bank'
    )
    
    cursor = connection.cursor()
    sql = ('''SELECT total, date FROM server_estate_history''')

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


chart_style_str = "#total_money_line_chart {max-width:1920px;max-height:480px;}"
total_money_label_list_str = '"' + '","'.join(total_money_label_list) + '"'
total_money_total_list_str = ','.join(total_money_total_list)

html_template = '''
<html>
<head>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>

<body>
<style>
{chart_style_str}
</style>

<canvas id="total_money_line_chart"></canvas>

<script>
var ctx = document.getElementById('total_money_line_chart');

var data = {{
    labels: [{labels}],
    datasets: [{{
        label: 'man10 total money transition',
        data: [{total_data}],
        borderColor: 'rgba(255, 100, 100, 1)'
    }}]
}};

var options ={{}};

var ex_chart = new Chart(ctx, {{
    type: 'line',
    data: data,
    options: options
}});
</script>
</body>
</html>
'''.format(chart_style_str = chart_style_str, labels = total_money_label_list_str, total_data = total_money_total_list_str)

with open("./index.html", "w") as f:
    f.write(html_template)

print("total_money write success!", datetime.datetime.now()) 
