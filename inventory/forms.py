from django import forms

from accounts.forms import BootstrapFormMixin

from .models import Item, Location


class ItemForm(BootstrapFormMixin, forms.ModelForm):
    """
    Creates a brand-new inventory item, with its starting quantity,
    location, and — decided by whoever's adding it — whether it can be
    taken (consumed permanently) and/or borrowed (checked out and
    expected back).
    """

    class Meta:
        model = Item
        fields = [
            'sku', 'name', 'description', 'unit', 'quantity', 'location',
            'reorder_level', 'allow_take', 'allow_borrow',
        ]

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['location'].required = False
        if organization is not None:
            self.fields['location'].queryset = organization.locations.all()


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
        fields = ['sku', 'name', 'description', 'unit', 'reorder_level', 'allow_take', 'allow_borrow']


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
