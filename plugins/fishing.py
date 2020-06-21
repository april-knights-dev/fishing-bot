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

@listen_to('^釣りテスト$')
def test_fishing(message):

    l_fishinfo = selectFishInfoAll(dbname)
    l_weights = selectWeigths(dbname)
    l = []
    w = []

    # fish_idリスト作成
    l_fishid = [d.get('fish_id') for d in l_fishinfo]

    for fishid in l_fishid:
        resultMessage = fishing(fishid, l_fishinfo, user_id = message.body['user'])

    message.send('全種類登録完了')

@listen_to('^釣り$')
def listen_fishing(message):

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

    resultMessage = fishing(ret_fishid, l_fishinfo, user_id = message.body['user'])

    message.reply(resultMessage)

def fishing(ret_fishid, l_fishinfo, user_id):

    # fish_idから行を取得
    fish = ""
    for row in l_fishinfo:
        if row.get('fish_id') == ret_fishid:
            fishInfo = row

    # 体長を範囲内でランダム生成
    flen = 0
    if fishInfo.get('min_length') != None:
        flen = random.randint(fishInfo.get('min_length'),  fishInfo.get('max_length'))
        result = fishInfo.get('fish_name') + fishInfo.get('fish_icon') + \
                '(レア度' + str(fishInfo.get('rarity')) + ', 体長 ' + str(flen) + 'cm):' + fishInfo.get('comment') 
    else:
        result = fishInfo.get('fish_name') + fishInfo.get('fish_icon') + \
                '(レア度' + str(fishInfo.get('rarity')) + '):' + fishInfo.get('comment') 

    # 釣果を検索
    # 検索条件    
    l_catch_list = selectCatch(dbname, fishInfo, user_id)

    if len(l_catch_list)==0:
        # まだ釣ってなかったら登録
        insertFishCatch(dbname, fishInfo, user_id, flen)
    else:
        # 既に釣ってたら最小最長cm、釣った数、ポイントを更新
        dict_catch = l_catch_list[0]
        before_count = dict_catch.get('count')
        before_point = dict_catch.get('point')
        catch_min = dict_catch.get('min_length')
        catch_max = dict_catch.get('max_length')
        min_length = None
        max_length = None

        if fishInfo.get('min_length') != None:
            if flen < catch_min:
                min_length = flen
            else:
                min_length = catch_min
            if flen > catch_max:
                max_length = flen
            else:
                max_length = catch_max
        else:
            min_length = None
            min_length = None
        updateFishCatch(dbname, fishInfo, user_id, min_length, max_length, before_count, before_point)

    return str(result)

@listen_to('^底びき網漁$')
def fishingAll(message):
 
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

    for num in range(100):
        ret = random.choices(l_fishid, weights=w)
        ret_fishid = ret[0]
        resultMessage = fishing(ret_fishid, l_fishinfo, user_id = message.body['user'])

    message.send('100匹釣ったで')
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

def selectCatch(dbName, fishInfo, userId):
    conn = sqlite3.connect(dbName)
    # row_factoryの変更(dict_factoryに変更)
    conn.row_factory = dict_factory

    c = conn.cursor()

    sql = "select * from fish_catch where fish_id =? and angler_id=?"
    c.execute(sql, [fishInfo.get('fish_id'), userId])

    resultList = c.fetchall()

    c.close()
    conn.close()

    return resultList

def insertFishCatch(dbName, fishInfo, userId, length):
    conn = sqlite3.connect(dbName)
    c = conn.cursor()
    try:

        sql = "INSERT INTO fish_catch (fish_id, angler_id, min_length, max_length, count, point) VALUES (?, ?, ?, ?, ?, ?)"
        # 1匹につきレア度に応じて以下のポイントを付与
        # 1 ** 5 = 1
        # 2 ** 5 = 32
        # 3 ** 5 = 243
        # 4 ** 5 = 1024
        # 5 ** 5 = 3125
        rarity = fishInfo.get('rarity') 
        if rarity <= 5:
            point = rarity ** 5
        else:
            point = rarity * 2

        c.execute(sql, 
            [fishInfo.get('fish_id'), userId, length, length, 1, point])
        c.close()

    except sqlite3.IntegrityError as e:
        print(e)
        
    conn.commit()
    conn.close()

def updateFishCatch(dbName, fishInfo, userId, min_length, max_length, before_count, before_point):
    conn = sqlite3.connect(dbName)
    # row_factoryの変更(dict_factoryに変更)
    c = conn.cursor()
    try:

        sql = "UPDATE fish_catch SET min_length=?, max_length=?, count=?, point=? where fish_id=? and angler_id=?"
        count = before_count + 1
        # 1匹につきレア度に応じて以下のポイントを付与
        # 1 ** 5 = 1
        # 2 ** 5 = 32
        # 3 ** 5 = 243
        # 4 ** 5 = 1024
        # 5 ** 5 = 3125
        rarity = fishInfo.get('rarity') 
        if rarity <= 5:
            point = count * (fishInfo.get('rarity') ** 5)
        else:
            point = count * (fishInfo.get('rarity') * 2)

        c.execute(sql, 
            [min_length, max_length, count, point, fishInfo.get('fish_id'), userId])
        c.close()

    except sqlite3.IntegrityError as e:
        print(e)
        
    conn.commit()
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
