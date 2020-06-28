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
    sql = "select * from fish_catch where angler_id ='" + user_id + "' ORDER BY LENGTH(fish_id) ,fish_id"
    
    catch_dict = get_db_dict(sql)
    send_text = []

    for row in d:
        for catch_row in catch_dict:
            if catch_row.get('fish_id') == row.get('fish_id'):
                fish_name = row.get('fish_name')
                fish_icon = row.get('fish_icon')
                fish_rarity = str(row.get('rarity'))
                fish_min = str(catch_row.get('min_length'))
                fish_max = str(catch_row.get('max_length'))
                fish_count = str(catch_row.get('count'))

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
                                "text": fish_name
                            },
                            {
                                "type": "mrkdwn",
                                "text": "レア度：" + fish_rarity
                            },
                            {
                                "type": "mrkdwn",
                                "text": "釣った数：" + fish_count
                            },
                            {
                                "type": "mrkdwn",
                                "text": "最小サイズ：" + fish_min
                            },
                            {
                                "type": "mrkdwn",
                                "text": "最大サイズ：" + fish_max
                            }
                        ]
                    },]

    try:
        client.chat_postMessage(
            channel=message.body['channel'],
            username='釣堀',
            blocks = send_text
        )
    except AttributeError:
        send_text = "まだ登録されてませんよ？"
        message.send(send_text)

@listen_to('^ランキング$')
def fish_catch(message):
    client.chat_postMessage(
                channel=message.body['channel'],
                username='釣堀',
                blocks=[
                    {
                        "type": "section",
                        "text": {
                                "type": "mrkdwn",
                                "text": "ただいま集計中・・・"
                        }
                    },
                    {
                        "type": "divider"
                    }
                ]
            )
    #お魚一覧とってくるよ
    user_id = message.body['user']
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
    
    user_id_list = []
    total_point_list = []
    for row in ranking_dict:
        user_id_list.append(row.get('angler_id'))
        total_point_list.append(row.get('total_point'))

    user_name_list = []
    for user_id in user_id_list:
        user_profile = client.users_profile_get(user=user_id)['profile']
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
                blocks = send_text
            )
        
    except AttributeError:
        send_text = "まだ登録されてませんよ？"
        message.send(send_text)
    