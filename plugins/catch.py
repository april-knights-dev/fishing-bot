# coding: utf-8
from slack import WebClient

from slack.errors import SlackApiError
from slackbot.bot import respond_to     # @botname: で反応するデコーダ
from slackbot.bot import listen_to      # チャネル内発言で反応するデコーダ
from slackbot.bot import default_reply  # 該当する応答がない場合に反応するデコーダ

from psycopg2.extras import DictCursor
import os
import requests
import urllib.request as req
import json
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

def member(member_id_list):
    member_dict = {}
    user_list = []
    is_active_list = []

    for name_id in member_id_list:
        user_url = 'https://slack.com/api/users.info?token={0}&user={1}&pretty=1'.format(client, name_id)

        user_response = requests.get(user_url).json()

        user_list.append(user_name(user_response))

    return user_dict


@listen_to('^釣果$')
def fish_catch(message):
    #お魚リストとってくるよ
    sql = "select * from fish_info ORDER BY rarity DESC;"
    d = get_db_dict(sql)
    #お魚一覧とってくるよ
    user_id = message.body['user']
    ts = message.body['ts']
    sql = "select * from fish_catch where angler_id ='" + user_id + "' ORDER BY LENGTH(fish_id) ,fish_id"
    
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
                
                send_text +=[
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
                                        "レア度：" + fish_rarity  + "　" + 
                                        "釣った数：" + fish_count + "\n" + 
                                        "最小サイズ：" + catch_fish_min + "　" +
                                        "最大サイズ：" + catch_fish_max
                            }
                        ]
                    },]

    try:
        client.chat_postMessage(
            channel=message.body['channel'],
            username='釣堀',
            blocks = send_text,
            thread_ts = ts,
            reply_broadcast = False
        )
    except AttributeError:
        send_text = "まだ登録されてませんよ？"
        message.send(send_text)
    except SlackApiError as e:
        send_text = "まだ登録されてませんよ？"
        message.send(send_text)

@listen_to('^ランキング$')
def fish_catch(message):
    #お魚一覧とってくるよ
    user_id = message.body['user']
    ts = message.body['ts']
    sql = "select * from fish_catch where angler_id ='" + user_id + "';"
    fish_catch_dict = get_db_dict(sql)

    #ランキング取得
    sql = "select * from angler_ranking ORDER BY total_point DESC LIMIT 10;"
    ranking_dict = get_db_dict(sql)
    
    #個人のトータルポイントを算出
    total_point = 0
    for catch_row in fish_catch_dict:
        fish_point = catch_row.get('point')
        fish_count = catch_row.get('count')

        if catch_row.get('point') != None and catch_row.get('count') != None:
            total_point += fish_count * fish_point
    
    response = client.users_list()
    users = response["members"]
    # user_ids = list(map(lambda u: u["profile"], users))
    user_profile_dict = {}
    for user in users:
        user_profile_dict[user["id"]]=user["profile"]

    user_id_list = []
    total_point_list = []
    for row in ranking_dict:
        user_id_list.append(row.get('angler_id'))
        total_point_list.append(row.get('total_point'))

    user_name_list = []
    for user_id in user_id_list:
        user_profile = user_profile_dict[user_id]
        # user_profile = client.users_profile_get(user=user_id)['profile']
        if user_profile["display_name"] != "":
            angler_name = user_profile['display_name']
        else:
            angler_name = user_profile['real_name']

        user_name_list.append(angler_name)

    send_text = []
    for count in range(0,len(user_name_list)):
        if count == 10:
            break

        if count == 0:
            send_text +=[
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
            send_text +=[
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
    
    send_text +=[
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "自分のトータルポイント:" + str(total_point)
                    }
                ]
            },
            {
                "type": "divider"
            },  
        ]

    try:
        client.chat_postMessage(
            channel=message.body['channel'],
            username='釣堀',
            blocks = send_text,
            thread_ts = ts,
            reply_broadcast = False
        )
        
    except AttributeError:
        send_text = "まだ登録されてませんよ？"
        message.send(send_text)

@listen_to('^ヘルプ$')
def fish_help(message):
    ts = message.body['ts']
    send_text = [
        {
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": "おめさ何が知りてぇんだ？"
			}
        },
        {
			"type": "divider"
		},
		{
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": "Q:釣りがしたい\nA:「釣り」と入力すると釣りができます。"
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
				"text": "Q:自分の釣った魚がみたい。\nA:「釣果一覧」と入力すると魚が見れます。"
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
				"text": "Q:ランキングが見たい。\nA:「ランキング」と入力するとランキングが見れます。"
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
				"text": "Q:魚のレア度って何？。\nA:魚のレア度とは希少性を表しています。\n　魚のレア度が低いと釣れやすくなりポイントが低くなります。\n　魚のレア度が高いと釣れにくくなりポイントが高くなります。"
			},
			"accessory": {
				"type": "image",
				"image_url": "https://twemoji.maxcdn.com/v/13.0.1/72x72/1f31f.png",
				"alt_text": "レア度の説明"
			}
		}]

    try:
        client.chat_postMessage(
            channel=message.body['channel'],
            username='釣堀',
            blocks = send_text,
            thread_ts = ts,
            reply_broadcast = False
        )
        
    except AttributeError:
        send_text = "まだ登録されてませんよ？"
        message.send(send_text)