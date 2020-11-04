from django.shortcuts import render
import requests
import json
from django.http import HttpResponse
from .models import Team
from django.conf import settings
from django.core.management import call_command
from threading import Thread
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


# Create your views here.
def index(request):
    client_id = settings.SLACK_CLIENT_ID
    return render(request, 'landing.html', {'client_id': client_id})


def slack_oauth(request):
    code = request.GET['code']

    params = {
        'code': code,
        'client_id': settings.SLACK_CLIENT_ID,
        "client_secret": settings.SLACK_CLIENT_SECRET
    }
    url = 'https://slack.com/api/oauth.access'
    json_response = requests.get(url, params)
    data = json.loads(json_response.text)
    logger.info("GET REQUEST URL - {}, PARAMS - {}".format(url, params))
    Team.objects.get_or_create(
        name=data['team_name'],
        team_id=data['team_id'],
        bot_user_id=data['bot']['bot_user_id'],
        bot_access_token=data['bot']['bot_access_token']
    )

    t = Thread(target=call_command, args=('listener',))
    t.start()
    return HttpResponse('Bot added to your Slack team!')