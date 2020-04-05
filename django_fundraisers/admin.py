from django.contrib import admin
from django_products.admin import ProductChildAdmin

from django_fundraisers.models import (
    Campaign,
    Fundraiser,
)


@admin.register(Fundraiser)
class FundraiserAdmin(admin.ModelAdmin):
    pass


# Register your models here.
@admin.register(Campaign)
class CampaignAdmin(ProductChildAdmin):
    save_as = True
    list_display = ['title', 'target_donation']


