from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import IntegrityError
from .models import Category, Unit, Product
from supplier.models import Supplier
import logging

# Set up logging for debugging
logger = logging.getLogger(__name__)

def add_category(request):
    if request.method == 'POST':
        name = request.POST.get('category_name', '').strip()
        status = request.POST.get('status')
        if name and status in ['Active', 'Inactive']:
            try:
                Category.objects.create(name=name, status=status)
                messages.success(request, "Category added successfully!")
            except IntegrityError as e:
                logger.error(f"Error adding category: {e}")
                messages.error(request, "Failed to add category. Please try again.")
        else:
            messages.error(request, "Category name and valid status are required.")
        return redirect('category_list')
    return render(request, 'add_category.html')

def category_list(request):
    categories = Category.objects.all()
    updated_category = request.session.pop('updated_category', None)
    deleted_category = request.session.pop('deleted_category', None)
    return render(request, 'category_list.html', {
        'categories': categories,
        'updated_category': updated_category,
        'deleted_category': deleted_category
    })

def update_category(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        name = request.POST.get('category_name', '').strip()
        status = request.POST.get('status')
        if name and status in ['Active', 'Inactive']:
            try:
                category.name = name
                category.status = status
                category.save()
                request.session['updated_category'] = {
                    'id': category.id,
                    'name': category.name,
                    'status': category.status
                }
                messages.success(request, "Category updated successfully!")
                return redirect('category_list')
            except IntegrityError as e:
                logger.error(f"Error updating category: {e}")
                messages.error(request, "Failed to update category. Please try again.")
        else:
            messages.error(request, "Category name and valid status are required.")
    return render(request, 'add_category.html', {'category': category})

def delete_category(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        try:
            category_name = category.name
            category.delete()
            request.session['deleted_category'] = category_name
            messages.success(request, f"Category '{category_name}' deleted successfully!")
            return redirect('category_list')
        except Exception as e:
            logger.error(f"Error deleting category: {e}")
            messages.error(request, "Failed to delete category. It may be in use.")
    return redirect('category_list')

def add_unit(request):
    if request.method == 'POST':
        name = request.POST.get('unit_name', '').strip()
        status = request.POST.get('status')
        if name and status in ['Active', 'Inactive']:
            try:
                unit = Unit.objects.create(name=name, status=status)
                request.session['updated_unit'] = {
                    'id': unit.id,
                    'name': unit.name,
                    'status': unit.status
                }
                messages.success(request, "Unit added successfully!")
            except IntegrityError as e:
                logger.error(f"Error adding unit: {e}")
                messages.error(request, "Failed to add unit. Please try again.")
        else:
            messages.error(request, "Unit name and valid status are required.")
        return redirect('unit_list')
    return render(request, 'add_unit.html')

def unit_list(request):
    units = Unit.objects.all()
    updated_unit = request.session.pop('updated_unit', None)
    return render(request, 'unit_list.html', {
        'units': units,
        'updated_unit': updated_unit
    })

def update_unit(request, pk):
    unit = get_object_or_404(Unit, pk=pk)
    if request.method == 'POST':
        name = request.POST.get('unit_name', '').strip()
        status = request.POST.get('status')
        if name and status in ['Active', 'Inactive']:
            try:
                unit.name = name
                unit.status = status
                unit.save()
                request.session['updated_unit'] = {
                    'id': unit.id,
                    'name': unit.name,
                    'status': unit.status
                }
                messages.success(request, "Unit updated successfully!")
                return redirect('unit_list')
            except IntegrityError as e:
                logger.error(f"Error updating unit: {e}")
                messages.error(request, "Failed to update unit. Please try again.")
        else:
            messages.error(request, "Unit name and valid status are required.")
    return render(request, 'add_unit.html', {'unit': unit})

def delete_unit(request, pk):
    unit = get_object_or_404(Unit, pk=pk)
    if request.method == 'POST':
        try:
            unit_name = unit.name
            unit.delete()
            request.session['deleted_unit'] = unit_name
            messages.success(request, f"Unit '{unit_name}' deleted successfully!")
            return redirect('unit_list')
        except Exception as e:
            logger.error(f"Error deleting unit: {e}")
            messages.error(request, "Failed to delete unit. It may be in use.")
    return redirect('unit_list')

def add_product(request):
    if request.method == 'POST':
        # Extract form data
        barcode = request.POST.get('barcode', '').strip()
        product_name = request.POST.get('product_name', '').strip()
        category_id = request.POST.get('category', '').strip()
        sale_price = request.POST.get('sale_price', '').strip()
        cost_price = request.POST.get('cost_price', '').strip()
        image = request.FILES.get('image')
        supplier_id = request.POST.get('supplier', '').strip()
        serial_number = request.POST.get('serial_number', '').strip()
        model = request.POST.get('model', '').strip()
        unit_id = request.POST.get('unit', '').strip()
        details = request.POST.get('details', '').strip()
        vat_percentage = request.POST.get('vat_percentage', '0.00').strip()

        # Initialize errors dictionary
        errors = {}

        # Validate required fields
        if not barcode:
            errors['barcode'] = "Barcode is required."
        if not product_name:
            errors['product_name'] = "Product name is required."
        if not category_id:
            errors['category'] = "Please select a category."
        if not sale_price:
            errors['sale_price'] = "Sale price is required."
        if not cost_price:
            errors['cost_price'] = "Cost price is required."
        if not supplier_id:
            errors['supplier'] = "Please select a supplier."
        if not unit_id:
            errors['unit'] = "Please select a unit."
        if not image:
            errors['image'] = "Image is required."

        # Validate numeric fields
        try:
            sale_price = float(sale_price)
            cost_price = float(cost_price)
            vat_percentage = float(vat_percentage)
            if sale_price < 0:
                errors['sale_price'] = "Sale price cannot be negative."
            if cost_price < 0:
                errors['cost_price'] = "Cost price cannot be negative."
            if vat_percentage < 0:
                errors['vat_percentage'] = "VAT percentage cannot be negative."
        except (ValueError, TypeError):
            if 'sale_price' not in errors:
                errors['sale_price'] = "Sale price must be a valid number."
            if 'cost_price' not in errors:
                errors['cost_price'] = "Cost price must be a valid number."
            if 'vat_percentage' not in errors:
                errors['vat_percentage'] = "VAT percentage must be a valid number."

        # Validate barcode uniqueness
        if barcode and not errors.get('barcode'):
            if Product.objects.filter(barcode=barcode).exists():
                errors['barcode'] = "A product with this barcode already exists."

        # Validate foreign keys
        category = None
        if category_id and not errors.get('category'):
            try:
                category = Category.objects.get(id=category_id, status='Active')
            except (Category.DoesNotExist, ValueError):
                errors['category'] = "Selected category is invalid or inactive."

        supplier = None
        if supplier_id and not errors.get('supplier'):
            try:
                supplier = Supplier.objects.get(id=supplier_id)
            except (Supplier.DoesNotExist, ValueError):
                errors['supplier'] = "Selected supplier is invalid."

        unit = None
        if unit_id and not errors.get('unit'):
            try:
                unit = Unit.objects.get(id=unit_id, status='Active')
            except (Unit.DoesNotExist, ValueError):
                errors['unit'] = "Selected unit is invalid or inactive."

        # Log form data for debugging
        logger.debug(f"Form data: barcode={barcode}, category_id={category_id}, supplier_id={supplier_id}, unit_id={unit_id}")

        # If no errors, attempt to create the product
        if not errors:
            try:
                product = Product.objects.create(
                    barcode=barcode,
                    name=product_name,
                    category=category,
                    sale_price=sale_price,
                    cost_price=cost_price,
                    image=image,
                    supplier=supplier,
                    serial_number=serial_number,
                    model=model,
                    unit=unit,
                    details=details,
                    vat_percentage=vat_percentage
                )
                logger.info(f"Product '{product.name}' created successfully with barcode '{barcode}'")
                # Store product fields in session for update
                request.session[f'product_{product.id}'] = {
                    'barcode': barcode,
                    'product_name': product_name,
                    'category': category_id,
                    'category_name': category.name if category else '',
                    'sale_price': str(sale_price),
                    'cost_price': str(cost_price),
                    'supplier': supplier_id,
                    'supplier_name': supplier.supplier_name if supplier else '',
                    'serial_number': serial_number,
                    'model': model,
                    'unit': unit_id,
                    'unit_name': unit.name if unit else '',
                    'details': details,
                    'vat_percentage': str(vat_percentage),
                }
                request.session['updated_product'] = {'name': product.name}
                messages.success(request, f"Product '{product.name}' added successfully!")
                return redirect('product_list')
            except IntegrityError as e:
                logger.error(f"IntegrityError while creating product: {e}")
                errors['general'] = f"Failed to add product due to a database error: {str(e)}"
            except Exception as e:
                logger.error(f"Unexpected error while creating product: {e}")
                errors['general'] = "An unexpected error occurred. Please try again."

        # If errors exist, re-render the form with errors and submitted data
        form_data = {
            'barcode': barcode,
            'product_name': product_name,
            'category': category_id,
            'category_name': category.name if category else '',
            'sale_price': sale_price,
            'cost_price': cost_price,
            'supplier': supplier_id,
            'supplier_name': supplier.supplier_name if supplier else '',
            'serial_number': serial_number,
            'model': model,
            'unit': unit_id,
            'unit_name': unit.name if unit else '',
            'details': details,
            'vat_percentage': vat_percentage,
        }
        messages.error(request, "Please correct the errors below.")
        return render(request, 'add_product.html', {
            'categories': Category.objects.filter(status='Active'),
            'suppliers': Supplier.objects.all(),
            'units': Unit.objects.filter(status='Active'),
            'errors': errors,
            'form_data': form_data,
        })

    # For GET request, render empty form
    return render(request, 'add_product.html', {
        'categories': Category.objects.filter(status='Active'),
        'suppliers': Supplier.objects.all(),
        'units': Unit.objects.filter(status='Active'),
    })

def product_list(request):
    products = Product.objects.all()
    updated_product = request.session.pop('updated_product', None)
    deleted_product = request.session.pop('deleted_product', None)
    logger.info(f"Retrieved {products.count()} products for product_list")
    return render(request, 'product_list.html', {
        'products': products,
        'updated_product': updated_product,
        'deleted_product': deleted_product
    })

def update_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    session_key = f'product_{pk}'
    session_data = request.session.get(session_key, {})

    if request.method == 'POST':
        # Extract form data
        barcode = request.POST.get('barcode', '').strip()
        product_name = request.POST.get('product_name', '').strip()
        category_id = request.POST.get('category', '').strip()
        sale_price = request.POST.get('sale_price', '').strip()
        cost_price = request.POST.get('cost_price', '').strip()
        image = request.FILES.get('image')
        supplier_id = request.POST.get('supplier', '').strip()
        serial_number = request.POST.get('serial_number', '').strip()
        model = request.POST.get('model', '').strip()
        unit_id = request.POST.get('unit', '').strip()
        details = request.POST.get('details', '').strip()
        vat_percentage = request.POST.get('vat_percentage', '0.00').strip()

        # Initialize errors dictionary
        errors = {}

        # Validate required fields
        if not barcode:
            errors['barcode'] = "Barcode is required."
        if not product_name:
            errors['product_name'] = "Product name is required."
        if not category_id:
            errors['category'] = "Please select a category."
        if not sale_price:
            errors['sale_price'] = "Sale price is required."
        if not cost_price:
            errors['cost_price'] = "Cost price is required."
        if not supplier_id:
            errors['supplier'] = "Please select a supplier."
        if not unit_id:
            errors['unit'] = "Please select a unit."

        # Validate numeric fields
        try:
            sale_price = float(sale_price)
            cost_price = float(cost_price)
            vat_percentage = float(vat_percentage)
            if sale_price < 0:
                errors['sale_price'] = "Sale price cannot be negative."
            if cost_price < 0:
                errors['cost_price'] = "Cost price cannot be negative."
            if vat_percentage < 0:
                errors['vat_percentage'] = "VAT percentage cannot be negative."
        except (ValueError, TypeError):
            if 'sale_price' not in errors:
                errors['sale_price'] = "Sale price must be a valid number."
            if 'cost_price' not in errors:
                errors['cost_price'] = "Cost price must be a valid number."
            if 'vat_percentage' not in errors:
                errors['vat_percentage'] = "VAT percentage must be a valid number."

        # Validate barcode uniqueness (exclude current product)
        if barcode and not errors.get('barcode'):
            if Product.objects.filter(barcode=barcode).exclude(pk=product.pk).exists():
                errors['barcode'] = "A product with this barcode already exists."

        # Validate foreign keys
        category = None
        if category_id and not errors.get('category'):
            try:
                category = Category.objects.get(id=category_id, status='Active')
            except (Category.DoesNotExist, ValueError):
                errors['category'] = "Selected category is invalid or inactive."

        supplier = None
        if supplier_id and not errors.get('supplier'):
            try:
                supplier = Supplier.objects.get(id=supplier_id)
            except (Supplier.DoesNotExist, ValueError):
                errors['supplier'] = "Selected supplier is invalid."

        unit = None
        if unit_id and not errors.get('unit'):
            try:
                unit = Unit.objects.get(id=unit_id, status='Active')
            except (Unit.DoesNotExist, ValueError):
                errors['unit'] = "Selected unit is invalid or inactive."

        # Log form data for debugging
        logger.debug(f"Update form data: barcode={barcode}, category_id={category_id}, supplier_id={supplier_id}, unit_id={unit_id}")

        # If no errors, update the product and then update session
        if not errors:
            try:
                product.barcode = barcode
                product.name = product_name
                product.category = category
                product.sale_price = sale_price
                product.cost_price = cost_price
                if image:
                    product.image = image
                product.supplier = supplier
                product.serial_number = serial_number
                product.model = model
                product.unit = unit
                product.details = details
                product.vat_percentage = vat_percentage
                product.save()
                logger.info(f"Product '{product.name}' updated successfully with barcode '{barcode}'")
                # Update session with the saved product data
                request.session[session_key] = {
                    'barcode': product.barcode,
                    'product_name': product.name,
                    'category': str(product.category.id) if product.category else '',
                    'category_name': product.category.name if product.category else '',
                    'sale_price': str(product.sale_price),
                    'cost_price': str(product.cost_price),
                    'supplier': str(product.supplier.id) if product.supplier else '',
                    'supplier_name': product.supplier.supplier_name if product.supplier else '',
                    'serial_number': product.serial_number if product.serial_number else '',
                    'model': product.model if product.model else '',
                    'unit': str(product.unit.id) if product.unit else '',
                    'unit_name': product.unit.name if product.unit else '',
                    'details': product.details if product.details else '',
                    'vat_percentage': str(product.vat_percentage) if product.vat_percentage else '0.00',
                }
                request.session['updated_product'] = {
                    'id': product.id,
                    'name': product.name
                }
                messages.success(request, f"Product '{product.name}' updated successfully!")
                return redirect('product_list')
            except IntegrityError as e:
                logger.error(f"IntegrityError while updating product: {e}")
                errors['general'] = f"Failed to update product due to a database error: {str(e)}"
            except Exception as e:
                logger.error(f"Unexpected error while updating product: {e}")
                errors['general'] = "An unexpected error occurred. Please try again."

        # If errors exist, update session with submitted form data and re-render the form
        request.session[session_key] = {
            'barcode': barcode,
            'product_name': product_name,
            'category': category_id,
            'category_name': category.name if category else '',
            'sale_price': sale_price,
            'cost_price': cost_price,
            'supplier': supplier_id,
            'supplier_name': supplier.supplier_name if supplier else '',
            'serial_number': serial_number if serial_number else '',
            'model': model if model else '',
            'unit': unit_id,
            'unit_name': unit.name if unit else '',
            'details': details if details else '',
            'vat_percentage': vat_percentage if vat_percentage else '0.00',
        }
        form_data = {
            'barcode': barcode,
            'product_name': product_name,
            'category': category_id,
            'category_name': category.name if category else '',
            'sale_price': sale_price,
            'cost_price': cost_price,
            'supplier': supplier_id,
            'supplier_name': supplier.supplier_name if supplier else '',
            'serial_number': serial_number,
            'model': model,
            'unit': unit_id,
            'unit_name': unit.name if unit else '',
            'details': details,
            'vat_percentage': vat_percentage,
        }
        messages.error(request, "Please correct the errors below.")
        return render(request, 'add_product.html', {
            'product': product,
            'categories': Category.objects.filter(status='Active'),
            'suppliers': Supplier.objects.all(),
            'units': Unit.objects.filter(status='Active'),
            'errors': errors,
            'form_data': form_data,
        })

    # For GET request, pre-populate with product data, falling back to session data if available
    initial_data = {
        'barcode': session_data.get('barcode', product.barcode),
        'product_name': session_data.get('product_name', product.name),
        'category': session_data.get('category', str(product.category.id) if product.category else ''),
        'category_name': session_data.get('category_name', product.category.name if product.category else ''),
        'sale_price': session_data.get('sale_price', str(product.sale_price)),
        'cost_price': session_data.get('cost_price', str(product.cost_price)),
        'supplier': session_data.get('supplier', str(product.supplier.id) if product.supplier else ''),
        'supplier_name': session_data.get('supplier_name', product.supplier.supplier_name if product.supplier else ''),
        'serial_number': session_data.get('serial_number', product.serial_number if product.serial_number else ''),
        'model': session_data.get('model', product.model if product.model else ''),
        'unit': session_data.get('unit', str(product.unit.id) if product.unit else ''),
        'unit_name': session_data.get('unit_name', product.unit.name if product.unit else ''),
        'details': session_data.get('details', product.details if product.details else ''),
        'vat_percentage': session_data.get('vat_percentage', str(product.vat_percentage) if product.vat_percentage else '0.00'),
    }
    return render(request, 'add_product.html', {
        'product': product,
        'categories': Category.objects.filter(status='Active'),
        'suppliers': Supplier.objects.all(),
        'units': Unit.objects.filter(status='Active'),
        'form_data': initial_data,
    })

def delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        try:
            product_name = product.name
            product.delete()
            request.session.pop(f'product_{pk}', None)  # Clear session data for deleted product
            request.session['deleted_product'] = product_name
            messages.success(request, f"Product '{product_name}' deleted successfully!")
            return redirect('product_list')
        except Exception as e:
            logger.error(f"Error deleting product: {e}")
            messages.error(request, "Failed to delete product. It may be in use.")
    return redirect('product_list')

def add_product_csv(request):
    return render(request, 'add_product_csv.html')

def manage_product(request):
    return render(request, 'manage_product.html')