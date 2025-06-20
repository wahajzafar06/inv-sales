from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from .models import Supplier

def supplier_list(request):
    query = request.GET.get('q', '')
    suppliers = Supplier.objects.filter(supplier_name__icontains=query) if query else Supplier.objects.all().order_by('supplier_name')
    paginator = Paginator(suppliers, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    updated_supplier = request.session.pop('updated_supplier', None)
    deleted_supplier = request.session.pop('deleted_supplier', None)
    
    return render(request, 'supplier_list.html', {
        'suppliers': page_obj,
        'query': query,
        'updated_supplier': updated_supplier,
        'deleted_supplier': deleted_supplier,
    })

def add_supplier(request):
    if request.method == 'POST':
        supplier_name = request.POST.get('supplier_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address1 = request.POST.get('address1')
        fax = request.POST.get('fax')
        state = request.POST.get('state')
        country = request.POST.get('country')
        mobile = request.POST.get('mobile')
        vat = request.POST.get('vat')
        address2 = request.POST.get('address2')
        city = request.POST.get('city')
        zip = request.POST.get('zip')

        if supplier_name:
            supplier = Supplier.objects.create(
                supplier_name=supplier_name,
                email=email,
                phone=phone,
                address1=address1,
                fax=fax,
                state=state,
                country=country,
                mobile=mobile,
                vat=vat,
                address2=address2,
                city=city,
                zip=zip,
                balance=0.00
            )
            request.session['updated_supplier'] = {'name': supplier.supplier_name}
        return redirect('supplier_list')
    
    # For GET request, check if we're updating an existing supplier
    supplier_id = request.GET.get('id')
    if supplier_id:
        supplier = get_object_or_404(Supplier, pk=supplier_id)
        return render(request, 'add_supplier.html', {'supplier': supplier})
    
    return render(request, 'add_supplier.html')

def update_supplier(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    
    if request.method == 'POST':
        supplier.supplier_name = request.POST.get('supplier_name')
        supplier.email = request.POST.get('email')
        supplier.phone = request.POST.get('phone')
        supplier.address1 = request.POST.get('address1')
        supplier.fax = request.POST.get('fax')
        supplier.state = request.POST.get('state')
        supplier.country = request.POST.get('country')
        supplier.mobile = request.POST.get('mobile')
        supplier.vat = request.POST.get('vat')
        supplier.address2 = request.POST.get('address2')
        supplier.city = request.POST.get('city')
        supplier.zip = request.POST.get('zip')
        supplier.save()
        
        request.session['updated_supplier'] = {
            'id': supplier.id,
            'name': supplier.supplier_name
        }
        return redirect('supplier_list')
    
    # For GET request, render the form with supplier data
    return render(request, 'add_supplier.html', {'supplier': supplier})

def delete_supplier(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    
    if request.method == 'POST':
        supplier_name = supplier.supplier_name
        supplier.delete()
        request.session['deleted_supplier'] = supplier_name
        return redirect('supplier_list')
    
    return redirect('supplier_list')

def dashboard(request):
    return render(request, 'dashboard.html')