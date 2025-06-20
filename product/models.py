from django.db import models
from supplier.models import Supplier

class Category(models.Model):
    STATUS_CHOICES = (
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
    )
    name = models.CharField(max_length=100)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)

    def __str__(self):
        return self.name

class Unit(models.Model):
    name = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=[('Active', 'Active'), ('Inactive', 'Inactive')])

    def __str__(self):
        return self.name

class Product(models.Model):
    barcode = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='products img/', blank=True, null=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    serial_number = models.CharField(max_length=100, blank=True)
    model = models.CharField(max_length=100, blank=True)
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE)
    details = models.TextField(blank=True)
    vat_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    def get_stock(self):
        from purchase.models import PurchaseItem
        from sale.models import SaleItem
        total_purchased = PurchaseItem.objects.filter(product=self).aggregate(
            total=models.Sum('quantity')
        )['total'] or 0
        total_sold = SaleItem.objects.filter(product=self).aggregate(
            total=models.Sum('quantity')
        )['total'] or 0
        return max(0, total_purchased - total_sold)

    def __str__(self):
        return self.name