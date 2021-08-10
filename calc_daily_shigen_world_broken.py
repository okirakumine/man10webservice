#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
import csv
import requests
import json
import datetime
import mysql.connector
import configparser

config_path = "./config.ini"
config = configparser.ConfigParser()
config.read(config_path, encoding='utf-8')

if config == None:
      print("先にconfig.iniを作成してください")
      print("必要なパラメータ:")
      print("[Default] ranking_count")
      print("[Path] CSV_DIR")
      print("[MySQL] user")
      print("[MySQL] password")
      print("[MySQL] host")
      print("[Webhook] shigen")
      sys.exit("1")

CSV_DIR=config["Path"]["CSV_DIR"]
CSV_NAME="shigen_breaklog.csv"
# 今日の日付のYYMMDDHH
CSV_DATE= datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
# ランキングに表示する順位(10なら1～10位まで)
OUTPUT_FLAG="http"

# 引数で"print" を渡した場合はWebhookには送らずに結果をconsole出力する
if len(sys.argv) > 1:
  OUTPUT_FLAG=sys.argv[1]

CSV_PATH=CSV_DIR + "/shigen_breaklog/" + CSV_NAME

# CSVのデータを一時的に記録するdict
csv_dict = {}

# Discord出力用の文字列
result_str = "資源ワールド別破壊記録(" + CSV_DATE + ")```\n"

title_line = []
# CSV読み込み
try:
    with open(CSV_PATH) as f:
        csv_r = csv.reader(f)
        for row in csv_r:
            if row[0] == "NAME":
                title_line = row
                title_line.append(CSV_DATE)
            else:
                csv_dict[row[0]] = row

except Exception as e:
    print("[ERROR]", e)

# SQL実行関数
def get_broken_count(cursor, worldname):
    sql = ("select sum(value) from statz_blocks_broken where world=\"{}\"".format(worldname))
    cursor.execute(sql)
    return cursor.fetchone()[0]

try:
    result_str += "{: >13s}: {: >10s} (  {: >10s})\n".format("world_name", "total", "daily")
    connection = mysql.connector.connect(
        user=config["MySQL"]["user"],
        password=config["MySQL"]["password"],
        host=config["MySQL"]["host"],
        database="statz"
    )
    cursor = connection.cursor()
    shigen1_broken_count = get_broken_count(cursor, "shigen1")
    result_str += "{: >13s}: {: >10d} (+ {: >10d})\n".format(
                  "shigen1", 
                  int(shigen1_broken_count), 
                  int(shigen1_broken_count - int(csv_dict["shigen1"][-1])))
    csv_dict["shigen1"].append(shigen1_broken_count)

    shigen2_broken_count = get_broken_count(cursor, "shigen2")
    result_str += "{: >13s}: {: >10d} (+ {: >10d})\n".format("shigen2", int(shigen2_broken_count), int(shigen2_broken_count - int(csv_dict["shigen2"][-1])))
    csv_dict["shigen2"].append(shigen2_broken_count)

    shigen_nether_broken_count = get_broken_count(cursor, "shigen_nether")
    result_str += "{: >13s}: {: >10d} (+ {: >10d})\n".format("shigen_nether", int(shigen_nether_broken_count), int(shigen_nether_broken_count - int(csv_dict["shigen_nether"][-1])))
    csv_dict["shigen_nether"].append(shigen_nether_broken_count)

    with open(CSV_PATH, "w") as f:
        csv_w = csv.writer(f)
        csv_w.writerow(title_line)
        for worldname in csv_dict.keys():
            csv_w.writerow(csv_dict[worldname])
        
except Exception as e:
    print("[ERROR]: ", e)
    sys.exit(1)

result_str += "```\n"

# WebhookでDiscordに送る
if OUTPUT_FLAG=="http":
    # man10
    webhook_url = config["Webhook"]["man10"]
    # TEST用
    # webhook_url = config["Webhook"]["test"]
    content = {"content": result_str}
    headers = {"Content-Type": "application/json"}
    response = requests.post(webhook_url, json.dumps(content), headers=headers)
else:
    print(result_str)
