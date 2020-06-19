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

client = WebClient(token=os.getenv('SLACK_API_TOKEN'))

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

# 釣りコマンド拾うのはslackbotじゃなくてRTMClientを使えばできるっぽい

@listen_to('^釣り$')
def fishing(message):

    dbname = './db/fishing_test.db'
    resultList = selectFishInfoAll(dbname)
    l = []
    w = []

    # 名前＋絵文字とコメントリスト取得
    for row in resultList:
        fish = row.get('fish_name') + row.get('fish_icon') + ':' + row.get('comment') 
        l.append(fish)

    # レア度リスト取得
    for row in resultList:
        rarity = row.get('rarity')
        if is_int(rarity):
            w.append(rarity)
        else:
            w.append(10)

    ret = random.choices(l, weights=w)

    print(ret)
    message.send(str(ret))


@listen_to('^底びき網漁$')
def fishingAll(message):
 
    # json_dict = json.loads(block_kit)
    # print('json_dict:{}'.format(json_dict['blocks']['text']['type']))

    fish_count = {'アジ': 0, 'ヒラメ': 0, 'ハマチ': 0, 'ジンベエザメ': 0, '平田': 0}
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
