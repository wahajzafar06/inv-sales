from django.shortcuts import render, redirect, get_object_or_404
from .models import Customer

# Create your views here.
def add_customer(request):
    if request.method == 'POST':
        customer_name = request.POST.get('customer_name')
        email = request.POST.get('email')
        address = request.POST.get('address')
        phone = request.POST.get('phone')
        fax = request.POST.get('fax')
        state = request.POST.get('state')
        country = request.POST.get('country')
        mobile = request.POST.get('mobile')
        vat_no = request.POST.get('vat_no')
        cr_no = request.POST.get('cr_no')
        address2 = request.POST.get('address2')
        city = request.POST.get('city')
        zip_code = request.POST.get('zip_code')

        if customer_name:
            Customer.objects.create(
                customer_name=customer_name,
                email=email,
                address=address,
                phone=phone,
                fax=fax,
                state=state,
                country=country,
                mobile=mobile,
                vat_no=vat_no,
                cr_no=cr_no,
                address2=address2,
                city=city,
                zip_code=zip_code
            )
            request.session['updated_customer'] = {'name': customer_name}
        return redirect('customer_list')
    return render(request, 'add_customer.html')

def customer_list(request):
    customers = Customer.objects.all()
    updated_customer = request.session.pop('updated_customer', None)
    deleted_customer = request.session.pop('deleted_customer', None)
    return render(request, 'customer_list.html', {
        'customers': customers,
        'updated_customer': updated_customer,
        'deleted_customer': deleted_customer
    })

def update_customer(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        customer.customer_name = request.POST.get('customer_name')
        customer.email = request.POST.get('email')
        customer.address = request.POST.get('address')
        customer.phone = request.POST.get('phone')
        customer.fax = request.POST.get('fax')
        customer.state = request.POST.get('state')
        customer.country = request.POST.get('country')
        customer.mobile = request.POST.get('mobile')
        customer.vat_no = request.POST.get('vat_no')
        customer.cr_no = request.POST.get('cr_no')
        customer.address2 = request.POST.get('address2')
        customer.city = request.POST.get('city')
        customer.zip_code = request.POST.get('zip_code')
        customer.save()
        request.session['updated_customer'] = {
            'id': customer.id,
            'name': customer.customer_name
        }
        return redirect('customer_list')
    return render(request, 'add_customer.html', {'customer': customer})

def delete_customer(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        customer_name = customer.customer_name
        customer.delete()
        request.session['deleted_customer'] = customer_name
        return redirect('customer_list')
    return redirect('customer_list')