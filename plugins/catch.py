from slack.errors import SlackApiError
from slackbot.bot import respond_to     # @botname: で反応するデコーダ
from slackbot.bot import listen_to      # チャネル内発言で反応するデコーダ
from slackbot.bot import default_reply  # 該当する応答がない場合に反応するデコーダ
import requests
import urllib.request as req
import sys
import json

@listen_to('釣果')
def listen_func(message):
    message.send('まだ準備中（平田くんが頑張ってます）')      # ただの投稿
    # message.reply('君だね？')
