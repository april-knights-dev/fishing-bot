# coding: utf-8
import os
import re

# from slackbot.bot import Bot
from apscheduler.schedulers.blocking import BlockingScheduler
from plugins.ranking_reset import init_weekly_point
from plugins.ranking_reset import init_monthly_point
from threading import Thread
from slack import WebClient
from slackeventsapi import SlackEventAdapter
from flask import Flask

import plugins.fishing
import plugins.catch

app = Flask(__name__)
slack_signing_secret = os.environ["SIGINING"]
slack_events_adapter = SlackEventAdapter(
    slack_signing_secret, "/slack/events", app)

slack_client = WebClient(token=os.getenv('SLACK_CLIENT_TOKEN'))

sched = BlockingScheduler()


@slack_events_adapter.on("message")
def events_adapter(event_data):
    message = event_data["event"]
    channel = message["channel"]

    if message.get("subtype") is None and re.match(r"^釣り$", message.get("text")):
        plugins.fishing.listen_fishing(message)

    if message.get("subtype") is None and re.match(r"^釣果$", message.get("text")):
        plugins.catch.fish_catch(message)

    if message.get("subtype") is None and re.match(r"^ランキング$", message.get("text")):
        plugins.catch.listen_ranking(message)

    if message.get("subtype") is None and re.match(r"^ヘルプ$", message.get("text")):
        plugins.catch.fish_help(message)

    if message.get("subtype") is None and re.match(r"^野沢ヘルプ$", message.get("text")):
        plugins.catch.fish_help_cv_nozawa(message)


@sched.scheduled_job("cron", day=1, hour=0, minute=0, second=0)
def monthly_job():
    init_monthly_point()


@sched.scheduled_job("cron", day_of_week='mon', hour=0, minute=0, second=0)
def weekly_job():
    init_weekly_point()


# def main():
#     # bot = Bot()
#     # bot.run()
@app.route('/')
def main():
    return "Hello World"


if __name__ == "__main__":


    # APSchedulerの起動
    job = Thread(target=sched.start)
    job.start()
    print("APScheduler job start")

    # flaskの起動
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
