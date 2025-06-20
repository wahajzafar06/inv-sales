from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.forms import inlineformset_factory, BaseInlineFormSet
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import PurchaseOrder, PurchaseOrderItem
from supplier.models import Supplier
from product.models import Product
from decimal import Decimal, ROUND_HALF_UP
import logging
from django import forms
from django.db.models import F
from datetime import datetime

logger = logging.getLogger(__name__)

class PurchaseOrderItemForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrderItem
        fields = [
            'id', 'product', 'stock', 'ordered_quantity', 'received_quantity',
            'unit_price', 'discount_percent', 'discount_value', 'vat_percent', 'vat_value', 'total'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product'].queryset = Product.objects.all()

    def clean(self):
        cleaned_data = super().clean()
        ordered_quantity = cleaned_data.get('ordered_quantity')
        received_quantity = cleaned_data.get('received_quantity')
        if ordered_quantity and received_quantity and received_quantity > ordered_quantity:
            raise forms.ValidationError("Received quantity cannot exceed ordered quantity.")
        return cleaned_data

class PurchaseOrderItemFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        product_ids = []
        for form in self.forms:
            if form.cleaned_data and not form.cleaned_data.get('DELETE'):
                product = form.cleaned_data.get('product')
                if product:
                    if product.id in product_ids:
                        raise forms.ValidationError(f"Product {product.name} is selected multiple times.")
                    product_ids.append(product.id)

class PurchaseOrderListView(ListView):
    model = PurchaseOrder
    template_name = 'manage_purchase_order.html'
    context_object_name = 'purchase_orders'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        purchase_orders = context['purchase_orders']
        for po in purchase_orders:
            po.discrepancy_count = po.discrepancy_count()
        return context

class PurchaseOrderCreateView(CreateView):
    model = PurchaseOrder
    fields = [
        'supplier', 'purchase_date', 'purchase_discount',
        'total_discount', 'total_vat', 'grand_total', 'paid_amount', 'due_amount',
        'payment_type'
    ]
    template_name = 'add_purchase_order.html'
    success_url = reverse_lazy('manage_purchase_order')

    def generate_po_number(self):
        """Generate a unique PO number in the format PO-YYYYMMDD-XXX"""
        today_str = datetime.now().strftime('%Y%m%d')
        last_po_today = PurchaseOrder.objects.filter(
            po_number__startswith=f'PO-{today_str}-'
        ).order_by('-po_number').first()
        
        if last_po_today:
            try:
                last_num = int(last_po_today.po_number.split('-')[-1])
                new_num = last_num + 1
            except (IndexError, ValueError):
                new_num = 1
        else:
            new_num = 1
            
        return f'PO-{today_str}-{new_num:03d}'

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['supplier'].empty_label = "Select Supplier"
        form.fields['purchase_date'].widget = forms.DateInput(
            attrs={'type': 'date', 'class': 'form-control'}
        )
        form.fields['purchase_date'].initial = datetime.now().strftime('%Y-%m-%d')
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        FormSet = inlineformset_factory(
            PurchaseOrder, PurchaseOrderItem,
            form=PurchaseOrderItemForm,
            formset=PurchaseOrderItemFormSet,
            fields=[
                'id', 'product', 'stock', 'ordered_quantity', 'received_quantity',
                'unit_price', 'discount_percent', 'discount_value', 'vat_percent', 'vat_value', 'total'
            ],
            extra=1, can_delete=True,
            widgets={
                'id': forms.HiddenInput(attrs={'class': 'form-control'}),
                'product': forms.HiddenInput(attrs={'class': 'form-control'}),
                'stock': forms.TextInput(attrs={'class': 'form-control'}),
                'ordered_quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'step': 1}),
                'received_quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'step': 1}),
                'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
                'discount_percent': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0, 'max': 100}),
                'discount_value': forms.NumberInput(attrs={'class': 'form-control', 'readonly': True}),
                'vat_percent': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0, 'max': 100}),
                'vat_value': forms.NumberInput(attrs={'class': 'form-control', 'readonly': True}),
                'total': forms.NumberInput(attrs={'class': 'form-control', 'readonly': True}),
            }
        )
        if self.request.POST:
            context['formset'] = FormSet(self.request.POST)
        else:
            context['formset'] = FormSet()
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        if form.is_valid() and formset.is_valid():
            self.object = form.save(commit=False)
            self.object.po_number = self.generate_po_number()
            self.object.save()
            formset.instance = self.object
            formset.save()

            # Calculate totals
            items_total = sum(item.total for item in self.object.items.all())
            total_discount = sum(item.discount_value for item in self.object.items.all()) + form.cleaned_data['purchase_discount']
            total_vat = sum(item.vat_value for item in self.object.items.all())
            grand_total = items_total + total_vat - form.cleaned_data['purchase_discount']
            paid_amount = form.cleaned_data.get('paid_amount', Decimal('0'))
            due_amount = grand_total - paid_amount

            # Update totals
            self.object.total_discount = total_discount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            self.object.total_vat = total_vat.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            self.object.grand_total = grand_total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            self.object.paid_amount = paid_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            self.object.due_amount = due_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            self.object.save()

            # Check for discrepancies
            discrepancies = [item for item in self.object.items.all() if item.received_quantity < item.ordered_quantity]
            if discrepancies:
                messages.warning(self.request, f"Purchase Order {self.object.po_number} created, but some items have outstanding quantities.")
            else:
                messages.success(self.request, f"Purchase Order {self.object.po_number} created successfully.")
            return redirect(self.get_success_url())
        else:
            logger.error(f"Form errors: {form.errors}, Formset errors: {formset.errors}, POST data: {self.request.POST}")
            return self.render_to_response(self.get_context_data(form=form))

class PurchaseOrderUpdateView(UpdateView):
    model = PurchaseOrder
    fields = [
        'supplier', 'purchase_date', 'purchase_discount',
        'total_discount', 'total_vat', 'grand_total', 'paid_amount', 'due_amount',
        'payment_type'
    ]
    template_name = 'update_purchase_order.html'
    success_url = reverse_lazy('manage_purchase_order')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['supplier'].empty_label = "Select Supplier"
        form.fields['purchase_date'].widget = forms.DateInput(
            attrs={'type': 'date', 'class': 'form-control'}
        )
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        FormSet = inlineformset_factory(
            PurchaseOrder, PurchaseOrderItem,
            form=PurchaseOrderItemForm,
            formset=PurchaseOrderItemFormSet,
            fields=[
                'id', 'product', 'stock', 'ordered_quantity', 'received_quantity',
                'unit_price', 'discount_percent', 'discount_value', 'vat_percent', 'vat_value', 'total'
            ],
            extra=0, can_delete=True,
            widgets={
                'id': forms.HiddenInput(attrs={'class': 'form-control'}),
                'product': forms.HiddenInput(attrs={'class': 'form-control'}),
                'stock': forms.TextInput(attrs={'class': 'form-control'}),
                'ordered_quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'step': 1, 'readonly': True}),
                'received_quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'step': 1}),
                'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
                'discount_percent': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0, 'max': 100}),
                'discount_value': forms.NumberInput(attrs={'class': 'form-control', 'readonly': True}),
                'vat_percent': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0, 'max': 100}),
                'vat_value': forms.NumberInput(attrs={'class': 'form-control', 'readonly': True}),
                'total': forms.NumberInput(attrs={'class': 'form-control', 'readonly': True}),
            }
        )
        if self.request.POST:
            context['formset'] = FormSet(self.request.POST, instance=self.object)
        else:
            context['formset'] = FormSet(instance=self.object)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        if form.is_valid() and formset.is_valid():
            self.object = form.save(commit=False)
            self.object.save()
            formset.instance = self.object
            formset.save()

            # Calculate totals
            items_total = sum(item.total for item in self.object.items.all())
            total_discount = sum(item.discount_value for item in self.object.items.all()) + form.cleaned_data['purchase_discount']
            total_vat = sum(item.vat_value for item in self.object.items.all())
            grand_total = items_total + total_vat - form.cleaned_data['purchase_discount']
            paid_amount = form.cleaned_data.get('paid_amount', Decimal('0'))
            due_amount = grand_total - paid_amount

            # Update totals
            self.object.total_discount = total_discount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            self.object.total_vat = total_vat.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            self.object.grand_total = grand_total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            self.object.paid_amount = paid_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            self.object.due_amount = due_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            self.object.save()

            # Check for discrepancies
            discrepancies = [item for item in self.object.items.all() if item.received_quantity < item.ordered_quantity]
            if discrepancies:
                messages.warning(self.request, f"Purchase Order {self.object.po_number} updated, but some items have outstanding quantities.")
            else:
                messages.success(self.request, f"Purchase Order {self.object.po_number} updated successfully.")
            return redirect(self.get_success_url())
        else:
            logger.error(f"Form errors: {form.errors}, Formset errors: {formset.errors}, POST data: {self.request.POST}")
            return self.render_to_response(self.get_context_data(form=form))

class PurchaseOrderDeleteView(DeleteView):
    model = PurchaseOrder
    template_name = 'purchase_order_confirm_delete.html'
    success_url = reverse_lazy('manage_purchase_order')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        order_id = self.object.po_number
        self.object.delete()
        messages.success(request, f'Purchase Order {order_id} deleted successfully.')
        return redirect(self.success_url)

def purchase_order_detail_view(request, pk):
    purchase_order = get_object_or_404(PurchaseOrder, pk=pk)
    discrepancies = [
        item for item in purchase_order.items.all()
        if item.received_quantity < item.ordered_quantity
    ]
    context = {
        'purchase_order': purchase_order,
        'discrepancies': discrepancies
    }
    return render(request, 'purchase_order_detail.html', context)