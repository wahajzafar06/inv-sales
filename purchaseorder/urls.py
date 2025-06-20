from django.urls import path
from . import views

urlpatterns = [
    path('purchase-orders/', views.PurchaseOrderListView.as_view(), name='manage_purchase_order'),
    path('purchase-orders/add/', views.PurchaseOrderCreateView.as_view(), name='add_purchase_order'),
    path('purchase-orders/update/<int:pk>/', views.PurchaseOrderUpdateView.as_view(), name='update_purchase_order'),
    path('purchase-orders/delete/<int:pk>/', views.PurchaseOrderDeleteView.as_view(), name='delete_purchase_order'),
    path('purchase-orders/detail/<int:pk>/', views.purchase_order_detail_view, name='purchase_order_detail'),
]