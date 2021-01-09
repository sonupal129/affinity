from imports import *

# Create your models here.

class MarketPlace(BaseModel):
    country_choices = countries_list

    name = models.CharField(max_length=100)
    website = models.URLField()
    affiliate_id = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(choices=country_choices, default=None, max_length=30)

    def __str__(self):
        return self.website

class Category(BaseModel):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class Channel(BaseModel):
    company_choices = {(k,v)for k,v in AFFILIATE_CHANNEL_COMPANY.items()}

    name = models.CharField(max_length=100)
    social_handle = models.CharField(max_length=100)
    unique_id = models.CharField(max_length=100)
    url = models.URLField()
    networking_company = models.CharField(max_length=2, default="FB", choices=company_choices)
    marketplace = models.ForeignKey(MarketPlace, on_delete=models.PROTECT)

    def __str__(self):
        return self.name

class Product(BaseModel):
    url = models.URLField()
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    new_price = models.DecimalField(max_digits=8, decimal_places=2)
    old_price = models.DecimalField(max_digits=8, decimal_places=2)
    channels = models.ManyToManyField(Channel, blank=True)
    marketplace = models.ForeignKey(MarketPlace, on_delete=models.PROTECT, null=True)

    def __str__(self):
        return self.name

    @property
    def channels(self):
        return self.channels.filter(marketplace_id=self.marketplace_id)


