from django import forms

from accounts.forms import BootstrapFormMixin

from .models import Item


class ItemForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Item
        fields = [
            'sku', 'name', 'description', 'track_quantity', 'unit', 'quantity',
            'location_name', 'location_description', 'reorder_level', 'allow_take', 'allow_borrow',
        ]

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['quantity'].required = False
        self.fields['reorder_level'].required = False

    def clean(self):
        cleaned_data = super().clean()
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
    quantity = forms.IntegerField(min_value=1, label='Quantity to take')
    note = forms.CharField(max_length=255, required=False, help_text='Optional, e.g. "used on Job #42" or "damaged / written off".')

    def __init__(self, *args, item=None, **kwargs):
        self.item = item
        super().__init__(*args, **kwargs)

    def clean_quantity(self):
        quantity = self.cleaned_data['quantity']
        if self.item is not None and quantity > self.item.quantity:
            raise forms.ValidationError(
                f'Only {self.item.quantity} {self.item.unit} in stock — cannot take {quantity}.'
            )
        return quantity


class BorrowForm(BootstrapFormMixin, forms.Form):
    quantity = forms.IntegerField(min_value=1, initial=1)
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
