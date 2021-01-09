# Django DB Import
from django.db import models


# CELERY Stuff
from affinity import celery_app



# Affiliate Models Choices
AFFILIATE_CHANNEL_COMPANY = {
    "FB": "Facebook",
    "TG": "Telegram",
    "IT": "Instagram",
    "TW": "Twitter"
}