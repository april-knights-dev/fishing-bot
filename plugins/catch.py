# coding: utf-8
from slack import WebClient

from slack.errors import SlackApiError

from psycopg2.extras import DictCursor
import os
import requests
import urllib.request as req
import json
import traceback
import sys
import random
import psycopg2

client = WebClient(token=os.getenv('SLACK_CLIENT_TOKEN'))


def get_connection():
    dsn = os.environ.get('DATABASE_URL')
    return psycopg2.connect(dsn)


def get_db_dict(sql):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute(sql)
            dictList = cur.fetchall()
    return dictList


def get_ranking_(sql):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute(sql)
            dictList = cur.fetchall()
    return dictList


def fish_catch(message):
    # お魚リストとってくるよ
    sql = "select * from fish_info ORDER BY rarity DESC;"
    d = get_db_dict(sql)
    # お魚一覧とってくるよ
    user_id = message.body['user']
    ts = message.body['ts']
    sql = "select * from fish_catch where angler_id ='" + \
        user_id + "' ORDER BY LENGTH(fish_id) ,fish_id"

    catch_dict = get_db_dict(sql)
    send_text = []

    for row in d:
        for catch_row in catch_dict:
            if catch_row.get('fish_id') == row.get('fish_id'):
                fish_name = row.get('fish_name')
                fish_icon = row.get('fish_icon')
                fish_rarity = str(row.get('rarity'))
                info_fish_min = str(row.get('min_length'))
                catch_fish_min = str(catch_row.get('min_length'))
                info_fish_max = str(row.get('max_length'))
                catch_fish_max = str(catch_row.get('max_length'))
                fish_count = str(catch_row.get('count'))

                if info_fish_min == catch_fish_min and info_fish_min != "None":
                    catch_fish_min = "👑" + catch_fish_min
                elif catch_fish_min == "None":
                    catch_fish_min = "はずれ"

                if info_fish_max == catch_fish_max and info_fish_max != "None":
                    catch_fish_max = "👑" + catch_fish_max
                elif catch_fish_max == "None":
                    catch_fish_max = "はずれ"

                send_text += [
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "image",
                                "image_url": f"{fish_icon}",
                                "alt_text": "icon"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*{fish_name}*" + "\n" +
                                        "レア度：" + fish_rarity + "　" +
                                        "釣った数：" + fish_count + "\n" +
                                        "最小サイズ：" + catch_fish_min + "　" +
                                        "最大サイズ：" + catch_fish_max
                            }
                        ]
                    }, ]

    try:
        client.chat_postMessage(
            channel=message.body['channel'],
            username='釣堀',
            blocks=send_text,
            thread_ts=ts,
            reply_broadcast=False
        )
    except Exception:
        traceback.print_exc()


def listen_ranking(message):
    # お魚一覧とってくるよ
    user_id = message.body['user']
    ts = message.body['ts']

    # 全メンバーのプロフィール取得
    response = client.users_list()
    users = response["members"]

    user_profile_dict = {}
    for user in users:
        user_profile_dict[user["id"]] = user["profile"]

    try:
        # 全期間自分の釣果
        sql = "select * from fish_catch where angler_id ='" + user_id + "';"
        fish_catch_dict = get_db_dict(sql)

        # 個人のトータルポイントを算出
        sql = "select total_point from angler_ranking where angler_id ='" + user_id + "';"
        total_point = get_db_dict(sql)

        # 全期間ランキング取得
        sql = "select * from angler_ranking ORDER BY total_point DESC LIMIT 10;"
        ranking_dict = get_db_dict(sql)

        send_text = get_send_text("全期間ランキング", ranking_dict, user_profile_dict,
                                  "total_point", total_point[0]["total_point"])

        client.chat_postMessage(
            channel=message.body['channel'],
            username='釣堀',
            blocks=send_text,
            thread_ts=ts,
            reply_broadcast=False
        )

        # personal weekly point
        sql = "select weekly_point from angler_ranking where angler_id ='" + user_id + "';"
        total_point = get_db_dict(sql)

        # get weekly ranking
        sql = "select * from angler_ranking ORDER BY weekly_point DESC LIMIT 10;"
        ranking_dict = get_db_dict(sql)

        send_text = get_send_text(
            "週間(月~日)ランキング", ranking_dict, user_profile_dict, "weekly_point", total_point[0]["weekly_point"])

        client.chat_postMessage(
            channel=message.body['channel'],
            username='釣堀',
            blocks=send_text,
            thread_ts=ts,
            reply_broadcast=False
        )

        # personal monthly point
        sql = "select monthly_point from angler_ranking where angler_id ='" + user_id + "';"
        total_point = get_db_dict(sql)

        # get monthly ranking
        sql = "select * from angler_ranking ORDER BY monthly_point DESC LIMIT 10;"
        ranking_dict = get_db_dict(sql)

        send_text = get_send_text(
            "月間ランキング", ranking_dict, user_profile_dict, "monthly_point", total_point[0]["monthly_point"])

        client.chat_postMessage(
            channel=message.body['channel'],
            username='釣堀',
            blocks=send_text,
            thread_ts=ts,
            reply_broadcast=False
        )
    except Exception:
        traceback.print_exc()


def fish_help(message):
    ts = message.body['ts']
    send_text = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "何が知りたいですか？"
            }
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Q:釣りがしたい。\nA:「釣り」と入力すると釣りができます。"
            },
            "accessory": {
                "type": "image",
                "image_url": "https://twemoji.maxcdn.com/v/13.0.1/72x72/1f3a3.png",
                "alt_text": "釣りコマンド"
            }
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Q:自分の釣った魚が見たい。\nA:「釣果」と入力すると釣った魚が見れます。"
            },
            "accessory": {
                "type": "image",
                "image_url": "https://twemoji.maxcdn.com/v/13.0.1/72x72/1f41f.png",
                "alt_text": "釣果コマンド"
            }
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Q:ランキングが見たい。\nA:「ランキング」と入力するとランキングが見れます。\n自分のポイントを確認することもできます。"
            },
            "accessory": {
                "type": "image",
                "image_url": "https://twemoji.maxcdn.com/v/13.0.1/72x72/1f3c6.png",
                "alt_text": "ランキングコマンド"
            }
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Q:魚のレア度って何？\nA:魚のレア度は希少性を表しています。\nレア度が低いとポイントは低いですが釣れやすくなります。\nレア度が高いとポイントが高いですが釣れにくくなります。"
            },
            "accessory": {
                "type": "image",
                "image_url": "https://twemoji.maxcdn.com/v/13.0.1/72x72/1f31f.png",
                "alt_text": "レア度の説明"
            }
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Q:サイズの横についてる金冠は何？\nA:金冠はその魚の最大または最小サイズを釣ると表示されます。\nモンスターハンターの討伐サイズの最大最小をイメージしてもらえるとわかりやすいです。\nわからない方はモンスターハンターをプレイしてください。"
            },
            "accessory": {
                "type": "image",
                "image_url": "https://twemoji.maxcdn.com/v/13.0.1/72x72/1f451.png",
                "alt_text": "レア度の説明"
            }
        }]

    try:
        client.chat_postMessage(
            channel=message.body['channel'],
            username='釣堀',
            blocks=send_text,
            thread_ts=ts,
            reply_broadcast=False
        )

    except AttributeError:
        traceback.print_exc()


def fish_help_cv_nozawa(message):
    ts = message.body['ts']
    send_text = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "おめぇは何が知りてぇんだ？"
            }
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Q:釣りがしてぇ。\nA:「釣り」っちゅうと魚が釣れっぞぉ。"
            },
            "accessory": {
                "type": "image",
                "image_url": "https://twemoji.maxcdn.com/v/13.0.1/72x72/1f3a3.png",
                "alt_text": "釣りコマンド"
            }
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Q:自分の釣った魚が見てぇ。\nA:「釣果」っちゅうと自分が釣った魚が見れっぞぉ。"
            },
            "accessory": {
                "type": "image",
                "image_url": "https://twemoji.maxcdn.com/v/13.0.1/72x72/1f41f.png",
                "alt_text": "釣果コマンド"
            }
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Q:つぇえ奴が見てぇ。\nA:「ランキング」っちゅうとつえぇ奴らがわかってわくわくすっぞぉ。\n自分の戦闘力も確認できっぞぉ。"
            },
            "accessory": {
                "type": "image",
                "image_url": "https://twemoji.maxcdn.com/v/13.0.1/72x72/1f3c6.png",
                "alt_text": "ランキングコマンド"
            }
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Q:魚のレア度ってなんだぁ？\nA:魚の希少性を現してっぞぉ。\nよぇえ奴を釣るとポイントがひきぃ。\nつぇえ奴を釣るとポイントがたけぇ。"
            },
            "accessory": {
                "type": "image",
                "image_url": "https://twemoji.maxcdn.com/v/13.0.1/72x72/1f31f.png",
                "alt_text": "レア度の説明"
            }
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Q:釣果についてる金冠はなんだぁ？\nA:金冠は魚のセイデェ、セイショウのセェズを釣ると釣果に表示されっぞぉ。\nモンステェーヘンテェーのテェバツセェズのセイデェ、セイショウをイメージすっとわかりやしぃぞぉ。\nわかんねぇやつはモンハンをいっちょやってみっかぁ！"
            },
            "accessory": {
                "type": "image",
                "image_url": "https://twemoji.maxcdn.com/v/13.0.1/72x72/1f451.png",
                "alt_text": "レア度の説明"
            }
        }]

    try:
        client.chat_postMessage(
            channel=message.body['channel'],
            username='釣堀',
            blocks=send_text,
            thread_ts=ts,
            reply_broadcast=False
        )

    except AttributeError:
        traceback.print_exc()


def get_send_text(title, ranking_dict, user_profile_dict, point_col_name, total_point):
    user_id_list = []
    total_point_list = []
    for row in ranking_dict:
        user_id_list.append(row.get('angler_id'))
        total_point_list.append(row.get(point_col_name))

    user_name_list = []
    for user_id in user_id_list:
        user_profile = user_profile_dict[user_id]

        if user_profile["display_name"] != "":
            angler_name = user_profile['display_name']
        else:
            angler_name = user_profile['real_name']

        user_name_list.append(angler_name)

    send_text = []
    send_text += [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{title}*"
            },
        },
    ]
    for count in range(0, len(user_name_list)):
        if count == 10:
            break

        if count == 0:
            send_text += [
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": str(count+1) + "位"
                        },
                        {
                            "type": "mrkdwn",
                            "text": user_name_list[count]
                        },
                        {
                            "type": "mrkdwn",
                            "text": str(total_point_list[count])
                        },
                        {
                            "type": "image",
                            "image_url": "https://twemoji.maxcdn.com/2/72x72/1f451.png",
                            "alt_text": "icon"
                        }
                    ]
                },
            ]
        else:
            send_text += [
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": str(count+1) + "位"
                        },
                        {
                            "type": "mrkdwn",
                            "text": user_name_list[count]
                        },
                        {
                            "type": "mrkdwn",
                            "text": str(total_point_list[count])
                        }
                    ]
                },
            ]

    send_text += [
        {
            "type": "context",
            "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "自分のトータルポイント: " + str(total_point)
                    }
            ]
        },
        {
            "type": "divider"
        },
    ]

    return send_text
