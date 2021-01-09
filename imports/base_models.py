from django.db import models
from simple_history.models import HistoricalRecords

# CODE BELOW

class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords(inherit=True)
    

    class Meta:
        abstract=True
        ordering=["created_at"]


