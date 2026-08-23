from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from organizations.decorators import permission_required

from .excel_import import ExcelImportError, build_template_workbook, import_items_from_excel
from .forms import AddStockForm, BorrowForm, EditItemForm, ExcelUploadForm, ItemForm, RemoveStockForm, ReturnForm
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
    items = request.current_organization.items.all()
    query = request.GET.get('q', '').strip()
    if query:
        items = items.filter(name__icontains=query)
    return render(request, 'inventory/item_list.html', {'items': items, 'query': query})


@permission_required('can_view_inventory')
def item_detail(request, item_id):
    item = _get_org_item_or_404(request, item_id)
    outstanding_borrows = item.borrow_records.filter(returned_at__isnull=True).select_related('borrowed_by')
    history = item.transactions.select_related('performed_by')[:50]
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
                new_location_name=item.location_name,
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
    if not item.track_quantity:
        messages.error(request, f'"{item.name}" isn\'t quantity-tracked — there\'s no stock count to add to.')
        return redirect('inventory:item_detail', item_id=item.id)

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
    if not item.track_quantity:
        messages.error(request, f'"{item.name}" isn\'t quantity-tracked — there\'s no stock count to remove from.')
        return redirect('inventory:item_detail', item_id=item.id)

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
    Edits an item's own details — name, SKU, description, unit, location,
    reorder level, and whether it's takeable/borrowable. Location lives
    right here now: it's plain text owned by this one item (not a shared
    object other items also point to), so there's no separate "Move"
    screen to send people to anymore, and editing it here can never
    affect any other item.

    Quantity is still deliberately not on this form — see EditItemForm's
    docstring — that goes through Add/Remove stock so it stays in the
    audit trail. Location changes still land in that same audit trail
    (a LOCATION_CHANGE entry) even though the field lives on this general
    form; the old/new values are captured before saving specifically so
    that logging is accurate no matter how many other fields changed too.
    """
    item = _get_org_item_or_404(request, item_id)
    old_location_name = item.location_name
    old_location_description = item.location_description

    if request.method == 'POST':
        form = EditItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            location_changed = (
                item.location_name != old_location_name
                or item.location_description != old_location_description
            )
            if location_changed:
                StockTransaction.objects.create(
                    item=item,
                    transaction_type=StockTransaction.LOCATION_CHANGE,
                    quantity_change=0,
                    previous_location_name=old_location_name,
                    new_location_name=item.location_name,
                    performed_by=request.user,
                )
            messages.success(request, f'"{item.name}" updated.')
            return redirect('inventory:item_detail', item_id=item.id)
    else:
        form = EditItemForm(instance=item)

    return render(request, 'inventory/edit_item.html', {'form': form, 'item': item})


@permission_required('can_delete_items')
def delete_item(request, item_id):
    """
    Deleting an item is its own permission ('can_delete_items'), separate
    from taking/removing stock or borrowing — so a role can be allowed to
    take or borrow items without also being able to delete them outright.
    """
    item = _get_org_item_or_404(request, item_id)

    if request.method == 'POST':
        name = item.name
        item.delete()
        messages.success(request, f'"{name}" deleted from inventory.')
        return redirect('inventory:item_list')

    return render(request, 'inventory/delete_item_confirm.html', {'item': item})


@permission_required('can_borrow_items')
def borrow_item(request, item_id):
    """
    Borrowing has its own permission ('can_borrow_items'), separate from
    taking/removing stock — but only applies at all if this specific item
    was marked as borrowable when it was added (item.allow_borrow).
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


@permission_required('can_borrow_items')
def return_item(request, record_id):
    """
    Anyone with can_borrow_items can mark an outstanding borrow returned —
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


@permission_required('can_upload_excel')
def upload_excel(request):
    org = request.current_organization

    if request.method == 'POST':
        form = ExcelUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                result = import_items_from_excel(form.cleaned_data['file'], org, request.user)
            except ExcelImportError as exc:
                messages.error(request, str(exc))
            else:
                summary = f"Import finished — {result['created']} item(s) created, {result['updated']} updated."
                if result['skipped']:
                    summary += f" {len(result['skipped'])} row(s) skipped."
                messages.success(request, summary)
                for row_number, reason in result['skipped']:
                    messages.warning(request, f'Row {row_number} skipped: {reason}.')
                return redirect('inventory:item_list')
    else:
        form = ExcelUploadForm()

    return render(request, 'inventory/upload_excel.html', {'form': form})


@permission_required('can_upload_excel')
def download_excel_template(request):
    workbook = build_template_workbook()
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = 'attachment; filename="inventory_upload_template.xlsx"'
    workbook.save(response)
    return response


@permission_required('can_view_inventory')
def transaction_history(request):
    transactions = StockTransaction.objects.filter(
        item__organization=request.current_organization,
    ).select_related('item', 'performed_by')[:200]

    return render(request, 'inventory/transaction_history.html', {'transactions': transactions})
