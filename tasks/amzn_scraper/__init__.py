from affinity import celery_app


@celery_app.task
def drum1(a,b):
    return a+b



