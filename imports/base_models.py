from django.db import models
from simpler_history.models import HistoricalRecords

# CODE BELOW

class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()
    

    class Meta:
        abstract=True
        ordering=["created_at"]


