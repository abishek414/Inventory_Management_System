from django import forms

from accounts.forms import BootstrapFormMixin

from .models import Item


class ItemForm(BootstrapFormMixin, forms.ModelForm):
    """
    Creates a brand-new inventory item, with its starting quantity,
    location, and — decided by whoever's adding it — whether it can be
    taken (consumed permanently) and/or borrowed (checked out and
    expected back). Location (name + optional description) is plain text
    entered right here, owned by this item alone — not shared with or
    affected by any other item's location.

    If "Track quantity" is unchecked (bulk material where only the
    location matters), quantity/unit/reorder level become optional and
    take/borrow are forced off — see clean() below.
    """

    class Meta:
        model = Item
        fields = [
            'sku', 'name', 'description', 'track_quantity', 'unit', 'quantity',
            'location_name', 'location_description', 'reorder_level', 'allow_take', 'allow_borrow',
        ]

    def __init__(self, *args, organization=None, **kwargs):
        # organization is accepted (and ignored) for backwards compatibility
        # with call sites that still pass it — location no longer needs an
        # organization-scoped queryset since it's plain text per item.
        super().__init__(*args, **kwargs)
        self.fields['quantity'].required = False
        self.fields['reorder_level'].required = False

    def clean(self):
        cleaned_data = super().clean()
        # quantity/reorder_level are optional fields now (see __init__), so a
        # blank entry cleans to None — not a valid value for the model's
        # PositiveIntegerField — so it's coalesced to 0 here regardless of
        # track_quantity.
        if cleaned_data.get('quantity') is None:
            cleaned_data['quantity'] = 0
        if cleaned_data.get('reorder_level') is None:
            cleaned_data['reorder_level'] = 0
        if not cleaned_data.get('track_quantity'):
            cleaned_data['quantity'] = 0
            cleaned_data['reorder_level'] = 0
            cleaned_data['allow_take'] = False
            cleaned_data['allow_borrow'] = False
        return cleaned_data


class EditItemForm(BootstrapFormMixin, forms.ModelForm):
    """
    Edits an item's own details, including its location — location is
    plain text owned by this one item, so changing it here has no effect
    on any other item, unlike the old shared-Location design. The view
    that uses this form (inventory.views.edit_item) still logs a location
    change to the item's history when location_name/location_description
    actually changes, even though the field lives on this general form now.

    Quantity stays off this form on purpose: it's tracked with a full
    audit trail (who changed it, when, by how much) through the dedicated
    Add/Remove stock actions. Letting this form touch it too would let
    someone silently overwrite a quantity with no log entry at all, which
    defeats the point of having that history.
    """

    class Meta:
        model = Item
        fields = [
            'sku', 'name', 'description', 'track_quantity', 'unit',
            'location_name', 'location_description', 'reorder_level', 'allow_take', 'allow_borrow',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['reorder_level'].required = False

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('reorder_level') is None:
            cleaned_data['reorder_level'] = 0
        if not cleaned_data.get('track_quantity'):
            cleaned_data['reorder_level'] = 0
            cleaned_data['allow_take'] = False
            cleaned_data['allow_borrow'] = False
        return cleaned_data


class AddStockForm(BootstrapFormMixin, forms.Form):
    quantity = forms.IntegerField(min_value=1, label='Quantity to add')
    note = forms.CharField(max_length=255, required=False, help_text='Optional, e.g. "delivery from supplier".')


class RemoveStockForm(BootstrapFormMixin, forms.Form):
    quantity = forms.IntegerField(min_value=1, label='Quantity to remove')
    note = forms.CharField(max_length=255, required=False, help_text='Optional, e.g. "damaged / written off".')

    def __init__(self, *args, item=None, **kwargs):
        self.item = item
        super().__init__(*args, **kwargs)

    def clean_quantity(self):
        quantity = self.cleaned_data['quantity']
        if self.item is not None and quantity > self.item.quantity:
            raise forms.ValidationError(
                f'Only {self.item.quantity} {self.item.unit} in stock — cannot remove {quantity}.'
            )
        return quantity


class BorrowForm(BootstrapFormMixin, forms.Form):
    quantity = forms.IntegerField(min_value=1, initial=1)
    due_date = forms.DateField(
        required=False, widget=forms.DateInput(attrs={'type': 'date'}), help_text='Optional.',
    )
    note = forms.CharField(max_length=255, required=False)

    def __init__(self, *args, item=None, **kwargs):
        self.item = item
        super().__init__(*args, **kwargs)

    def clean_quantity(self):
        quantity = self.cleaned_data['quantity']
        if self.item is not None and quantity > self.item.quantity:
            raise forms.ValidationError(
                f'Only {self.item.quantity} {self.item.unit} available — cannot borrow {quantity}.'
            )
        return quantity


class ReturnForm(BootstrapFormMixin, forms.Form):
    note = forms.CharField(max_length=255, required=False, help_text='Optional, e.g. condition on return.')


class ExcelUploadForm(BootstrapFormMixin, forms.Form):
    file = forms.FileField(
        label='Excel file',
        help_text='.xlsx only. Use "Download template" below if you\'re not sure of the columns.',
    )

    def clean_file(self):
        uploaded = self.cleaned_data['file']
        if not uploaded.name.lower().endswith('.xlsx'):
            raise forms.ValidationError('Please upload a .xlsx file (the format Excel saves by default).')
        return uploaded
