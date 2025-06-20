from django.db import models
from customer.models import Customer
from product.models import Product, Unit
from django.utils import timezone

class Sale(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='sales')
    date = models.DateTimeField(default=timezone.now)
    sale_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, editable=False)
    total_vat = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, editable=False)
    grand_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, editable=False)
    net_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, editable=False)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"Sale {self.id} - {self.customer.customer_name} ({self.date})"

class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    description = models.TextField(blank=True)
    available_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, editable=False)
    unit = models.ForeignKey(Unit, on_delete=models.SET_NULL, null=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, editable=False)
    vat_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    vat_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, editable=False)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, editable=False)

    def __str__(self):
        return f"{self.product.name} ({self.quantity}) - Sale {self.sale.id}"