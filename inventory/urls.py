from django.urls import path

from . import views

app_name = 'inventory'

urlpatterns = [
    path('', views.item_list, name='item_list'),
    path('add/', views.add_item, name='add_item'),
    path('upload/', views.upload_excel, name='upload_excel'),
    path('upload/template/', views.download_excel_template, name='download_excel_template'),
    path('history/', views.transaction_history, name='transaction_history'),
    path('borrow/<int:record_id>/return/', views.return_item, name='return_item'),
    path('<int:item_id>/', views.item_detail, name='item_detail'),
    path('<int:item_id>/edit/', views.edit_item, name='edit_item'),
    path('<int:item_id>/add-stock/', views.add_stock, name='add_stock'),
    path('<int:item_id>/remove-stock/', views.remove_stock, name='remove_stock'),
    path('<int:item_id>/borrow/', views.borrow_item, name='borrow_item'),
    path('<int:item_id>/delete/', views.delete_item, name='delete_item'),
]
