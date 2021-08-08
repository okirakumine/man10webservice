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

config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8')

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
LATEST_CSV_PATH=CSV_PATH + "block_break_latest.csv"
connection = None

print("----- block break log -----")

block_break_count = {}
try:
    connection = mysql.connector.connect(
        user=config["MySQL"]["user"],
        password=config["MySQL"]["password"],
        host=config["MySQL"]["host"],
        database=config["MySQL"]["database"]
    )
    cursor = connection.cursor()
    # StatzのDBから、プレイヤー毎の採掘数（降順）を取得するSQL
    sql = ('''select playerName, sum(value) from statz_blocks_broken inner join statz_players on statz_blocks_broken.uuid = statz_players.uuid group by playerName order by sum(value) desc''')
    
    cursor.execute(sql)

    for player, total in cursor:
        block_break_count[player] = total


except Exception as e:
    print("[ERROR]: ", e)

finally:
    if connection and connection.is_connected():
        connection.close()

block_break_count_history = {}
header = ""
# 1つ前のCSVファイルをリネームしてから読み込み、今回MySQLから取得したデータを追記
if os.path.exists(LATEST_CSV_PATH):
    rename_filepath =  CSV_PATH + "block_break_" + str(UNIXTIME) + ".csv"
    os.rename(LATEST_CSV_PATH, rename_filepath)
    with open(rename_filepath, "r") as f:
        csv_r = csv.reader(f, delimiter=",", doublequote=True, lineterminator="\r\n", quotechar='"', skipinitialspace=True)
        header = next(csv_r)
        header.append(DATETIME)
        for row in csv_r:
            playername = row.pop(0)
            block_break_count_history[playername] = [int(s) for s in row]
    os.remove(rename_filepath)
for playername, value in block_break_count.items():
    if not playername in block_break_count_history:
        block_break_count_history[playername] = [0] * (len(header) - 2) # -2: playername, latest value
        print("new_player:", playername)
    block_break_count_history[playername].append(int(block_break_count[playername])) # latest value

# CSVファイルを作って保存
with open(LATEST_CSV_PATH, "w") as f:
    csv_w = csv.writer(f)
    if not header:
        header = ["PlayerName", DATETIME]
    csv_w.writerow(header)
    for playername in block_break_count.keys():
        writedata = [playername] + block_break_count_history[playername]
        csv_w.writerow(writedata)

