from .amzn_scraper import *

@celery_app.task
def drum(a,b):
    return a+b

print("O BHOSADI KE")