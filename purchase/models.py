from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from supplier.models import Supplier
from product.models import Product

class Purchase(models.Model):
    PAYMENT_TYPES = (
        ('CASH', 'Cash'),
        ('CREDIT', 'Credit'),
        ('BANK', 'Bank Transfer'),
    )

    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='purchases')
    challan_no = models.CharField(max_length=50, unique=True)
    purchase_date = models.DateField()
    details = models.TextField(blank=True)
    purchase_discount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00,
        validators=[MinValueValidator(0.00)]
    )
    total_discount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00,
        validators=[MinValueValidator(0.00)]
    )
    total_vat = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00,
        validators=[MinValueValidator(0.00)]
    )
    grand_total = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00,
        validators=[MinValueValidator(0.00)]
    )
    paid_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00,
        validators=[MinValueValidator(0.00)]
    )
    due_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00,
        validators=[MinValueValidator(0.00)]
    )
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES, default='CASH')

    def __str__(self):
        return f"Purchase {self.challan_no} - {self.supplier.supplier_name}"

    def save(self, *args, **kwargs):
        if not self.pk:
            items = self.items.all() if self.pk else []
            self.total_discount = sum(item.discount_value for item in items) + self.purchase_discount
            self.total_vat = sum(item.vat_value for item in items)
            self.grand_total = sum(item.total for item in items) + self.total_vat - self.purchase_discount
            self.due_amount = self.grand_total - self.paid_amount
        super().save(*args, **kwargs)

class PurchaseItem(models.Model):
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)  # Allow null temporarily
    item_name = models.CharField(max_length=255)
    stock = models.CharField(max_length=100, blank=True)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    batch_no = models.CharField(max_length=50, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    rate = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    discount_percent = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00,
        validators=[MinValueValidator(0.00), MaxValueValidator(100.00)]
    )
    discount_value = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00,
        validators=[MinValueValidator(0.00)]
    )
    vat_percent = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00,
        validators=[MinValueValidator(0.00), MaxValueValidator(100.00)]
    )
    vat_value = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00,
        validators=[MinValueValidator(0.00)]
    )
    total = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00,
        validators=[MinValueValidator(0.00)]
    )

    def __str__(self):
        return f"{self.item_name} (Purchase {self.purchase.challan_no})"

    def save(self, *args, **kwargs):
        self.discount_value = (self.rate * self.quantity * self.discount_percent) / 100
        subtotal = (self.rate * self.quantity) - self.discount_value
        self.vat_value = (subtotal * self.vat_percent) / 100
        self.total = subtotal + self.vat_value
        super().save(*args, **kwargs)