from django.db import models
from django.db.models import F
from django.core.validators import MinValueValidator, MaxValueValidator
from supplier.models import Supplier
from product.models import Product

class PurchaseOrder(models.Model):
    PAYMENT_TYPES = (
        ('CASH', 'Cash'),
        ('CREDIT', 'Credit'),
        ('BANK', 'Bank Transfer'),
    )

    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.CASCADE,
        related_name='purchase_orders',
        null=True,
        blank=True
    )
    po_number = models.CharField(max_length=50, unique=True, blank=True, null=True)  # New field
    purchase_date = models.DateField(null=True, blank=True)
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
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Generate po_number if not set
        if not self.po_number:
            max_id = PurchaseOrder.objects.aggregate(models.Max('id'))['id__max'] or 0
            self.po_number = f"PO-{max_id + 1:04d}"  # e.g., PO-0001

        # Calculate totals
        items = self.items.all() if self.pk else []
        self.total_discount = sum(item.discount_value for item in items) + self.purchase_discount
        self.total_vat = sum(item.vat_value for item in items)
        self.grand_total = sum(item.total for item in items) + self.total_vat - self.purchase_discount
        self.due_amount = self.grand_total - self.paid_amount
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.po_number or f'PO#{self.id}'} - {self.supplier.supplier_name if self.supplier else 'No Supplier'}"

    def discrepancy_count(self):
        return self.items.filter(received_quantity__lt=F('ordered_quantity')).count()

class PurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    stock = models.CharField(max_length=100, blank=True)
    ordered_quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    received_quantity = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)])
    unit_price = models.DecimalField(
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
        return f"Item for {self.purchase_order.po_number or f'PO#{self.purchase_order.id}'} (Product: {self.product.name if self.product else 'No Product'})"

    def save(self, *args, **kwargs):
        self.discount_value = (self.unit_price * self.ordered_quantity * self.discount_percent) / 100
        subtotal = (self.unit_price * self.ordered_quantity) - self.discount_value
        self.vat_value = (subtotal * self.vat_percent) / 100
        self.total = subtotal + self.vat_value
        super().save(*args, **kwargs)