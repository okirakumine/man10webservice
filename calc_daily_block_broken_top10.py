#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
import csv
import requests
import json
import datetime
import configparser

config_path = os.path.dirname(__file__) + "/config.ini"
config = configparser.ConfigParser()
config.read(config_path, encoding='utf-8')

if config == None:
    print("先にconfig.iniを作成してください")
    print("必要なパラメータ:")
    print("[Default] ranking_count")
    print("[Path] CSV_DIR")
    print("[Webhook] shigen")
    sys.exit("1")

CSV_DIR=config["Path"]["CSV_DIR"]
CSV_NAME="block_break_latest.csv"
# 今日の日付のYYMMDD
CSV_DATE= datetime.datetime.now().strftime("%Y%m%d")
# ランキングに表示する順位(10なら1～10位まで)
RANKING_COUNT=int(config["Default"]["ranking_count"])
OUTPUT_FLAG="http"

# 引数で日付(YYMMDD)を与えてもOK
if len(sys.argv) > 1:
    CSV_DATE=sys.argv[1]

if len(sys.argv) > 2:
    OUTPUT_FLAG=sys.argv[2]

CSV_PATH=CSV_DIR + CSV_DATE + "/" + CSV_NAME

# CSVからデータを一時格納する辞書
daily_list = {}

# CSV読み込み
with open(CSV_PATH) as f:
    csv_r = csv.reader(f)
    for row in csv_r:
        if row[0] == "PlayerName":
             continue
        # row[0]は名前, row[-1]は一番最後の数値、row[1]は一番最初の数値。ひき算して採掘数が出る
        daily_list[row[0]] = int(row[-1]) - int(row[1])

# 採掘数の多い順でソート
daily_list_sorted = sorted(daily_list.items(), key=lambda x:x[1], reverse=True)

# Discord出力用の文字列
result_str = "資源デイリー採掘数ランキング(" + CSV_DATE + ")```\n"
for i in range(RANKING_COUNT):
    # 順位データを整形出力
    result_str += "{: >2d}位: {: >16s} {: >10d}\n".format(i+1, daily_list_sorted[i][0], daily_list_sorted[i][1])
result_str += "```\n"

# WebhookでDiscordに送る
if OUTPUT_FLAG=="http":
    # shigen のWebhookアドレス
    webhook_url = config["webhook"]["shigen"]
    content = {"content": result_str}
    headers = {"Content-Type": "application/json"}
    response = requests.post(webhook_url, json.dumps(content), headers=headers)
else:
    print(result_str)
