from django.conf import settings
from django.db import models

from organizations.models import Organization


class Item(models.Model):
    """
    One inventory item within an organization. Its current stock quantity
    and current location live directly on this record.

    Location is plain text on the item itself (location_name /
    location_description) rather than a shared object multiple items
    point to — deliberately. Earlier this was a separate Location model
    that items referenced by foreign key, so renaming "Main Warehouse"
    changed it for every item stored there at once. That surprised
    whoever renamed it expecting to affect only the one item they were
    looking at, so each item now owns its own independent location text
    instead — set when the item is created, and editable per item from
    then on, with no effect on any other item.

    A history of who changed what and when is kept in StockTransaction
    below rather than cluttering this model.
    """

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='items')
    sku = models.CharField('SKU', max_length=50, help_text='Your own item code / stock number.')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    track_quantity = models.BooleanField(
        default=True,
        help_text=(
            'Uncheck for items you don\'t want to count individually — e.g. bulk material '
            '("a pile of sand") where only the location matters. Quantity, unit, reorder '
            'warnings, and the stock actions (+Stock / Take / Borrow) are all hidden for an '
            'item with this off.'
        ),
    )
    unit = models.CharField(max_length=20, default='pcs', help_text='e.g. pcs, kg, box, litre')
    quantity = models.PositiveIntegerField(default=0)
    location_name = models.CharField(
        max_length=150, blank=True, help_text='Where this item is kept — e.g. "Main Warehouse", "Rack 3".',
    )
    location_description = models.CharField(
        max_length=255, blank=True, help_text='Optional: aisle, building, address, etc.',
    )
    reorder_level = models.PositiveIntegerField(
        default=0,
        help_text='Show a low-stock warning at or below this quantity. Use 0 to never warn.',
    )
    allow_take = models.BooleanField(
        default=True,
        help_text='Can be permanently taken out of stock (consumed) — most items.',
    )
    allow_borrow = models.BooleanField(
        default=False,
        help_text='Can be checked out temporarily and later returned — e.g. tools or equipment.',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('organization', 'sku')
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.sku})'

    @property
    def is_out_of_stock(self):
        if not self.track_quantity:
            return False
        return self.quantity <= 0

    @property
    def is_low_stock(self):
        """
        True at or below the reorder level — INCLUDING zero, since zero is
        the most extreme case of "at or below." False outright for an item
        that isn't quantity-tracked, since its quantity field isn't
        meaningful there. Templates check is_out_of_stock first and only
        fall back to this for the "Low stock" label, so an item that's
        completely out shows "Out of stock" instead of the more
        misleading "Low stock."
        """
        if not self.track_quantity:
            return False
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
    BORROW = 'BORROW'
    RETURN = 'RETURN'
    TRANSACTION_TYPES = [
        (ADD, 'Stock added'),
        (REMOVE, 'Stock removed (taken)'),
        (LOCATION_CHANGE, 'Location changed'),
        (EXCEL_IMPORT, 'Bulk Excel import'),
        (BORROW, 'Borrowed'),
        (RETURN, 'Returned'),
    ]

    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    quantity_change = models.IntegerField(
        default=0, help_text='Positive for additions, negative for removals, 0 for a pure location change.',
    )
    # Text snapshots, not a foreign key — location lives directly on Item
    # now (see Item.location_name), so a history entry just records what
    # the text was before/after at the time of the change.
    previous_location_name = models.CharField(max_length=150, blank=True)
    new_location_name = models.CharField(max_length=150, blank=True)
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='stock_transactions',
    )
    note = models.CharField(max_length=255, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f'{self.get_transaction_type_display()} — {self.item} ({self.timestamp:%Y-%m-%d %H:%M})'


class BorrowRecord(models.Model):
    """
    One checkout of a borrowable item. Created when someone borrows an
    item (Item.quantity goes down by the borrowed amount) and closed when
    it's marked returned (Item.quantity goes back up). Whether an item
    supports this at all is decided by whoever added it, via
    Item.allow_borrow — not every item needs to be trackable this way.
    """

    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='borrow_records')
    borrowed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='borrowed_items',
    )
    quantity = models.PositiveIntegerField(default=1)
    borrowed_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField(null=True, blank=True, help_text='Optional — when it should come back.')
    returned_at = models.DateTimeField(null=True, blank=True)
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-borrowed_at']

    @property
    def is_outstanding(self):
        return self.returned_at is None

    def __str__(self):
        status = 'outstanding' if self.is_outstanding else 'returned'
        return f'{self.item} x{self.quantity} — {self.borrowed_by} ({status})'
