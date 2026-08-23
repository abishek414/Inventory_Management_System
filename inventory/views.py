from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from organizations.decorators import permission_required

from .forms import (
    AddStockForm, BorrowForm, EditItemForm, ItemForm, LocationForm, RemoveStockForm, ReturnForm,
    UpdateLocationForm,
)
from .models import BorrowRecord, Item, StockTransaction


def _get_org_item_or_404(request, item_id):
    """
    Always look items up scoped to the current organization. Without the
    `organization=` filter here, a logged-in user could load
    /inventory/<id>/add-stock/ for an item ID belonging to a *different*
    organization just by guessing/incrementing the number in the URL —
    this is what stops that.
    """
    return get_object_or_404(Item, pk=item_id, organization=request.current_organization)


@permission_required('can_view_inventory')
def item_list(request):
    items = request.current_organization.items.select_related('location')
    return render(request, 'inventory/item_list.html', {'items': items})


@permission_required('can_view_inventory')
def item_detail(request, item_id):
    item = _get_org_item_or_404(request, item_id)
    outstanding_borrows = item.borrow_records.filter(returned_at__isnull=True).select_related('borrowed_by')
    history = item.transactions.select_related('performed_by', 'previous_location', 'new_location')[:50]
    return render(request, 'inventory/item_detail.html', {
        'item': item,
        'outstanding_borrows': outstanding_borrows,
        'history': history,
    })


@permission_required('can_add_stock')
def add_item(request):
    org = request.current_organization
    if request.method == 'POST':
        form = ItemForm(request.POST, organization=org)
        if form.is_valid():
            item = form.save(commit=False)
            item.organization = org
            item.save()
            StockTransaction.objects.create(
                item=item,
                transaction_type=StockTransaction.ADD,
                quantity_change=item.quantity,
                new_location=item.location,
                performed_by=request.user,
                note='Item created',
            )
            messages.success(request, f'"{item.name}" added to inventory.')
            return redirect('inventory:item_list')
    else:
        form = ItemForm(organization=org)

    return render(request, 'inventory/item_form.html', {'form': form})


@permission_required('can_add_stock')
def add_stock(request, item_id):
    item = _get_org_item_or_404(request, item_id)

    if request.method == 'POST':
        form = AddStockForm(request.POST)
        if form.is_valid():
            quantity = form.cleaned_data['quantity']
            item.quantity += quantity
            item.save(update_fields=['quantity', 'updated_at'])
            StockTransaction.objects.create(
                item=item,
                transaction_type=StockTransaction.ADD,
                quantity_change=quantity,
                performed_by=request.user,
                note=form.cleaned_data['note'],
            )
            messages.success(request, f'Added {quantity} {item.unit} to "{item.name}" (new total: {item.quantity}).')
            return redirect('inventory:item_list')
    else:
        form = AddStockForm()

    return render(request, 'inventory/stock_form.html', {'form': form, 'item': item, 'action': 'Add'})


@permission_required('can_remove_stock')
def remove_stock(request, item_id):
    item = _get_org_item_or_404(request, item_id)

    if request.method == 'POST':
        form = RemoveStockForm(request.POST, item=item)
        if form.is_valid():
            quantity = form.cleaned_data['quantity']
            item.quantity -= quantity
            item.save(update_fields=['quantity', 'updated_at'])
            StockTransaction.objects.create(
                item=item,
                transaction_type=StockTransaction.REMOVE,
                quantity_change=-quantity,
                performed_by=request.user,
                note=form.cleaned_data['note'],
            )
            messages.success(request, f'Removed {quantity} {item.unit} from "{item.name}" (new total: {item.quantity}).')
            return redirect('inventory:item_list')
    else:
        form = RemoveStockForm(item=item)

    return render(request, 'inventory/stock_form.html', {'form': form, 'item': item, 'action': 'Remove'})


@permission_required('can_edit_items')
def edit_item(request, item_id):
    """
    Edits an item's own details (name, SKU, description, unit, reorder
    level, and whether it's takeable/borrowable). Quantity and location
    are deliberately not here — see EditItemForm's docstring — those go
    through Add/Remove stock and Move so they stay in the audit trail.
    """
    item = _get_org_item_or_404(request, item_id)

    if request.method == 'POST':
        form = EditItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, f'"{item.name}" updated.')
            return redirect('inventory:item_detail', item_id=item.id)
    else:
        form = EditItemForm(instance=item)

    return render(request, 'inventory/edit_item.html', {'form': form, 'item': item})


@permission_required('can_edit_items')
def update_location(request, item_id):
    item = _get_org_item_or_404(request, item_id)
    org = request.current_organization

    if request.method == 'POST':
        form = UpdateLocationForm(request.POST, organization=org)
        if form.is_valid():
            old_location = item.location
            new_location = form.cleaned_data['location']
            item.location = new_location
            item.save(update_fields=['location', 'updated_at'])
            StockTransaction.objects.create(
                item=item,
                transaction_type=StockTransaction.LOCATION_CHANGE,
                quantity_change=0,
                previous_location=old_location,
                new_location=new_location,
                performed_by=request.user,
            )
            messages.success(request, f'"{item.name}" moved to {new_location or "no location"}.')
            return redirect('inventory:item_list')
    else:
        form = UpdateLocationForm(initial={'location': item.location}, organization=org)

    return render(request, 'inventory/update_location.html', {'form': form, 'item': item})


@permission_required('can_remove_stock')
def delete_item(request, item_id):
    """
    Deleting an item entirely uses the same permission as removing stock
    ('can_remove_stock') rather than a brand-new flag — the brief grouped
    "delete stock or item" as one action. If you'd rather split these into
    separate permissions later, that just means adding a new boolean field
    to the Role model (a small migration) and swapping the decorator here.
    """
    item = _get_org_item_or_404(request, item_id)

    if request.method == 'POST':
        name = item.name
        item.delete()
        messages.success(request, f'"{name}" deleted from inventory.')
        return redirect('inventory:item_list')

    return render(request, 'inventory/delete_item_confirm.html', {'item': item})


@permission_required('can_remove_stock')
def borrow_item(request, item_id):
    """
    Borrowing uses the same permission as removing stock — both reduce
    what's available — but only applies at all if this specific item was
    marked as borrowable when it was added (item.allow_borrow).
    """
    item = _get_org_item_or_404(request, item_id)
    if not item.allow_borrow:
        messages.error(request, f'"{item.name}" is not set up as borrowable.')
        return redirect('inventory:item_detail', item_id=item.id)

    if request.method == 'POST':
        form = BorrowForm(request.POST, item=item)
        if form.is_valid():
            quantity = form.cleaned_data['quantity']
            item.quantity -= quantity
            item.save(update_fields=['quantity', 'updated_at'])
            BorrowRecord.objects.create(
                item=item,
                borrowed_by=request.user,
                quantity=quantity,
                due_date=form.cleaned_data['due_date'],
                note=form.cleaned_data['note'],
            )
            StockTransaction.objects.create(
                item=item,
                transaction_type=StockTransaction.BORROW,
                quantity_change=-quantity,
                performed_by=request.user,
                note=form.cleaned_data['note'],
            )
            messages.success(request, f'Borrowed {quantity} {item.unit} of "{item.name}".')
            return redirect('inventory:item_detail', item_id=item.id)
    else:
        form = BorrowForm(item=item)

    return render(request, 'inventory/borrow_form.html', {'form': form, 'item': item})


@permission_required('can_remove_stock')
def return_item(request, record_id):
    """
    Anyone with can_remove_stock can mark an outstanding borrow returned —
    not just the person who originally borrowed it — since in practice
    it's often a manager checking the item back in physically, not the
    borrower operating the computer themselves.
    """
    record = get_object_or_404(
        BorrowRecord,
        pk=record_id,
        item__organization=request.current_organization,
        returned_at__isnull=True,
    )
    item = record.item

    if request.method == 'POST':
        form = ReturnForm(request.POST)
        if form.is_valid():
            record.returned_at = timezone.now()
            if form.cleaned_data['note']:
                record.note = f"{record.note} | {form.cleaned_data['note']}" if record.note else form.cleaned_data['note']
            record.save(update_fields=['returned_at', 'note'])

            item.quantity += record.quantity
            item.save(update_fields=['quantity', 'updated_at'])
            StockTransaction.objects.create(
                item=item,
                transaction_type=StockTransaction.RETURN,
                quantity_change=record.quantity,
                performed_by=request.user,
                note=form.cleaned_data['note'],
            )
            messages.success(request, f'Marked {record.quantity} {item.unit} of "{item.name}" as returned.')
            return redirect('inventory:item_detail', item_id=item.id)
    else:
        form = ReturnForm()

    return render(request, 'inventory/return_form.html', {'form': form, 'record': record})


@permission_required('can_edit_items')
def manage_locations(request):
    org = request.current_organization

    if request.method == 'POST':
        form = LocationForm(request.POST)
        if form.is_valid():
            location = form.save(commit=False)
            location.organization = org
            location.save()
            messages.success(request, f'Location "{location.name}" added.')
            return redirect('inventory:manage_locations')
    else:
        form = LocationForm()

    locations = org.locations.all()
    return render(request, 'inventory/manage_locations.html', {'form': form, 'locations': locations})


@permission_required('can_view_inventory')
def transaction_history(request):
    transactions = StockTransaction.objects.filter(
        item__organization=request.current_organization,
    ).select_related('item', 'previous_location', 'new_location', 'performed_by')[:200]

    return render(request, 'inventory/transaction_history.html', {'transactions': transactions})
