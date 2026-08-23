from django import forms

from accounts.forms import BootstrapFormMixin

from .models import Item, Location


class ItemForm(BootstrapFormMixin, forms.ModelForm):
    """
    Creates a brand-new inventory item, with its starting quantity,
    location, and — decided by whoever's adding it — whether it can be
    taken (consumed permanently) and/or borrowed (checked out and
    expected back).

    If "Track quantity" is unchecked (bulk material where only the
    location matters), quantity/unit/reorder level become optional and
    take/borrow are forced off — see clean() below.
    """

    class Meta:
        model = Item
        fields = [
            'sku', 'name', 'description', 'track_quantity', 'unit', 'quantity', 'location',
            'reorder_level', 'allow_take', 'allow_borrow',
        ]

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['location'].required = False
        self.fields['quantity'].required = False
        self.fields['reorder_level'].required = False
        if organization is not None:
            self.fields['location'].queryset = organization.locations.all()

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
    Edits an item's own details — everything about it EXCEPT quantity and
    location. Those two stay off this form on purpose: they're both
    tracked with a full audit trail (who changed them, when, by how much)
    through the dedicated Add/Remove stock and Move actions. Letting this
    form touch them too would let someone silently overwrite a quantity or
    location with no log entry at all, which defeats the point of having
    that history.
    """

    class Meta:
        model = Item
        fields = [
            'sku', 'name', 'description', 'track_quantity', 'unit',
            'reorder_level', 'allow_take', 'allow_borrow',
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


class UpdateLocationForm(BootstrapFormMixin, forms.Form):
    location = forms.ModelChoiceField(
        queryset=Location.objects.none(), required=False, empty_label='— No location —',
    )

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        if organization is not None:
            self.fields['location'].queryset = organization.locations.all()


class LocationForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Location
        fields = ['name', 'description']


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
