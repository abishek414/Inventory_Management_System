from django.urls import path

from . import views

app_name = 'organizations'

urlpatterns = [
    path('create/', views.create_organization, name='create'),
    path('switch/<int:org_id>/', views.switch_organization, name='switch'),
    path('roles/', views.manage_roles, name='manage_roles'),
    path('roles/create/', views.create_role, name='create_role'),
    path('roles/<int:role_id>/edit/', views.edit_role, name='edit_role'),
    path('members/', views.manage_members, name='manage_members'),
    path('members/add/', views.add_member, name='add_member'),
    path('members/<int:membership_id>/edit/', views.edit_member, name='edit_member'),
    path('members/<int:membership_id>/history/', views.member_history, name='member_history'),
]
