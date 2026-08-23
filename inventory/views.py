from organizations.decorators import permission_required

from django.shortcuts import render


@permission_required('can_view_inventory')
def item_list(request):
    """
    The inventory list for whichever organization the user is currently
    working in. Items are added manually or via Excel upload starting in
    the next pieces — for now, add a couple of test rows through
    /admin/ to see this page populated.
    """
    items = request.current_organization.items.select_related('location')
    return render(request, 'inventory/item_list.html', {'items': items})
