from django.urls import path
from . import views

urlpatterns = [
    path('add/', views.new_sale, name='new_sale'),
    path('list/', views.manage_sale, name='manage_sale'),
    path('detail/<int:pk>/', views.sale_detail, name='sale_detail'),
]