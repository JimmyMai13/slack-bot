from django.core.management.base import BaseCommand
from slackbot.models import Team
from slackclient import SlackClient
import os
import sys
import time
import sqlite3
import re
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from semaphore import Sem
import logging

logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'console': {
            'format': '%(name)-12s %(levelname)-8s %(message)s'
        },
        'file': {
            'format': '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'console'
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'formatter': 'file',
            'filename': '/tmp/slackapp_debug.log'
        }
    },
    'loggers': {
        '': {
            'level': 'DEBUG',
            'handlers': ['console', 'file']
        }
    }
})


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Starts the bot for the first'

    def querySqliteTable(self):
        try:
            sqliteConnection = sqlite3.connect('db.sqlite3')
            cursor = sqliteConnection.cursor()
            print("Connected to SQLite")

            sqlite_select_query = """SELECT * from slackbot_team"""
            cursor.execute(sqlite_select_query)
            records = cursor.fetchall()
            print("Total rows are:  ", len(records))
            print("Printing each row")
            db_data = {}
            for row in records:
                db_data['id'] = row[0]
                db_data['name'] = row[1]
                db_data['team_id'] = row[2]
                db_data['bot_user_id'] = row[3]
                db_data['bot_user_access_token'] = row[4]
            cursor.close()

        except sqlite3.Error as error:
            print("Failed to read data from sqlite table", error)
        finally:
            if (sqliteConnection):
                sqliteConnection.close()
                print("The SQLite connection is closed")
        return db_data

    def process_event(self, client, team):
        events = client.rtm_read()
        print("%s----%s" % (team, events))
        logger.info("%s----%s" % (team, events))
        for event in events:
            if 'type' in event and event['type'] == 'message' and 'client_msg_id' in event.keys():
                channel = event.get('channel')
                user = event.get('user')
                thread_ts = event.get('ts')
                text = event.get('text')

                print('$$$$$$$')
                print(user)
                print(channel)
                print(thread_ts)
                print(text)
                logger.info("Text sent to slack app - {}".format(text))
                regex = re.match('deploy ([^ ]+) run \/(.*)', text)
                print("Regex Match  - " + str(regex))
                if regex:
                    logger.info("Regex Match 1- " + regex.group(1))
                    logger.info("Regex Match 2- " + regex.group(2))
                    sem = Sem()
                    sem.install_and_connect_sem()
                    logger.info("Successfully install and connect Semaphore")
                    sem.create_sem_secret({"slack_ts": thread_ts, "slack_channel": channel}, "adhoc_bot_initial_slack")
                    print('- Regex Group 1 match: ' + regex.group(1))
                    print('- Regex Group 2 match: ' + regex.group(2))
                    print('- THREAD_TS: ' + thread_ts)
                    sem.create_sem_secret({"SHA": regex.group(1), "WDIO_CMD": regex.group(2), "USERID": user},
                                          'adhoc')
                    sem.run_workflow('jimmy2')
                    response_msg = ":wave:, Hello <@{}>, build has been triggered ... ".format(user)

                    # client.rtm_send_message(event['channel'], response_msg)

                    client.api_call("chat.postMessage",
                                    channel=event['channel'],
                                    text=response_msg,
                                    thread_ts=thread_ts
                                    )
                else:
                    response_msg = ":wave:, Hello <@{}>, error in cmd (e.g. `deploy 3b82706780153a7a839281822fe9ac30e1829205 run /wdio.bs.conf.js --suite login`)".format(
                        user)

                    # client.rtm_send_message(event['channel'], response_msg)

                    client.api_call("chat.postMessage",
                                    channel=event['channel'],
                                    text=response_msg,
                                    thread_ts=thread_ts
                                    )
        time.sleep(1)

    def handle(self, *args, **options):
        # bot_access_token = self.querySqliteTable()['bot_user_access_token']
        team = Team.objects.first()
        logger.info("listener.py bot_access_token - {}".format(team.bot_access_token))
        client = SlackClient(team.bot_access_token)
        if client.rtm_connect():
            logger.info("Connection established")
            while True:
                logger.info("Proceeding to process event messages")
                try:
                    self.process_event(client, team)
                except:
                    logger.info("Connection Failed -")
                    client.rtm_connect()
        else:
            logger.info("Connection Failed *")
