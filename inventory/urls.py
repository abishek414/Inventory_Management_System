from django.urls import path

from . import views

app_name = 'inventory'

urlpatterns = [
    path('', views.item_list, name='item_list'),
    path('add/', views.add_item, name='add_item'),
    path('locations/', views.manage_locations, name='manage_locations'),
    path('history/', views.transaction_history, name='transaction_history'),
    path('borrow/<int:record_id>/return/', views.return_item, name='return_item'),
    path('<int:item_id>/', views.item_detail, name='item_detail'),
    path('<int:item_id>/add-stock/', views.add_stock, name='add_stock'),
    path('<int:item_id>/remove-stock/', views.remove_stock, name='remove_stock'),
    path('<int:item_id>/borrow/', views.borrow_item, name='borrow_item'),
    path('<int:item_id>/update-location/', views.update_location, name='update_location'),
    path('<int:item_id>/delete/', views.delete_item, name='delete_item'),
]
