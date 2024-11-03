from django.contrib import admin
from django.contrib.admin import TabularInline, ModelAdmin

from .models import Wallet, Transaction

admin.site.site_header = "Wallet API Admin"
admin.site.site_title = "Wallet API site admin"
admin.site.index_title = "Wallet API"
admin.site.site_url = "/admin/"


class TransactionAdminInline(TabularInline):
    model = Transaction
    extra = 0
    can_delete = False
    readonly_fields = ('wallet', 'txid', 'amount')


@admin.register(Wallet)
class WalletAdmin(ModelAdmin):
    list_display = ('label', 'balance')
    inlines = [TransactionAdminInline]


@admin.register(Transaction)
class TransactionAdmin(ModelAdmin):
    list_display = ('wallet', 'txid', 'amount')
