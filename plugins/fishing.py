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
import sys
import random
import psycopg2
import datetime
import math

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


@listen_to('^釣り$')
def listen_fishing(message):

    l_fishinfo = selectFishInfoAll()
    l_weights = selectWeigths()
    l_rarity = select_rarity()
    l = []
    w = []
    # 朝と夜で２つ作る必要あり
    bonus_time_increase_rate = os.getenv('BONUS_TIME_INCREASE_RATE')
    bonus_time_reduced_rate = os.getenv('BONUS_TIME_REDUCED_RATE')
    bonus_start_HHmmss_1 = os.getenv('BONUS_START_TIME_1')
    bonus_end_HHmmss_1 = os.getenv('BONUS_END_TIME_1')
    bonus_start_HHmmss_2 = os.getenv('BONUS_START_TIME_2')
    bonus_end_HHmmss_2 = os.getenv('BONUS_END_TIME_2')
    ts = message.body['ts']
    message_HHmmss = datetime.datetime.fromtimestamp(
        math.floor(float(ts))).strftime('%H:%M')
    isBonusTime = False

    # fish_idリスト作成
    l_fishid = [d.get('fish_id') for d in l_fishinfo]

    bonus_message = None

    if bonus_start_HHmmss_1 <= message_HHmmss <= bonus_end_HHmmss_1:
        bonus_message = bonus_start_HHmmss_1 + '～' + \
            bonus_end_HHmmss_1 + 'までレア度４以上が' + bonus_time_increase_rate + 'べえだ！' + \
            'リモート勤務のやつはきんてぇ連絡出したか？'
        isBonusTime = True
    elif bonus_start_HHmmss_2 <= message_HHmmss <= bonus_end_HHmmss_2:
        bonus_message = bonus_start_HHmmss_2 + '～' + \
            bonus_end_HHmmss_2 + 'までレア度４以上が' + bonus_time_increase_rate + 'べえだ！' + \
            '日報わすれっなよ！'
        isBonusTime = True

    if isBonusTime:
        client.chat_postMessage(
            channel=message.body['channel'],
            username='釣堀',
            text=bonus_message)

    # レア度を％に変換する
    for row_w in l_weights:
        if isBonusTime and 4 <= row_w.get('rarity'):
            w.append(row_w.get('weights')*int(bonus_time_increase_rate))
        elif isBonusTime and 1 == row_w.get('rarity'):
            w.append(row_w.get('weights')/int(bonus_time_reduced_rate))
        else:
            w.append(row_w.get('weights'))

    # レア度をどれにするか重み付けありでチョイス
    ret = random.choices(l_rarity, weights=w)
    # チョイスされたレア度のfish_idを抽出
    target_fishlist = select_fishinfo_filtered_rarity(ret)
    # レア度が同じfish_idからランダムで１つ選択
    ret_fishid = target_fishlist[random.randrange(
        len(target_fishlist))].get('fish_id')
    # 釣果登録更新
    fishing_return_list = []
    fishing_return_list = fishing(ret_fishid, l_fishinfo,
                                  user_id=message.body['user'])

    result_dict = fishing_return_list[0]
    update_code = fishing_return_list[1]
    before_length = fishing_return_list[2]

    # ランキングにポイント加算
    upsert_ranking(user_id=message.body['user'], point=result_dict['point'])

    section_text = ""
    if "length" in result_dict:
        length_text = get_length_text(result_dict, update_code, before_length)
        section_text = f"*{result_dict['fish_name']}*\nレア度：{result_dict['star']}\n" \
            f"ポイント：{result_dict['point']} pt\n体長：{length_text}\nコメント：{result_dict['comment']}"
    else:
        section_text = f"*{result_dict['fish_name']}*\nレア度：{result_dict['star']}\n" \
            f"ポイント：{result_dict['point']} pt\nコメント：{result_dict['comment']}"

    angler_name = ""
    user_profile = client.users_profile_get(
        user=message.body['user'])['profile']

    # ニックネームがあればそっち表示
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
    # UPDATE-20200914-#23　最大最小判断時に必要なデータ　辞書の中身更新
    result_dict['info_min'] = fishInfo.get('min_length')
    result_dict['info_max'] = fishInfo.get('max_length')

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

    # ポイント設定
    if fishInfo.get('min_length') != None:
        result_dict['point'] = calc_point(fishInfo.get('rarity'))
    else:
        result_dict['point'] = 0

    # UPDATE-20200914-#24#25 最大、最小、新しく釣った魚を判定するためのリスト
    update_code = []
    # 前回釣った魚のサイズ
    before_length = None
    if len(l_catch_list) == 0:
        # UPDATE-20200914-#25 新しく釣ったフラグ
        update_code.append("new")

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
                # UPDATE-20200914-#24 最小を更新した
                update_code.append("min")
                before_length = catch_min
            else:
                min_length = catch_min
            if flen > catch_max:
                max_length = flen
                # UPDATE-20200914-#24 最大を更新した
                update_code.append("max")
                before_length = catch_max
            else:
                max_length = catch_max
        else:
            min_length = None
            min_length = None

        update_fish_catch(fishInfo, user_id, min_length,
                        max_length, before_count, result_dict['point'])

    return result_dict, update_code, before_length


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


def select_rarity():
    with get_connection() as conn:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("select rarity from weights")
            dictList = cur.fetchall()

    return dictList


def select_fishinfo_filtered_rarity(rarity):

    sql = "select * from fish_info where rarity =%s"
    with get_connection() as conn:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute(sql, rarity[0])
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


def update_fish_catch(fishInfo, userId, min_length, max_length, before_count, point):
    try:
        sql = "UPDATE fish_catch SET min_length=%s, max_length=%s, count=%s, point=%s where fish_id=%s and angler_id=%s"
        count = before_count + 1
        rarity = fishInfo.get('rarity')

        with get_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute(sql,
                            [min_length, max_length, count, point, fishInfo.get('fish_id'), userId])
                conn.commit()

    except psycopg2.Error as e:
        print(e)


def upsert_ranking(user_id, point):
    try:
        created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sql = "INSERT INTO angler_ranking(angler_id, total_point, weekly_point, monthly_point, created_at)"\
            f"VALUES('{user_id}',{point},{point},{point},'{created_at}')"\
            "ON CONFLICT (angler_id) DO UPDATE "\
            f"SET total_point = angler_ranking.total_point + {point}"\
            f", weekly_point = angler_ranking.weekly_point + {point}"\
            f", monthly_point = angler_ranking.monthly_point + {point}"

        with get_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute(sql, [point, user_id])
                conn.commit()
    except psycopg2.Error as e:
        print(e)


def get_length_text(result_dict, update_code, before_length):
    # 金冠　最大、最小　初めて釣ったか判定する
    length_text = str(result_dict['length']) + " cm"
    # UPDATE-20200914-#23 最大または最小を釣った場合👑をつける
    if result_dict['length'] != 0:
        if result_dict['info_min'] == result_dict['length'] or result_dict['info_max'] == result_dict['length']:
            length_text = "👑 " + length_text

    # UPDATE-20200914-#24 最大最小を更新した場合 UPを付与
    if True in [i in "min" for i in update_code]:
        length_text = str(before_length) + " -> " + \
            length_text + " :fishing-up-blue: 最小更新!!"
    elif True in [i in "max" for i in update_code]:
        length_text = str(before_length) + " -> " + \
            length_text + " :fishing-up: 最大更新!!"

    # UPDATE-20200914-#24 新しく釣った魚にnewを付与
    if True in [i in "new" for i in update_code]:
        result_dict['fish_name'] = result_dict['fish_name'] + " :new:"
    return length_text


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
