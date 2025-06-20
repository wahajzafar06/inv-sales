from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.forms import inlineformset_factory
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import Purchase, PurchaseItem
from supplier.models import Supplier
from product.models import Product
from django import forms
import logging
from decimal import Decimal, ROUND_HALF_UP

logger = logging.getLogger(__name__)

class PurchaseForm(forms.ModelForm):
    class Meta:
        model = Purchase
        fields = [
            'supplier', 'challan_no', 'purchase_date', 'details', 'purchase_discount',
            'total_discount', 'total_vat', 'grand_total', 'paid_amount', 'due_amount',
            'payment_type'
        ]
        widgets = {
            'purchase_date': forms.DateInput(attrs={'type': 'date'}),
            'details': forms.Textarea(attrs={'rows': 4}),
            'total_discount': forms.NumberInput(attrs={'readonly': 'readonly'}),
            'total_vat': forms.NumberInput(attrs={'readonly': 'readonly'}),
            'grand_total': forms.NumberInput(attrs={'readonly': 'readonly'}),
            'due_amount': forms.NumberInput(attrs={'step': '0.01', 'min': 0}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['supplier'].queryset = Supplier.objects.all()
        self.fields['supplier'].empty_label = "Select Supplier"

    def clean_supplier(self):
        supplier_data = self.cleaned_data['supplier']
        if not supplier_data:
            raise forms.ValidationError("Supplier is required.")
        return supplier_data

class PurchaseItemForm(forms.ModelForm):
    product = forms.ModelChoiceField(
        queryset=Product.objects.all(),
        empty_label="Select Product",
        widget=forms.Select(attrs={'class': 'product-select'})
    )

    class Meta:
        model = PurchaseItem
        fields = [
            'product', 'quantity', 'rate', 'discount_percent',
            'discount_value', 'vat_percent', 'vat_value', 'total',
            'batch_no', 'expiry_date'
        ]
        widgets = {
            'quantity': forms.NumberInput(attrs={'min': 1, 'step': '1'}),
            'rate': forms.NumberInput(attrs={'step': '0.01', 'min': 0}),
            'discount_percent': forms.NumberInput(attrs={'step': '0.01', 'min': 0, 'max': 100}),
            'vat_percent': forms.NumberInput(attrs={'step': '0.01', 'min': 0, 'max': 100}),
            'discount_value': forms.NumberInput(attrs={'readonly': 'readonly'}),
            'vat_value': forms.NumberInput(attrs={'readonly': 'readonly'}),
            'total': forms.NumberInput(attrs={'readonly': 'readonly'}),
            'batch_no': forms.TextInput(),
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product'].required = True

    def clean(self):
        cleaned_data = super().clean()
        product = cleaned_data.get('product')
        quantity = cleaned_data.get('quantity', 0)
        rate = cleaned_data.get('rate', 0)
        discount_percent = cleaned_data.get('discount_percent', 0)
        vat_percent = cleaned_data.get('vat_percent', 0)

        if not product:
            raise forms.ValidationError("Product is required.")

        subtotal = Decimal(quantity) * Decimal(str(rate))
        discount_value = (subtotal * Decimal(str(discount_percent)) / Decimal('100')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        vat_value = ((subtotal - discount_value) * Decimal(str(vat_percent)) / Decimal('100')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        total = (subtotal - discount_value + vat_value).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        cleaned_data['discount_value'] = discount_value
        cleaned_data['vat_value'] = vat_value
        cleaned_data['total'] = total
        return cleaned_data

class PurchaseListView(ListView):
    model = Purchase
    template_name = 'manage_purchase.html'
    context_object_name = 'purchases'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['updated_purchase'] = self.request.GET.get('updated_purchase')
        return context

class PurchaseCreateView(CreateView):
    model = Purchase
    form_class = PurchaseForm
    template_name = 'add_purchase.html'
    success_url = reverse_lazy('manage_purchase')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        PurchaseItemFormSet = inlineformset_factory(
            Purchase, PurchaseItem, form=PurchaseItemForm, extra=1, can_delete=True
        )
        if self.request.POST:
            context['formset'] = PurchaseItemFormSet(self.request.POST)
        else:
            context['formset'] = PurchaseItemFormSet()
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        if form.is_valid() and formset.is_valid():
            self.object = form.save(commit=False)
            self.object.supplier = form.cleaned_data['supplier']
            self.object.save()
            formset.instance = self.object
            formset.save()

            # Recalculate summary fields
            items_total = sum(item.total for item in self.object.items.all())
            total_discount = sum(item.discount_value for item in self.object.items.all()) + form.cleaned_data['purchase_discount']
            total_vat = sum(item.vat_value for item in self.object.items.all())
            grand_total = items_total - form.cleaned_data['purchase_discount']
            paid_amount = form.cleaned_data.get('paid_amount', grand_total)  # Fix: Use form data
            due_amount = form.cleaned_data.get('due_amount', Decimal('0'))

            self.object.total_discount = total_discount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            self.object.total_vat = total_vat.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            self.object.grand_total = grand_total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            self.object.paid_amount = paid_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            self.object.due_amount = due_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            self.object.save()

            messages.success(self.request, f"Purchase {self.object.challan_no} added successfully.")
            return redirect(self.get_success_url())
        else:
            logger.error(f"Form errors: {form.errors}, Formset errors: {formset.errors}")
            return self.render_to_response(self.get_context_data(form=form))

class PurchaseUpdateView(UpdateView):
    model = Purchase
    form_class = PurchaseForm
    template_name = 'add_purchase.html'
    success_url = reverse_lazy('manage_purchase')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        PurchaseItemFormSet = inlineformset_factory(
            Purchase, PurchaseItem, form=PurchaseItemForm, extra=1, can_delete=True
        )
        if self.request.POST:
            context['formset'] = PurchaseItemFormSet(self.request.POST, instance=self.object)
        else:
            context['formset'] = PurchaseItemFormSet(instance=self.object)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        if form.is_valid() and formset.is_valid():
            self.object = form.save(commit=False)
            self.object.supplier = form.cleaned_data['supplier']
            self.object.save()
            formset.instance = self.object
            formset.save()

            # Recalculate summary fields
            items_total = sum(item.total for item in self.object.items.all())
            total_discount = sum(item.discount_value for item in self.object.items.all()) + form.cleaned_data['purchase_discount']
            total_vat = sum(item.vat_value for item in self.object.items.all())
            grand_total = items_total - form.cleaned_data['purchase_discount']
            paid_amount = form.cleaned_data['paid_amount']
            due_amount = form.cleaned_data.get('due_amount', Decimal('0'))

            self.object.total_discount = total_discount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            self.object.total_vat = total_vat.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            self.object.grand_total = grand_total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            self.object.paid_amount = paid_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            self.object.due_amount = due_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            self.object.save()

            messages.success(self.request, f"Purchase {self.object.challan_no} updated successfully.")
            return redirect(self.get_success_url())
        else:
            logger.error(f"Form errors: {form.errors}, Formset errors: {formset.errors}")
            return self.render_to_response(self.get_context_data(form=form))

class PurchaseDeleteView(DeleteView):
    model = Purchase
    template_name = 'purchase_confirm_delete.html'
    success_url = reverse_lazy('manage_purchase')

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        challan_no = self.object.challan_no
        self.object.delete()
        messages.success(request, f"Purchase {challan_no} deleted successfully.")
        return redirect(self.success_url)

def purchase_detail_view(request, purchase_id):
    purchase = get_object_or_404(Purchase, id=purchase_id)
    context = {'purchase': purchase}
    return render(request, 'purchase_detail.html', context)