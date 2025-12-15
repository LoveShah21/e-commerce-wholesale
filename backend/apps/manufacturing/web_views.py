from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from django.db.models import Q
from django.views.decorators.http import require_http_methods
import json
from apps.users.models import City
from apps.users.permissions import admin_or_operator_required
from .models import RawMaterial, MaterialType, Supplier, MaterialSupplier, ManufacturingSpecification
from .services import ManufacturingService
import logging

logger = logging.getLogger(__name__)


@login_required
@admin_or_operator_required
def inventory_overview(request):
    """
    Display inventory overview with stats and reorder alerts.
    Validates: Requirements 13.4, 13.5
    """
    # Get stats
    total_materials = RawMaterial.objects.count()
    total_suppliers = Supplier.objects.count()
    total_types = MaterialType.objects.count()
    
    # Get reorder alerts
    reorder_alerts = ManufacturingService.get_reorder_alerts()
    low_stock_count = len(reorder_alerts)
    
    # Get recent materials
    recent_materials_qs = RawMaterial.objects.select_related('material_type').order_by('-last_updated')[:10]
    
    # Fetch material data from API to get is_below_reorder status
    recent_materials = []
    for material in recent_materials_qs:
        material_data = {
            'id': material.id,
            'material_name': material.material_name,
            'material_type_name': material.material_type.material_type_name,
            'unit_of_measurement': material.material_type.unit_of_measurement,
            'unit_price': material.unit_price,
            'current_quantity': material.current_quantity,
            'last_updated': material.last_updated,
            'is_below_reorder': False
        }
        
        # Check if below reorder level
        material_suppliers = MaterialSupplier.objects.filter(
            material=material,
            reorder_level__isnull=False
        )
        for ms in material_suppliers:
            if material.current_quantity < ms.reorder_level:
                material_data['is_below_reorder'] = True
                break
        
        recent_materials.append(material_data)
    
    context = {
        'total_materials': total_materials,
        'total_suppliers': total_suppliers,
        'total_types': total_types,
        'low_stock_count': low_stock_count,
        'reorder_alerts': reorder_alerts,
        'recent_materials': recent_materials,
    }
    
    return render(request, 'inventory/inventory_view.html', context)


@login_required
@admin_or_operator_required
def material_list(request):
    """
    Display list of raw materials with search and filters.
    Validates: Requirements 13.1, 13.4, 13.5
    """
    # Get query parameters
    search_query = request.GET.get('search', '')
    material_type_id = request.GET.get('material_type', '')
    alerts_only = request.GET.get('alerts_only', '') == 'true'
    
    # Build query
    materials_qs = RawMaterial.objects.select_related('material_type').order_by('-last_updated')
    
    if search_query:
        materials_qs = materials_qs.filter(material_name__icontains=search_query)
    
    if material_type_id:
        materials_qs = materials_qs.filter(material_type_id=material_type_id)
    
    # Get materials with reorder info
    materials = []
    for material in materials_qs:
        material_data = {
            'id': material.id,
            'material_name': material.material_name,
            'material_type_name': material.material_type.material_type_name,
            'unit_of_measurement': material.material_type.unit_of_measurement,
            'unit_price': material.unit_price,
            'current_quantity': material.current_quantity,
            'last_updated': material.last_updated,
            'is_below_reorder': False,
            'reorder_info': None
        }
        
        # Check if below reorder level
        material_suppliers = MaterialSupplier.objects.filter(
            material=material,
            reorder_level__isnull=False
        ).select_related('supplier')
        
        for ms in material_suppliers:
            if material.current_quantity < ms.reorder_level:
                material_data['is_below_reorder'] = True
                
                # Get preferred supplier
                preferred = MaterialSupplier.objects.filter(
                    material=material,
                    is_preferred=True
                ).select_related('supplier').first()
                
                material_data['reorder_info'] = {
                    'reorder_level': ms.reorder_level,
                    'shortage': ms.reorder_level - material.current_quantity,
                    'preferred_supplier': {
                        'id': preferred.supplier.id,
                        'name': preferred.supplier.supplier_name,
                        'price': preferred.supplier_price,
                        'min_order_qty': preferred.min_order_quantity,
                        'lead_time_days': preferred.lead_time_days
                    } if preferred else None
                }
                break
        
        materials.append(material_data)
    
    # Filter for alerts only
    if alerts_only:
        materials = [m for m in materials if m['is_below_reorder']]
    
    # Get material types for filter
    material_types = MaterialType.objects.all().order_by('material_type_name')
    
    context = {
        'materials': materials,
        'material_types': material_types,
        'search_query': search_query,
        'selected_type': material_type_id,
        'alerts_only': alerts_only,
    }
    
    return render(request, 'inventory/material_list.html', context)


@login_required
@admin_or_operator_required
def material_create(request):
    """
    Create a new raw material.
    Validates: Requirements 13.1
    """
    if request.method == 'POST':
        try:
            material_name = request.POST.get('material_name')
            material_type_id = request.POST.get('material_type')
            unit_price = request.POST.get('unit_price')
            current_quantity = request.POST.get('current_quantity')
            
            # Validate required fields
            if not all([material_name, material_type_id, unit_price, current_quantity]):
                messages.error(request, 'All fields are required.')
                return render(request, 'inventory/material_form.html', {
                    'material_types': MaterialType.objects.all(),
                    'errors': {'form': 'All fields are required'}
                })
            
            # Create material
            with transaction.atomic():
                material = RawMaterial.objects.create(
                    material_name=material_name,
                    material_type_id=material_type_id,
                    unit_price=unit_price,
                    current_quantity=current_quantity
                )
            
            messages.success(request, f'Material "{material.material_name}" created successfully.')
            logger.info(f"Created material: {material.material_name} by user {request.user.id}")
            return redirect('material-list-web')
            
        except Exception as e:
            logger.error(f"Error creating material: {str(e)}")
            messages.error(request, f'Error creating material: {str(e)}')
            return render(request, 'inventory/material_form.html', {
                'material_types': MaterialType.objects.all(),
                'form_error': str(e)
            })
    
    # GET request
    material_types = MaterialType.objects.all().order_by('material_type_name')
    return render(request, 'inventory/material_form.html', {
        'material_types': material_types
    })


@login_required
@admin_or_operator_required
def material_edit(request, material_id):
    """
    Edit an existing raw material.
    Validates: Requirements 13.1, 13.3
    """
    material = get_object_or_404(RawMaterial, id=material_id)
    
    if request.method == 'POST':
        try:
            material.material_name = request.POST.get('material_name')
            material.material_type_id = request.POST.get('material_type')
            material.unit_price = request.POST.get('unit_price')
            material.current_quantity = request.POST.get('current_quantity')
            
            with transaction.atomic():
                material.save()
            
            messages.success(request, f'Material "{material.material_name}" updated successfully.')
            logger.info(f"Updated material: {material.material_name} by user {request.user.id}")
            return redirect('material-list-web')
            
        except Exception as e:
            logger.error(f"Error updating material: {str(e)}")
            messages.error(request, f'Error updating material: {str(e)}')
    
    material_types = MaterialType.objects.all().order_by('material_type_name')
    return render(request, 'inventory/material_form.html', {
        'material': material,
        'material_types': material_types
    })


@login_required
@admin_or_operator_required
@require_http_methods(["POST"])
def material_update_quantity(request, material_id):
    """
    Update material quantity via AJAX.
    Validates: Requirements 13.3, 13.4
    """
    try:
        material = get_object_or_404(RawMaterial, id=material_id)
        
        # Parse JSON body
        data = json.loads(request.body)
        current_quantity = data.get('current_quantity')
        
        if current_quantity is None:
            return JsonResponse({'error': 'current_quantity is required'}, status=400)
        
        with transaction.atomic():
            material.current_quantity = current_quantity
            material.save()
        
        logger.info(f"Updated material quantity for {material.material_name}: {current_quantity} by user {request.user.id}")
        
        return JsonResponse({
            'success': True,
            'message': 'Quantity updated successfully',
            'material_id': material.id,
            'current_quantity': float(material.current_quantity),
            'last_updated': material.last_updated.isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error updating material quantity: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@admin_or_operator_required
@require_http_methods(["POST"])
def material_delete(request, material_id):
    """
    Delete a raw material.
    """
    try:
        material = get_object_or_404(RawMaterial, id=material_id)
        material_name = material.material_name
        
        with transaction.atomic():
            material.delete()
        
        messages.success(request, f'Material "{material_name}" deleted successfully.')
        logger.info(f"Deleted material: {material_name} by user {request.user.id}")
        
    except Exception as e:
        logger.error(f"Error deleting material: {str(e)}")
        messages.error(request, f'Error deleting material: {str(e)}')
    
    return redirect('material-list-web')


@login_required
@admin_or_operator_required
def supplier_list(request):
    """
    Display list of suppliers with search.
    Validates: Requirements 13.2
    """
    search_query = request.GET.get('search', '')
    
    suppliers = Supplier.objects.select_related('city', 'city__state').order_by('supplier_name')
    
    if search_query:
        suppliers = suppliers.filter(
            supplier_name__icontains=search_query
        ) | suppliers.filter(
            contact_person__icontains=search_query
        ) | suppliers.filter(
            email__icontains=search_query
        )
    
    context = {
        'suppliers': suppliers,
        'search_query': search_query,
    }
    
    return render(request, 'inventory/supplier_list.html', context)


@login_required
@admin_or_operator_required
def supplier_create(request):
    """
    Create a new supplier.
    Validates: Requirements 13.2
    """
    if request.method == 'POST':
        try:
            supplier_name = request.POST.get('supplier_name')
            contact_person = request.POST.get('contact_person')
            email = request.POST.get('email')
            phone = request.POST.get('phone')
            city_id = request.POST.get('city')
            
            if not supplier_name:
                messages.error(request, 'Supplier name is required.')
                return render(request, 'inventory/supplier_form.html', {
                    'cities': City.objects.select_related('state').all(),
                    'errors': {'supplier_name': 'Supplier name is required'}
                })
            
            with transaction.atomic():
                supplier = Supplier.objects.create(
                    supplier_name=supplier_name,
                    contact_person=contact_person or None,
                    email=email or None,
                    phone=phone or None,
                    city_id=city_id if city_id else None
                )
            
            messages.success(request, f'Supplier "{supplier.supplier_name}" created successfully.')
            logger.info(f"Created supplier: {supplier.supplier_name} by user {request.user.id}")
            return redirect('supplier-list-web')
            
        except Exception as e:
            logger.error(f"Error creating supplier: {str(e)}")
            messages.error(request, f'Error creating supplier: {str(e)}')
            return render(request, 'inventory/supplier_form.html', {
                'cities': City.objects.select_related('state').all(),
                'form_error': str(e)
            })
    
    cities = City.objects.select_related('state').order_by('city_name')
    return render(request, 'inventory/supplier_form.html', {
        'cities': cities
    })


@login_required
@admin_or_operator_required
def supplier_edit(request, supplier_id):
    """
    Edit an existing supplier.
    Validates: Requirements 13.2
    """
    supplier = get_object_or_404(Supplier, id=supplier_id)
    
    if request.method == 'POST':
        try:
            supplier.supplier_name = request.POST.get('supplier_name')
            supplier.contact_person = request.POST.get('contact_person') or None
            supplier.email = request.POST.get('email') or None
            supplier.phone = request.POST.get('phone') or None
            city_id = request.POST.get('city')
            supplier.city_id = city_id if city_id else None
            
            with transaction.atomic():
                supplier.save()
            
            messages.success(request, f'Supplier "{supplier.supplier_name}" updated successfully.')
            logger.info(f"Updated supplier: {supplier.supplier_name} by user {request.user.id}")
            return redirect('supplier-list-web')
            
        except Exception as e:
            logger.error(f"Error updating supplier: {str(e)}")
            messages.error(request, f'Error updating supplier: {str(e)}')
    
    cities = City.objects.select_related('state').order_by('city_name')
    return render(request, 'inventory/supplier_form.html', {
        'supplier': supplier,
        'cities': cities
    })


@login_required
@admin_or_operator_required
@require_http_methods(["POST"])
def supplier_delete(request, supplier_id):
    """
    Delete a supplier.
    """
    try:
        supplier = get_object_or_404(Supplier, id=supplier_id)
        supplier_name = supplier.supplier_name
        
        with transaction.atomic():
            supplier.delete()
        
        messages.success(request, f'Supplier "{supplier_name}" deleted successfully.')
        logger.info(f"Deleted supplier: {supplier_name} by user {request.user.id}")
        
    except Exception as e:
        logger.error(f"Error deleting supplier: {str(e)}")
        messages.error(request, f'Error deleting supplier: {str(e)}')
    
    return redirect('supplier-list-web')


@login_required
@admin_or_operator_required
def material_supplier_list(request):
    """
    Display list of material-supplier associations with filters.
    Validates: Requirements 13.2
    """
    material_id = request.GET.get('material', '')
    supplier_id = request.GET.get('supplier', '')
    is_preferred = request.GET.get('is_preferred', '') == 'true'
    
    material_suppliers = MaterialSupplier.objects.select_related(
        'material', 'material__material_type', 'supplier'
    ).order_by('-created_at')
    
    if material_id:
        material_suppliers = material_suppliers.filter(material_id=material_id)
    
    if supplier_id:
        material_suppliers = material_suppliers.filter(supplier_id=supplier_id)
    
    if is_preferred:
        material_suppliers = material_suppliers.filter(is_preferred=True)
    
    # Get all materials and suppliers for filters
    materials = RawMaterial.objects.all().order_by('material_name')
    suppliers = Supplier.objects.all().order_by('supplier_name')
    
    context = {
        'material_suppliers': material_suppliers,
        'materials': materials,
        'suppliers': suppliers,
        'selected_material': material_id,
        'selected_supplier': supplier_id,
        'is_preferred': is_preferred,
    }
    
    return render(request, 'inventory/material_supplier_list.html', context)


@login_required
@admin_or_operator_required
def material_supplier_create(request):
    """
    Create a new material-supplier association.
    Validates: Requirements 13.2
    """
    if request.method == 'POST':
        try:
            material_id = request.POST.get('material')
            supplier_id = request.POST.get('supplier')
            supplier_price = request.POST.get('supplier_price')
            min_order_quantity = request.POST.get('min_order_quantity')
            reorder_level = request.POST.get('reorder_level')
            lead_time_days = request.POST.get('lead_time_days')
            is_preferred = request.POST.get('is_preferred') == 'on'
            
            if not all([material_id, supplier_id]):
                messages.error(request, 'Material and Supplier are required.')
                return render(request, 'inventory/material_supplier_form.html', {
                    'materials': RawMaterial.objects.all(),
                    'suppliers': Supplier.objects.all(),
                    'errors': {'form': 'Material and Supplier are required'}
                })
            
            with transaction.atomic():
                material_supplier = MaterialSupplier.objects.create(
                    material_id=material_id,
                    supplier_id=supplier_id,
                    supplier_price=supplier_price if supplier_price else None,
                    min_order_quantity=min_order_quantity if min_order_quantity else None,
                    reorder_level=reorder_level if reorder_level else None,
                    lead_time_days=lead_time_days if lead_time_days else None,
                    is_preferred=is_preferred
                )
            
            messages.success(request, 'Material-Supplier association created successfully.')
            logger.info(f"Created material-supplier association: {material_supplier} by user {request.user.id}")
            return redirect('material-supplier-list-web')
            
        except Exception as e:
            logger.error(f"Error creating material-supplier association: {str(e)}")
            messages.error(request, f'Error: {str(e)}')
            return render(request, 'inventory/material_supplier_form.html', {
                'materials': RawMaterial.objects.select_related('material_type').all(),
                'suppliers': Supplier.objects.all(),
                'form_error': str(e)
            })
    
    materials = RawMaterial.objects.select_related('material_type').order_by('material_name')
    suppliers = Supplier.objects.order_by('supplier_name')
    return render(request, 'inventory/material_supplier_form.html', {
        'materials': materials,
        'suppliers': suppliers
    })


@login_required
@admin_or_operator_required
def material_supplier_edit(request, ms_id):
    """
    Edit an existing material-supplier association.
    Validates: Requirements 13.2
    """
    material_supplier = get_object_or_404(
        MaterialSupplier.objects.select_related('material', 'supplier'),
        id=ms_id
    )
    
    if request.method == 'POST':
        try:
            material_supplier.supplier_price = request.POST.get('supplier_price') or None
            material_supplier.min_order_quantity = request.POST.get('min_order_quantity') or None
            material_supplier.reorder_level = request.POST.get('reorder_level') or None
            material_supplier.lead_time_days = request.POST.get('lead_time_days') or None
            material_supplier.is_preferred = request.POST.get('is_preferred') == 'on'
            
            with transaction.atomic():
                material_supplier.save()
            
            messages.success(request, 'Material-Supplier association updated successfully.')
            logger.info(f"Updated material-supplier association: {material_supplier} by user {request.user.id}")
            return redirect('material-supplier-list-web')
            
        except Exception as e:
            logger.error(f"Error updating material-supplier association: {str(e)}")
            messages.error(request, f'Error: {str(e)}')
    
    materials = RawMaterial.objects.select_related('material_type').order_by('material_name')
    suppliers = Supplier.objects.order_by('supplier_name')
    return render(request, 'inventory/material_supplier_form.html', {
        'material_supplier': material_supplier,
        'materials': materials,
        'suppliers': suppliers
    })


@login_required
@admin_or_operator_required
@require_http_methods(["POST"])
def material_supplier_delete(request, ms_id):
    """
    Delete a material-supplier association.
    """
    try:
        material_supplier = get_object_or_404(MaterialSupplier, id=ms_id)
        
        with transaction.atomic():
            material_supplier.delete()
        
        messages.success(request, 'Material-Supplier association deleted successfully.')
        logger.info(f"Deleted material-supplier association by user {request.user.id}")
        
    except Exception as e:
        logger.error(f"Error deleting material-supplier association: {str(e)}")
        messages.error(request, f'Error: {str(e)}')
    
    return redirect('material-supplier-list-web')


@login_required
@admin_or_operator_required
def material_type_create(request):
    """
    Create a new material type.
    """
    if request.method == 'POST':
        try:
            material_type_name = request.POST.get('material_type_name')
            unit_of_measurement = request.POST.get('unit_of_measurement')
            description = request.POST.get('description')
            
            if not all([material_type_name, unit_of_measurement]):
                messages.error(request, 'Material type name and unit of measurement are required.')
                return render(request, 'inventory/material_type_form.html', {
                    'errors': {'form': 'All required fields must be filled'}
                })
            
            with transaction.atomic():
                material_type = MaterialType.objects.create(
                    material_type_name=material_type_name,
                    unit_of_measurement=unit_of_measurement,
                    description=description or None
                )
            
            messages.success(request, f'Material type "{material_type.material_type_name}" created successfully.')
            logger.info(f"Created material type: {material_type.material_type_name} by user {request.user.id}")
            
            # Close window with JavaScript
            return render(request, 'inventory/material_type_form.html', {
                'success': True,
                'message': 'Material type created successfully. You can close this window.'
            })
            
        except Exception as e:
            logger.error(f"Error creating material type: {str(e)}")
            messages.error(request, f'Error: {str(e)}')
            return render(request, 'inventory/material_type_form.html', {
                'form_error': str(e)
            })
    
    return render(request, 'inventory/material_type_form.html')


# Manufacturing Specification Views

@login_required
@admin_or_operator_required
def manufacturing_spec_list(request):
    """
    Display list of manufacturing specifications with filters.
    Validates: Requirements 10.1
    """
    from apps.products.models import Product, ProductVariant
    from .models import ManufacturingSpecification
    
    search_query = request.GET.get('search', '')
    material_id = request.GET.get('material', '')
    product_id = request.GET.get('product', '')
    
    specifications = ManufacturingSpecification.objects.select_related(
        'variant_size__variant__product',
        'variant_size__variant__fabric',
        'variant_size__variant__color',
        'variant_size__variant__pattern',
        'variant_size__size',
        'material__material_type'
    ).order_by('-created_at')
    
    if search_query:
        specifications = specifications.filter(
            variant_size__variant__product__product_name__icontains=search_query
        )
    
    if material_id:
        specifications = specifications.filter(material_id=material_id)
    
    if product_id:
        specifications = specifications.filter(variant_size__variant__product_id=product_id)
    
    # Add unit cost calculation
    specs_with_cost = []
    for spec in specifications:
        spec.unit_cost = spec.material.unit_price * spec.quantity_required
        specs_with_cost.append(spec)
    
    materials = RawMaterial.objects.all().order_by('material_name')
    products = Product.objects.all().order_by('product_name')
    
    context = {
        'specifications': specs_with_cost,
        'materials': materials,
        'products': products,
        'search_query': search_query,
        'selected_material': material_id,
        'selected_product': product_id,
    }
    
    return render(request, 'manufacturing/specification_list.html', context)


@login_required
@admin_or_operator_required
def manufacturing_spec_create(request):
    """
    Create a new manufacturing specification.
    Validates: Requirements 10.1
    """
    from apps.products.models import Product, VariantSize
    
    if request.method == 'POST':
        try:
            variant_size_id = request.POST.get('variant_size')
            material_id = request.POST.get('material')
            quantity_required = request.POST.get('quantity_required')
            
            if not all([variant_size_id, material_id, quantity_required]):
                messages.error(request, 'All fields are required.')
                return render(request, 'manufacturing/specification_form.html', {
                    'products': Product.objects.all(),
                    'materials': RawMaterial.objects.select_related('material_type').all(),
                    'form_error': 'All fields are required'
                })
            
            # Check if specification already exists
            existing = ManufacturingSpecification.objects.filter(
                variant_size_id=variant_size_id,
                material_id=material_id
            ).first()
            
            if existing:
                messages.error(request, 'A specification for this variant size and material already exists.')
                return render(request, 'manufacturing/specification_form.html', {
                    'products': Product.objects.all(),
                    'materials': RawMaterial.objects.select_related('material_type').all(),
                    'form_error': 'Specification already exists'
                })
            
            with transaction.atomic():
                spec = ManufacturingSpecification.objects.create(
                    variant_size_id=variant_size_id,
                    material_id=material_id,
                    quantity_required=quantity_required
                )
            
            messages.success(request, 'Manufacturing specification created successfully.')
            logger.info(f"Created manufacturing specification: {spec} by user {request.user.id}")
            return redirect('manufacturing-spec-list-web')
            
        except Exception as e:
            logger.error(f"Error creating manufacturing specification: {str(e)}")
            messages.error(request, f'Error: {str(e)}')
            return render(request, 'manufacturing/specification_form.html', {
                'products': Product.objects.all(),
                'materials': RawMaterial.objects.select_related('material_type').all(),
                'form_error': str(e)
            })
    
    products = Product.objects.all().order_by('product_name')
    materials = RawMaterial.objects.select_related('material_type').order_by('material_name')
    
    return render(request, 'manufacturing/specification_form.html', {
        'products': products,
        'materials': materials
    })


@login_required
@admin_or_operator_required
def manufacturing_spec_edit(request, spec_id):
    """
    Edit an existing manufacturing specification.
    Validates: Requirements 10.1
    """
    from apps.products.models import Product
    
    spec = get_object_or_404(
        ManufacturingSpecification.objects.select_related(
            'variant_size__variant__product',
            'variant_size__variant__fabric',
            'variant_size__variant__color',
            'variant_size__variant__pattern',
            'variant_size__size',
            'material__material_type'
        ),
        id=spec_id
    )
    
    if request.method == 'POST':
        try:
            quantity_required = request.POST.get('quantity_required')
            
            if not quantity_required:
                messages.error(request, 'Quantity required is mandatory.')
                return render(request, 'manufacturing/specification_form.html', {
                    'specification': spec,
                    'products': Product.objects.all(),
                    'materials': RawMaterial.objects.select_related('material_type').all(),
                    'form_error': 'Quantity required is mandatory'
                })
            
            with transaction.atomic():
                spec.quantity_required = quantity_required
                spec.save()
            
            messages.success(request, 'Manufacturing specification updated successfully.')
            logger.info(f"Updated manufacturing specification: {spec} by user {request.user.id}")
            return redirect('manufacturing-spec-list-web')
            
        except Exception as e:
            logger.error(f"Error updating manufacturing specification: {str(e)}")
            messages.error(request, f'Error: {str(e)}')
    
    products = Product.objects.all().order_by('product_name')
    materials = RawMaterial.objects.select_related('material_type').order_by('material_name')
    
    return render(request, 'manufacturing/specification_form.html', {
        'specification': spec,
        'products': products,
        'materials': materials
    })


@login_required
@admin_or_operator_required
@require_http_methods(["POST"])
def manufacturing_spec_delete(request, spec_id):
    """
    Delete a manufacturing specification.
    """
    try:
        spec = get_object_or_404(ManufacturingSpecification, id=spec_id)
        
        with transaction.atomic():
            spec.delete()
        
        messages.success(request, 'Manufacturing specification deleted successfully.')
        logger.info(f"Deleted manufacturing specification by user {request.user.id}")
        
    except Exception as e:
        logger.error(f"Error deleting manufacturing specification: {str(e)}")
        messages.error(request, f'Error: {str(e)}')
    
    return redirect('manufacturing-spec-list-web')


# Manufacturing Orders Views

@login_required
@admin_or_operator_required
def manufacturing_orders_list(request):
    """
    Display list of orders for manufacturing with production feasibility.
    Validates: Requirements 10.2, 10.5
    """
    from apps.orders.models import Order
    from django.db.models import Count, Sum
    
    status_filter = request.GET.get('status', '')
    feasibility_filter = request.GET.get('feasibility', '')
    search_query = request.GET.get('search', '')
    
    # Get orders that are confirmed or in production
    orders = Order.objects.select_related('user').prefetch_related(
        'items__variant_size__variant__product',
        'items__variant_size__size'
    ).filter(
        status__in=['confirmed', 'processing', 'dispatched']
    ).order_by('-order_date')
    
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    if search_query:
        orders = orders.filter(
            Q(id__icontains=search_query) |
            Q(user__full_name__icontains=search_query)
        )
    
    # Add production feasibility and item counts
    orders_with_data = []
    for order in orders:
        is_feasible, missing = ManufacturingService.check_production_feasibility(order)
        
        # Check if materials already consumed (order is processing or later)
        materials_consumed = order.status in ['processing', 'dispatched', 'delivered']
        
        order.is_feasible = is_feasible
        order.materials_consumed = materials_consumed
        order.total_items = order.items.count()
        order.total_quantity = order.items.aggregate(Sum('quantity'))['quantity__sum'] or 0
        
        # Apply feasibility filter
        if feasibility_filter == 'feasible' and not is_feasible:
            continue
        if feasibility_filter == 'not_feasible' and is_feasible:
            continue
        
        orders_with_data.append(order)
    
    context = {
        'orders': orders_with_data,
        'status_filter': status_filter,
        'feasibility_filter': feasibility_filter,
        'search_query': search_query,
    }
    
    return render(request, 'manufacturing/orders_list.html', context)


@login_required
@admin_or_operator_required
def manufacturing_order_materials(request, order_id):
    """
    Display material requirements for a specific order with consumption interface.
    Validates: Requirements 10.2, 10.3, 10.5
    """
    from apps.orders.models import Order
    from decimal import Decimal
    
    order = get_object_or_404(
        Order.objects.select_related('user').prefetch_related(
            'items__variant_size__variant__product',
            'items__variant_size__variant__fabric',
            'items__variant_size__variant__color',
            'items__variant_size__variant__pattern',
            'items__variant_size__size'
        ),
        id=order_id
    )
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'consume_materials':
            try:
                with transaction.atomic():
                    consumed = ManufacturingService.consume_materials_for_order(order)
                    
                    # Update order status to processing if it's confirmed
                    if order.status == 'confirmed':
                        order.status = 'processing'
                        order.save()
                
                messages.success(request, f'Materials consumed successfully for Order #{order.id}. Order status updated to Processing.')
                logger.info(f"Consumed materials for order {order.id} by user {request.user.id}")
                return redirect('manufacturing-orders-web')
                
            except Exception as e:
                logger.error(f"Error consuming materials for order {order.id}: {str(e)}")
                messages.error(request, f'Error consuming materials: {str(e)}')
    
    # Get material requirements
    try:
        material_data = ManufacturingService.get_order_material_requirements(order_id)
        requirements = material_data['requirements']
        is_feasible = material_data['is_feasible']
        missing_materials = material_data['missing_materials']
        total_materials_count = material_data['total_materials_count']
        
        # Add unit cost and total cost to requirements
        total_material_cost = Decimal('0.00')
        for req in requirements:
            material = RawMaterial.objects.get(id=req['material_id'])
            req['unit_cost'] = material.unit_price
            req['total_cost'] = material.unit_price * req['required_quantity']
            total_material_cost += req['total_cost']
        
    except Exception as e:
        logger.error(f"Error loading material requirements for order {order_id}: {str(e)}")
        messages.error(request, f'Error loading material requirements: {str(e)}')
        requirements = []
        is_feasible = False
        missing_materials = []
        total_materials_count = 0
        total_material_cost = Decimal('0.00')
    
    # Calculate total quantity
    total_quantity = sum(item.quantity for item in order.items.all())
    
    context = {
        'order': order,
        'requirements': requirements,
        'is_feasible': is_feasible,
        'missing_materials': missing_materials,
        'total_materials_count': total_materials_count,
        'total_quantity': total_quantity,
        'total_material_cost': total_material_cost,
    }
    
    return render(request, 'manufacturing/order_material_requirements.html', context)
