from django.db import models
import jsonfield
import pandas as pd

# Code Block

class Order(models.Model):
    order_time = models.DateTimeField(unique=True, db_index=True)
    _entry = jsonfield.JSONField(default={})
    exit_time = models.DateTimeField(blank=True, null=True)
    exit_price = models.CharField(blank=True, null=True, max_length=10)
    pl_status = models.CharField(blank=True, null=True, max_length=10)
    orderId = models.PositiveIntegerField(blank=True, null=True)


    @property
    def has_exit_signal(self):
        return all([self.exit_time, self.exit_price, self.pl_status])
        
    @property
    def entry(self):
        output = {}
        for name, tdata in self._entry.items():
            tstamp = pd.Timestamp(list(tdata.keys())[0])
            value = list(tdata.values())[0]
            output[name] = {tstamp: value}
        return output

    @property
    def entry_type(self):
        return list(self.entry["entry_signal"].values())[0]

    @property
    def entry_price(self):
        return list(self.entry["entry_price"].values())[0]