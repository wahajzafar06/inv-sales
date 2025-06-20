from django.shortcuts import render
from product.models import Product
from purchase.models import PurchaseItem
from sale.models import SaleItem
from django.db.models import Sum, F, Value, DecimalField
from django.db.models.functions import Coalesce
from django.db.models.expressions import ExpressionWrapper

def stock_report(request):
    products = Product.objects.annotate(
        in_qty=Coalesce(Sum('purchaseitem__quantity'), Value(0), output_field=DecimalField()),
        out_qty=Coalesce(Sum('saleitem__quantity'), Value(0), output_field=DecimalField()),
        stock=Coalesce(F('in_qty') - F('out_qty'), Value(0), output_field=DecimalField()),
        stock_sale_price=ExpressionWrapper(
            F('stock') * F('sale_price'),
            output_field=DecimalField(max_digits=10, decimal_places=2)
        ),
        stock_purchase_price=ExpressionWrapper(
            F('stock') * F('cost_price'),
            output_field=DecimalField(max_digits=10, decimal_places=2)
        )
    ).values(
        'id', 'name', 'model', 'sale_price', 'cost_price',
        'in_qty', 'out_qty', 'stock', 'stock_sale_price', 'stock_purchase_price'
    )

    stock_data = [
        {
            'product': {
                'id': p['id'],
                'name': p['name'],
                'model': p['model'],
                'sale_price': p['sale_price'],
                'cost_price': p['cost_price']
            },
            'in_qty': p['in_qty'],
            'out_qty': p['out_qty'],
            'stock': max(0, p['stock']),
            'stock_sale_price': p['stock_sale_price'] or 0,
            'stock_purchase_price': p['stock_purchase_price'] or 0,
        } for p in products
    ]

    total_stock = sum(item['stock'] for item in stock_data)
    total_stock_sale_price = sum(item['stock_sale_price'] for item in stock_data)
    total_stock_purchase_price = sum(item['stock_purchase_price'] for item in stock_data)

    context = {
        'stock_data': stock_data,
        'total_stock': total_stock,
        'total_stock_sale_price': total_stock_sale_price,
        'total_stock_purchase_price': total_stock_purchase_price,
    }
    return render(request, 'stock_report.html', context)