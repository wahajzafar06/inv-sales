from django.urls import path
from . import views

urlpatterns = [
    path('purchases/', views.PurchaseListView.as_view(), name='manage_purchase'),
    path('purchases/add/', views.PurchaseCreateView.as_view(), name='add_purchase'),
    path('purchases/update/<int:pk>/', views.PurchaseUpdateView.as_view(), name='update_purchase'),
    path('purchases/delete/<int:pk>/', views.PurchaseDeleteView.as_view(), name='delete_purchase'),
    path('details/<int:purchase_id>/', views.purchase_detail_view, name='purchase_detail'),
]