from affinity import celery_app
from slack import WebClient
from django.conf import settings



# Celery Tasks 

@celery_app.task
def send_slack_message(channel="#trade_error_notification", message="", attachment=None):
    sc = WebClient(token=settings.SLACK_TOKEN)
    response = sc.chat_postMessage(
            channel=channel,
            text=message,
        )
    return response.get('ok', False)
