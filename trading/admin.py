from django.contrib import admin
from .models import Order
# CODE Block


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["order_time", "orderId", "entry_type", "exit_time", "entry_price", "exit_price", "pl_status"]
    readonly_fields = ['orderId', "_entry", "entry_type", "entry_price", "tradeId"]


