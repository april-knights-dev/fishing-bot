# coding: utf-8

from slack import WebClient
from slack.errors import SlackApiError
from slackbot.bot import respond_to     # @botname: で反応するデコーダ
from slackbot.bot import listen_to      # チャネル内発言で反応するデコーダ
from slackbot.bot import default_reply  # 該当する応答がない場合に反応するデコーダ
import os
import requests
import urllib.request as req
import json
import sys
import random
import sqlite3

client = WebClient(token=os.getenv('SLACK_CLIENT_TOKEN'))
dbname = './db/fishing_test.db'

block_kit = {
            "blocks": [
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "plain_text",
                    "text": "This is a plain text section block.",
                    "emoji": 'true'
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "plain_text",
                        "text": "*this is plain_text text*",
                        "emoji": 'true'
                    },
                    {
                        "type": "plain_text",
                        "text": "*this is plain_text text*",
                        "emoji": 'true'
                    },
                    {
                        "type": "plain_text",
                        "text": "*this is plain_text text*",
                        "emoji": 'true'
                    },
                    {
                        "type": "plain_text",
                        "text": "*this is plain_text text*",
                        "emoji": 'true'
                    },
                    {
                        "type": "plain_text",
                        "text": "*this is plain_text text*",
                        "emoji": 'true'
                    }
                ]
            },
            {
                "type": "divider"
            }
        ]
    }

# @respond_to('string')     bot宛のメッセージ
#                           stringは正規表現が可能 「r'string'」
# @listen_to('string')      チャンネル内のbot宛以外の投稿
#                           @botname: では反応しないことに注意
#                           他の人へのメンションでは反応する
#                           正規表現可能
# @default_reply()          DEFAULT_REPLY と同じ働き
#                           正規表現を指定すると、他のデコーダにヒットせず、
#                           正規表現にマッチするときに反応
#                           ・・・なのだが、正規表現を指定するとエラーになる？

# message.reply('string')   @発言者名: string でメッセージを送信
# message.send('string')    string を送信
# message.react('icon_emoji')  発言者のメッセージにリアクション(スタンプ)する
#                               文字列中に':'はいらない

@listen_to('^釣り$')
def fishing(message):

    l_fishinfo = selectFishInfoAll(dbname)
    l_weights = selectWeigths(dbname)
    l = []
    w = []

    # fish_idリスト作成
    l_fishid = [d.get('fish_id') for d in l_fishinfo]

    # レア度リスト取得
    for row in l_fishinfo:
        rarity = row.get('rarity')
        # レア度を％に変換する
        for row_w in l_weights:
            if row_w.get('rarity') == rarity:
                w.append(row_w.get('weights'))

    ret = random.choices(l_fishid, weights=w)
    ret_fishid = ret[0]

    # fish_idから行を取得
    fish = ""
    for row in l_fishinfo:
        if row.get('fish_id') == ret_fishid:
            fish = row.get('fish_name') + row.get('fish_icon') + '(レア度' + str(row.get('rarity')) + '):' + row.get('comment') 

    message.send(str(fish))

    # 釣果を検索
    # 検索条件
    user_id = message.body['user']
    # 既に釣ってたら最小最長cm、釣った数、ポイントを更新
    # まだ釣ってなかったら登録

@listen_to('^底びき網漁$')
def fishingAll(message):
 
    resultList = selectFishInfoAll(dbname)
    weights = selectWeigths(dbname)
    l = []
    w = []

    for num in range(10000):
        ret = random.choices(l, weights=w)
        fish_count[ret[0]] = fish_count[ret[0]] + 1

    for k, v in fish_count.items():
        message.send(f"{k}は{v}匹\n")

    # # APIを使った投稿
    # client.chat_postMessage(
    #     channel='#tmp_bot放牧部屋',
    #     text="API使って送信テスト"
    # )

    # response = client.users_info(user='U011Q5G7685')
    # print(response)

    # client.chat_postMessage(
    #     channel='#tmp_bot放牧部屋',
    #     text=response['user']['real_name']
    # )

def selectFishInfoAll(dbName):
    conn = sqlite3.connect(dbName)
    # row_factoryの変更(dict_factoryに変更)
    conn.row_factory = dict_factory

    c = conn.cursor()

    sql = "select * from fish_info"
    c.execute(sql)

    resultList = c.fetchall()

    c.close()
    conn.close()

    return resultList

def selectWeigths(dbName):
    conn = sqlite3.connect(dbName)
    # row_factoryの変更(dict_factoryに変更)
    conn.row_factory = dict_factory

    c = conn.cursor()

    sql = "select * from weights"
    c.execute(sql)

    resultList = c.fetchall()

    c.close()
    conn.close()

    return resultList

def selectCatch(dbName, fishInfo, userInfo):
    conn = sqlite3.connect(dbName)
    # row_factoryの変更(dict_factoryに変更)
    conn.row_factory = dict_factory

    c = conn.cursor()

    sql = "select * from fish_catch where fish_id =? and angler_id=?"
    c.execute(sql, [fishInfo.get('fish_id'), userInfo('user')])

    resultList = c.fetchall()

    c.close()
    conn.close()

    return resultList

def insertFishCatch(dbName, fishInfo, userInfo):
    conn = sqlite3.connect(dbName)
    # row_factoryの変更(dict_factoryに変更)
    c = conn.cursor()

    sql = "INSERT INTO fish_catch (fish_id, angler_id, min_length, max_length, count, point) VALUES (?, ?, ?, ?, ?, ?);"
    c.execute(sql)

    resultList = c.fetchall()

    c.close()
    conn.close()

# dict_factoryの定義
def dict_factory(cursor, row):
   d = {}
   for idx, col in enumerate(cursor.description):
       d[col[0]] = row[idx]
   return d

def is_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

# fishing("")