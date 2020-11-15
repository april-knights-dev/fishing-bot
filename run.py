# coding: utf-8

from slackbot.bot import Bot
from apscheduler.schedulers.blocking import BlockingScheduler
from plugins.ranking_reset import init_weekly_point
from plugins.ranking_reset import init_monthly_point
from threading import Thread

sched = BlockingScheduler()


@sched.scheduled_job("cron", day=1, hour=0, minute=0, second=0)
def monthly_job():
    init_monthly_point()


@sched.scheduled_job("cron", day_of_week='mon', hour=0, minute=0, second=0)
def weekly_job():
    init_weekly_point()


def main():
    bot = Bot()
    bot.run()


if __name__ == "__main__":
    # print('start slackbot')
    # main()
    job = Thread(target=main)
    job.start()
    print("RTMbot job start")

    # APSchedulerの起動
    job = Thread(target=sched.start)
    job.start()
    print("APScheduler job start")
