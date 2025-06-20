from django.urls import path
from . import views

urlpatterns = [
    path('add-category/', views.add_category, name='add_category'),
    path('category-list/', views.category_list, name='category_list'),
    path('update-category/<int:pk>/', views.update_category, name='update_category'),
    path('delete-category/<int:pk>/', views.delete_category, name='delete_category'),
    path('add-unit/', views.add_unit, name='add_unit'),
    path('unit-list/', views.unit_list, name='unit_list'),
    path('update-unit/<int:pk>/', views.update_unit, name='update_unit'),
    path('delete-unit/<int:pk>/', views.delete_unit, name='delete_unit'),
    path('add-product/', views.add_product, name='add_product'),
    path('product-list/', views.product_list, name='product_list'),
    path('update-product/<int:pk>/', views.update_product, name='update_product'),
    path('delete-product/<int:pk>/', views.delete_product, name='delete_product'),
    path('add-product-csv/', views.add_product_csv, name='add_product_csv'),
    path('manage-product/', views.manage_product, name='manage_product'),
]