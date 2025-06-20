from django.urls import path
from . import views

urlpatterns = [
    path('stock/', views.stock_report, name='stock_report'),
]