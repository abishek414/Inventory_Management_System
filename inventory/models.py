from django.conf import settings
from django.db import models

from organizations.models import Organization


class Location(models.Model):
    """
    A physical place within an organization where stock is kept — e.g. a
    warehouse, a specific rack, or a shelf. Scoped to one organization, so
    "Rack 3" at one company is a completely separate row from "Rack 3" at
    another, even with the same name.
    """

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='locations')
    name = models.CharField(max_length=150)
    description = models.CharField(max_length=255, blank=True, help_text='Optional: aisle, building, address, etc.')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('organization', 'name')
        ordering = ['name']

    def __str__(self):
        return self.name


class Item(models.Model):
    """
    One inventory item within an organization. Its current stock quantity
    and current location live directly on this record — the simplest
    model that still covers the four core actions from the brief: view,
    add stock, remove stock / delete the item, and update its location.

    A history of who changed what and when (needed once we build the
    "add stock" / "update location" actions in the next piece) is kept
    in StockTransaction below rather than cluttering this model.
    """

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='items')
    sku = models.CharField('SKU', max_length=50, help_text='Your own item code / stock number.')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    unit = models.CharField(max_length=20, default='pcs', help_text='e.g. pcs, kg, box, litre')
    quantity = models.PositiveIntegerField(default=0)
    location = models.ForeignKey(
        Location, on_delete=models.SET_NULL, null=True, blank=True, related_name='items',
    )
    reorder_level = models.PositiveIntegerField(
        default=0,
        help_text='Show a low-stock warning at or below this quantity. Use 0 to never warn.',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('organization', 'sku')
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.sku})'

    @property
    def is_low_stock(self):
        return self.reorder_level > 0 and self.quantity <= self.reorder_level


class StockTransaction(models.Model):
    """
    An audit trail entry: one row per stock-affecting action. Not used yet
    (nothing creates these until piece 4 adds the add/remove/update-location
    views) but defined now alongside the models it references, so the next
    piece is just "write the views," not "also design the history table."
    """

    ADD = 'ADD'
    REMOVE = 'REMOVE'
    LOCATION_CHANGE = 'LOCATION_CHANGE'
    EXCEL_IMPORT = 'EXCEL_IMPORT'
    TRANSACTION_TYPES = [
        (ADD, 'Stock added'),
        (REMOVE, 'Stock removed'),
        (LOCATION_CHANGE, 'Location changed'),
        (EXCEL_IMPORT, 'Bulk Excel import'),
    ]

    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    quantity_change = models.IntegerField(
        default=0, help_text='Positive for additions, negative for removals, 0 for a pure location change.',
    )
    previous_location = models.ForeignKey(
        Location, on_delete=models.SET_NULL, null=True, blank=True, related_name='+',
    )
    new_location = models.ForeignKey(
        Location, on_delete=models.SET_NULL, null=True, blank=True, related_name='+',
    )
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='stock_transactions',
    )
    note = models.CharField(max_length=255, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f'{self.get_transaction_type_display()} — {self.item} ({self.timestamp:%Y-%m-%d %H:%M})'
