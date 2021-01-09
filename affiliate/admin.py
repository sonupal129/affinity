from django.contrib import admin
from .models import MarketPlace, Category, Channel, Product
# Register your models here.
admin.site.register(MarketPlace)
admin.site.register(Category)
admin.site.register(Channel)
admin.site.register(Product)