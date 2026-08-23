from django.contrib import admin

from .models import Item, Location, StockTransaction


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'created_at')
    list_filter = ('organization',)


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('sku', 'name', 'organization', 'quantity', 'unit', 'location', 'is_low_stock')
    list_filter = ('organization', 'location')
    search_fields = ('sku', 'name')


@admin.register(StockTransaction)
class StockTransactionAdmin(admin.ModelAdmin):
    list_display = ('item', 'transaction_type', 'quantity_change', 'performed_by', 'timestamp')
    list_filter = ('transaction_type',)
    readonly_fields = [f.name for f in StockTransaction._meta.fields]
