from django.urls import path
from . import views

urlpatterns = [
    path('add-customer/', views.add_customer, name='add_customer'),
    path('customer-list/', views.customer_list, name='customer_list'),
    path('update-customer/<int:pk>/', views.update_customer, name='update_customer'),
    path('delete-customer/<int:pk>/', views.delete_customer, name='delete_customer'),
]