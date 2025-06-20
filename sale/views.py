from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from decimal import Decimal, ROUND_HALF_UP
import logging
from .models import Sale, SaleItem
from customer.models import Customer
from product.models import Product, Unit

logger = logging.getLogger(__name__)

def new_sale(request):
    if request.method == 'POST':
        logger.info(f"Full POST data: {request.POST}")
        customer_id = request.POST.get('customer')
        sale_discount = request.POST.get('sale_discount', '0.00')
        shipping_cost = request.POST.get('shipping_cost', '0.00')
        paid_amount = request.POST.get('paid_amount', '0.00')
        total_forms = int(request.POST.get('items-TOTAL_FORMS', 0))

        errors = {
            'customer': None,
            'general': None,
            'items': [],
        }

        # Validate customer
        customer = None
        if not customer_id:
            errors['customer'] = "Please select a customer."
        else:
            try:
                customer = Customer.objects.get(id=customer_id)
            except Customer.DoesNotExist:
                errors['customer'] = "Invalid customer selected."

        # Extract and validate items
        items_data = []
        for i in range(total_forms):
            product_id = request.POST.get(f'items-{i}-product')
            product_name = request.POST.get(f'items-{i}-product_name', '')
            quantity = request.POST.get(f'items-{i}-quantity', '0.00')
            rate = request.POST.get(f'items-{i}-rate', '0.00')
            discount_percent = request.POST.get(f'items-{i}-discount_percent', '0.00')
            discount_value = request.POST.get(f'items-{i}-discount_value', '0.00')
            vat_percent = request.POST.get(f'items-{i}-vat_percent', '0.00')
            vat_value = request.POST.get(f'items-{i}-vat_value', '0.00')
            total = request.POST.get(f'items-{i}-total', '0.00')
            description = request.POST.get(f'items-{i}-description', '')
            available_quantity = request.POST.get(f'items-{i}-available_quantity', '0.00')
            unit = request.POST.get(f'items-{i}-unit', '')

            item_errors = {}
            product = None
            if product_id:
                product = Product.objects.filter(id=product_id).first()
            if not product:
                item_errors['product'] = f"Invalid product selected for item {i+1}."
            else:
                try:
                    qty = Decimal(quantity or '0.00')
                    stock = product.get_stock()
                    if qty <= 0:
                        item_errors['quantity'] = f"Quantity must be positive for item {i+1}."
                    elif qty > stock:
                        item_errors['quantity'] = f"Insufficient stock for {product.name} (Available: {stock})."
                except (ValueError, TypeError):
                    item_errors['quantity'] = f"Invalid quantity for item {i+1}."

            # Recalculate discount_value, vat_value, and total
            try:
                rate = Decimal(rate or '0.00')
                disc_percent = Decimal(discount_percent or '0.00')
                vat_percent = Decimal(vat_percent or '0.00')

                subtotal = qty * rate
                discount_value = (subtotal * disc_percent / 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                vat_value = ((subtotal - discount_value) * vat_percent / 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                total = (subtotal - discount_value + vat_value).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            except (ValueError, TypeError):
                item_errors['calculation'] = f"Invalid numerical values for item {i+1}."

            errors['items'].append(item_errors if item_errors else None)
            items_data.append({
                'prod_id': product_id,
                'product_name': product_name or '',
                'quantity': qty,
                'rate': rate,
                'discount_percent': disc_percent,
                'discount_value': discount_value,
                'vat_percent': vat_percent,
                'vat_value': vat_value,
                'total': total,
                'description': description or '',
                'available_quantity': Decimal(available_quantity or '0.00'),
                'unit': unit or '',
            })

        valid_items = [item for item in items_data if item['prod_id'] and not errors['items'][items_data.index(item)]]
        logger.info(f"Valid items: {valid_items}")
        if not valid_items:
            errors['items'] = ['At least one valid item is required.']

        try:
            sale_discount = Decimal(sale_discount or '0.00')
            shipping_cost = Decimal(shipping_cost or '0.00')
            paid_amount = Decimal(paid_amount or '0.00')
            # Recalculate summary fields
            items_total = sum(item['total'] for item in valid_items)
            total_discount = sum(item['discount_value'] for item in valid_items) + sale_discount
            total_vat = sum(item['vat_value'] for item in valid_items)
            grand_total = items_total
            net_total = grand_total - sale_discount + shipping_cost
            logger.info(f"Calculated: items_total={items_total}, total_discount={total_discount}, net_total={net_total}")
        except (ValueError, TypeError):
            errors['general'] = "Invalid numerical values provided."

        if not errors['customer'] and not errors['general'] and all(e is None for e in errors['items']) and valid_items:
            try:
                with transaction.atomic():
                    sale = Sale(
                        customer=customer,
                        sale_discount=sale_discount,
                        shipping_cost=shipping_cost,
                        total_discount=total_discount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
                        total_vat=total_vat.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
                        grand_total=grand_total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
                        net_total=net_total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
                        paid_amount=paid_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
                    )
                    sale.save()
                    logger.info(f"Sale saved: ID={sale.id}")

                    for item_data in valid_items:
                        product = Product.objects.get(id=item_data['prod_id'])
                        if item_data['quantity'] > product.get_stock():
                            raise ValueError(f"Insufficient stock for {product.name}")
                        sale_item = SaleItem(
                            sale=sale,
                            product=product,
                            quantity=item_data['quantity'],
                            rate=item_data['rate'],
                            discount_percent=item_data['discount_percent'],
                            discount_value=item_data['discount_value'],
                            vat_percent=item_data['vat_percent'],
                            vat_value=item_data['vat_value'],
                            total=item_data['total'],
                            description=item_data['description'],
                            available_quantity=product.get_stock(),
                            unit=product.unit,
                        )
                        sale_item.save()
                        logger.info(f"SaleItem saved: Product={product.name}, Quantity={item_data['quantity']}")

                    logger.info(f"Sale {sale.id} created successfully for customer {customer.customer_name}")
                    messages.success(request, "Sale created successfully!")
                    return redirect('manage_sale')
            except Exception as e:
                logger.exception(f"Transaction failed: {str(e)}")
                errors['general'] = f"An error occurred while saving the sale: {str(e)}"

        logger.error(f"Validation errors: {errors}")
        return render(request, 'new_sale.html', {
            'customers': Customer.objects.all(),
            'all_products': Product.objects.all(),
            'errors': errors,
            'form_data': {
                'customer': customer_id or '',
                'sale_discount': sale_discount,
                'shipping_cost': shipping_cost,
                'paid_amount': paid_amount,
                'date': timezone.now().strftime('%Y-%m-%dT%H:%M'),
                'items': items_data,
                'total_discount': total_discount,
                'total_vat': total_vat,
                'grand_total': grand_total,
                'net_total': net_total,
            },
        })

    customers = Customer.objects.all()
    products = Product.objects.all()
    logger.info(f"GET request: {[f'cust_id: {cust.id}, cust_name: {cust.customer_name}' for cust in customers]}")
    return render(request, 'new_sale.html', {
        'customers': customers,
        'all_products': products,
        'form_data': {
            'items': [{
                'prod_id': '',
                'product_name': '',
                'quantity': Decimal('1.00'),
                'rate': Decimal('0.00'),
                'discount_percent': Decimal('0.00'),
                'discount_value': Decimal('0.00'),
                'vat_percent': Decimal('0.00'),
                'vat_value': Decimal('0.00'),
                'total': Decimal('0.00'),
                'description': '',
                'available_quantity': Decimal('0.00'),
                'unit': '',
            }],
            'date': timezone.now().strftime('%Y-%m-%dT%H:%M'),
            'sale_discount': Decimal('0.00'),
            'shipping_cost': Decimal('0.00'),
            'paid_amount': Decimal('0.00'),
            'total_discount': Decimal('0.00'),
            'total_vat': Decimal('0.00'),
            'grand_total': Decimal('0.00'),
            'net_total': Decimal('0.00'),
        },
        'errors': {
            'customer': None,
            'general': None,
            'items': [],
        },
    })

def manage_sale(request):
    sales = Sale.objects.all().order_by('-id')
    logger.info(f"Sales fetched: {[f'sale_id: {s.id}, cust_name: {s.customer.customer_name}' for s in sales]}")
    return render(request, 'manage_sale.html', {
        'orders': sales,
        'sales_data': [{
            'id': sale.id,
            'customer_name': sale.customer.customer_name if sale.customer else 'Unknown',
            'date': sale.date,
            'total_discount': sale.total_discount,
            'total_vat': sale.total_vat,
            'grand_total': sale.grand_total,
            'net_total': sale.net_total,
            'paid_amount': sale.paid_amount,
            'sale_by': request.user.username if request.user.is_authenticated else 'Admin',
            'items': [{
                'product_name': item.product.name if item.product else 'Unknown',
                'quantity': item.quantity,
                'rate': item.rate,
                'discount_percent': item.discount_percent,
                'discount_value': item.discount_value,
                'vat_percent': item.vat_percent,
                'vat_value': item.vat_value,
                'total': item.total,
                'description': item.description or '-',
                'unit': item.unit.name if item.unit else '-',
            } for item in sale.items.all()]
        } for sale in sales]
    })

def sale_detail(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    sale_data = {
        'id': sale.id,
        'customer_name': sale.customer.customer_name if sale.customer else 'Unknown',
        'customer_address': sale.customer.address if sale.customer else '-',
        'customer_email': sale.customer.email if sale.customer else '-',
        'customer_mobile': sale.customer.mobile if sale.customer else '-',
        'customer_vat_number': sale.customer.vat_no if sale.customer else '-',
        'date': sale.date,
        'sale_discount': sale.sale_discount,
        'shipping_cost': sale.shipping_cost,
        'total_discount': sale.total_discount,
        'total_vat': sale.total_vat,
        'grand_total': sale.grand_total,
        'net_total': sale.net_total,
        'paid_amount': sale.paid_amount,
        'items': [{
            'product_name': item.product.name if item.product else 'Unknown',
            'quantity': item.quantity,
            'rate': item.rate,
            'discount_percent': item.discount_percent,
            'discount_value': item.discount_value,
            'vat_percent': item.vat_percent,
            'vat_value': item.vat_value,
            'total': item.total,
            'description': item.description or '-',
            'unit': item.unit.name if item.unit else '-',
        } for item in sale.items.all()]
    }
    logger.info(f"Sale detail: ID={sale.id}, customer={sale_data['customer_name']}, "
                f"address={sale_data['customer_address']}, email={sale_data['customer_email']}, "
                f"mobile={sale_data['customer_mobile']}, vat_no={sale_data['customer_vat_number']}, "
                f"items={len(sale_data['items'])}")
    return render(request, 'sale_detail.html', {'order': sale, 'sale_data': sale_data})