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
      print("[Webhook] man10")
      sys.exit("1")

CSV_DIR=config["Path"]["CSV_DIR"]
CSV_NAME="mbaltop_latest.csv"
# 今日の日付のYYMMDDHH
CSV_DATE= datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
# ランキングに表示する順位(10なら1～10位まで)
RANKING_NUM=config["Default"]["ranking_count"]
OUTPUT_FLAG="http"

# 引数で"print" を渡した場合はWebhookには送らずに結果をconsole出力する
if len(sys.argv) > 1:
  OUTPUT_FLAG=sys.argv[1]

CSV_PATH=CSV_DIR + "mbaltop/" + CSV_NAME

# CSVのデータを一時的に記録するdict
csv_dict = {}

# Discord出力用の文字列
result_str = "man10富豪ランキング(" + CSV_DATE + ")```\n"

# num1 とnum2を比較しておなじか上か下かを返す
def get_updown_mark(num1, num2):
    if num1 > num2:
        return "↓"
    elif num1 < num2:
        return "↑"
    elif num == num2:
        return "→"
    else:
        return ""
# numが0より上か下か同じかを返す
def get_updown_mark(num):
    if num < 0:
        return "↓"
    elif num > 0:
        return "↑"
    elif num == 0:
        return "→"
    else:
        return ""

# CSV読み込み
try:
    with open(CSV_PATH) as f:
        csv_r = csv.reader(f)
        for row in csv_r:
            if row[0] == "PlayerName":
                continue
            # row[0]は名前, row[1]は順位、row[2]は金額
            csv_dict[row[0]] = [int(row[1]), int(row[2])]

    os.rename(CSV_PATH, CSV_PATH.replace("latest", CSV_DATE))
except Exception as e:
    print("[ERROR]", e)

# MySQL読み込み
try:
    connection = mysql.connector.connect(
        user=config["MySQL"]["user"],
        password=config["MySQL"]["password"],
        host=config["MySQL"]["host"],
        database="man10_bank"
    )
    cursor = connection.cursor()
    sql = ('''SELECT player,total FROM estate_tbl order by total desc''')
    cursor.execute(sql)
    with open(CSV_PATH, "w") as f:
        csv_w = csv.writer(f)
        i = 1
        for player, total_money in cursor:
            csv_w.writerow([player, str(i), str(int(total_money))])
            
            # top10 を出力用の文字列に入れる
            if i <= 10:
                # CSVにプレイヤーが記録されていた場合（おはつでない場合）
                if player in csv_dict:
                    rank_updown_num = csv_dict[player][0] - i
                    rank_updown_mark = get_updown_mark(rank_updown_num)

                    money_updown_num = int(total_money - csv_dict[player][1])
                    money_updown_mark = get_updown_mark(money_updown_num)
                        
                    result_str += "{: >2d}位( {} {: >4d}) {: >16s} {: >12,d}( {} {: >12,d})\n".format(
                                     i,
                                     rank_updown_mark,
                                     rank_updown_num,
                                     player,
                                     int(total_money),
                                     money_updown_mark,
                                     money_updown_num) 
                else:
                    result_str += "{: 2d}位( - {: >4s}) {: >16s} {: >12,d}( - {: >12s})\n".format(
                                     i,
                                     "NEW",
                                     player,
                                     int(total_money),
                                     "NEW")
            i += 1
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
