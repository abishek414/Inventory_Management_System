from django.contrib import admin

from .models import BorrowRecord, Item, Location, StockTransaction


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'created_at')
    list_filter = ('organization',)


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = (
        'sku', 'name', 'organization', 'quantity', 'unit', 'location',
        'is_low_stock', 'allow_take', 'allow_borrow',
    )
    list_filter = ('organization', 'location', 'allow_take', 'allow_borrow')
    search_fields = ('sku', 'name')


@admin.register(BorrowRecord)
class BorrowRecordAdmin(admin.ModelAdmin):
    list_display = ('item', 'borrowed_by', 'quantity', 'borrowed_at', 'due_date', 'returned_at', 'is_outstanding')
    list_filter = ('item__organization',)


@admin.register(StockTransaction)
class StockTransactionAdmin(admin.ModelAdmin):
    list_display = ('item', 'transaction_type', 'quantity_change', 'performed_by', 'timestamp')
    list_filter = ('transaction_type',)
    readonly_fields = [f.name for f in StockTransaction._meta.fields]
