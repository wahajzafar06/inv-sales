from django.urls import path
from . import views

urlpatterns = [
    path('supplier-list/', views.supplier_list, name='supplier_list'),
    path('add-supplier/', views.add_supplier, name='add_supplier'),
    path('update-supplier/<int:pk>/', views.update_supplier, name='update_supplier'),
    path('delete-supplier/<int:pk>/', views.delete_supplier, name='delete_supplier'),
    path('dashboard/', views.dashboard, name='dashboard'),
]