# coding: utf-8

from slack import WebClient
from slack.errors import SlackApiError
from slackbot.bot import respond_to     # @botname: で反応するデコーダ
from slackbot.bot import listen_to      # チャネル内発言で反応するデコーダ
from slackbot.bot import default_reply  # 該当する応答がない場合に反応するデコーダ
from psycopg2.extras import DictCursor  # 辞書形式で取得するやつ
import os
import requests
import urllib.request as req
import json
import sys
import random
import psycopg2

client = WebClient(token=os.getenv('SLACK_CLIENT_TOKEN'))

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

    l_fishinfo = selectFishInfoAll()
    l_weights = selectWeigths()
    l = []
    w = []

    # fish_idリスト作成
    l_fishid = [d.get('fish_id') for d in l_fishinfo]

    for fishid in l_fishid:
        resultMessage = fishing(
            fishid, l_fishinfo, user_id=message.body['user'])

    message.send('全種類登録完了')


@listen_to('^釣り$')
def listen_fishing(message):

    l_fishinfo = selectFishInfoAll()
    l_weights = selectWeigths()
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

    result_dict = fishing(ret_fishid, l_fishinfo,
                          user_id=message.body['user'])

    section_text = ""
    if "length" in result_dict:
        section_text = f"*{result_dict['fish_name']}*\nレア度：{result_dict['star']}\nポイント：{result_dict['point']} pt\n体長：{result_dict['length']} cm \nコメント：{result_dict['comment']}"
    else:
        section_text = f"*{result_dict['fish_name']}*\nレア度：{result_dict['star']}\nポイント：{result_dict['point']} pt\nコメント：{result_dict['comment']}"

    angler_name = ""
    user_profile = client.users_profile_get(
        user=message.body['user'])['profile']
    if user_profile["display_name"] != "":
        angler_name = user_profile['display_name']
    else:
        angler_name = user_profile['real_name']

    client.chat_postMessage(
        channel=message.body['channel'],
        username='釣堀',
        blocks=[
            {
                "type": "section",
                "text": {
                        "type": "mrkdwn",
                        "text": angler_name + "が釣ったのは…"
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                        "type": "mrkdwn",
                        "text": section_text
                },
                "accessory": {
                    "type": "image",
                    "image_url": f"{result_dict['fish_icon']}",
                    "alt_text": "Twitter, Inc."
                }
            },
            {
                "type": "divider"
            }
        ]
    )


def fishing(ret_fishid, l_fishinfo, user_id):

    # fish_idから行を取得
    fish = ""
    for row in l_fishinfo:
        if row.get('fish_id') == ret_fishid:
            fishInfo = row

    result_dict = {}
    result_dict['fish_name'] = fishInfo.get('fish_name')
    result_dict['fish_icon'] = fishInfo.get('fish_icon')
    result_dict['comment'] = fishInfo.get('comment')

    # 体長を範囲内でランダム生成
    flen = 0
    if fishInfo.get('min_length') != None:
        flen = random.randint(fishInfo.get('min_length'),
                              fishInfo.get('max_length'))
        result_dict['length'] = flen

    # レア度に応じて★
    star = ""
    for num in range(fishInfo.get('rarity')):
        star += "⭐"

    result_dict['star'] = star

    # 釣果を検索
    # 検索条件
    l_catch_list = selectCatch(fishInfo, user_id)

    if len(l_catch_list) == 0:
        # まだ釣ってなかったら登録
        insertFishCatch(fishInfo, user_id, flen)
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
        updateFishCatch(fishInfo, user_id, min_length,
                        max_length, before_count, before_point)

    result_dict['point'] = calc_point(fishInfo.get('rarity'))

    return result_dict


@listen_to('^底びき網漁$')
def fishingAll(message):

    l_fishinfo = selectFishInfoAll()
    l_weights = selectWeigths()
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
        resultMessage = fishing(ret_fishid, l_fishinfo,
                                user_id=message.body['user'])

    message.send('100匹釣ったで')


def selectFishInfoAll():
    with get_connection() as conn:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("select * from fish_info")
            dictList = cur.fetchall()

    return dictList


def selectWeigths():
    with get_connection() as conn:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("select * from weights")
            dictList = cur.fetchall()

    return dictList


def selectCatch(fishInfo, userId):

    sql = "select * from fish_catch where fish_id =%s and angler_id=%s"

    with get_connection() as conn:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute(sql, [fishInfo.get('fish_id'), userId])
            dictList = cur.fetchall()

    return dictList


def insertFishCatch(fishInfo, userId, length):
    try:
        sql = "INSERT INTO fish_catch (fish_id, angler_id, min_length, max_length, count, point) VALUES (%s, %s, %s, %s, %s, %s)"
        rarity = fishInfo.get('rarity')
        point = calc_point(rarity)
        with get_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute(sql, [fishInfo.get('fish_id'),
                                  userId, length, length, 1, point])
                conn.commit()

    except psycopg2.Error as e:
        print(e)


def updateFishCatch(fishInfo, userId, min_length, max_length, before_count, before_point):
    try:
        sql = "UPDATE fish_catch SET min_length=%s, max_length=%s, count=%s, point=%s where fish_id=%s and angler_id=%s"
        count = before_count + 1
        rarity = fishInfo.get('rarity')
        point = calc_point(rarity)

        with get_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute(sql,
                            [min_length, max_length, count, point, fishInfo.get('fish_id'), userId])
                conn.commit()

    except psycopg2.Error as e:
        print(e)

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


def get_connection():
    dsn = os.getenv('DATABASE_URL')
    return psycopg2.connect(dsn)


def calc_point(rarity):
    # 1匹につきレア度に応じて以下のポイントを付与
    # 1 ** 5 = 1
    # 2 ** 5 = 32
    # 3 ** 5 = 243
    # 4 ** 5 = 1024
    # 5 ** 5 = 3125
    if rarity <= 5:
        point = rarity ** 5
    else:
        point = rarity * 2
    return point
