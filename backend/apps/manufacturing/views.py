from rest_framework import generics, permissions, filters, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction
from django.utils import timezone
from apps.users.permissions import IsAdminOrOperator, IsAdmin
from .models import RawMaterial, MaterialType, Supplier, MaterialSupplier, ManufacturingSpecification
from .serializers import (
    RawMaterialSerializer, RawMaterialCreateSerializer, RawMaterialUpdateSerializer,
    MaterialQuantityUpdateSerializer, MaterialTypeSerializer, SupplierSerializer,
    SupplierCreateSerializer, MaterialSupplierSerializer, MaterialSupplierCreateSerializer,
    ManufacturingSpecificationSerializer, ManufacturingSpecificationCreateSerializer,
    InventoryViewSerializer
)
from .services import ManufacturingService
import logging

logger = logging.getLogger(__name__)


class RawMaterialListCreateView(generics.ListCreateAPIView):
    """
    List all raw materials or create a new raw material.
    GET: Admin/Operator access
    POST: Admin only
    
    Validates: Requirements 13.1
    """
    queryset = RawMaterial.objects.all().select_related('material_type').order_by('-created_at')
    permission_classes = (IsAdminOrOperator,)
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    filterset_fields = ('material_type',)
    search_fields = ('material_name',)
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return RawMaterialCreateSerializer
        return RawMaterialSerializer
    
    def perform_create(self, serializer):
        material = serializer.save()
        logger.info(f"Created raw material: {material.material_name} by user {self.request.user.id}")


class RawMaterialDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a raw material.
    GET: Admin/Operator access
    PUT/PATCH/DELETE: Admin only
    
    Validates: Requirements 13.1
    """
    queryset = RawMaterial.objects.all().select_related('material_type')
    permission_classes = (IsAdminOrOperator,)
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return RawMaterialUpdateSerializer
        return RawMaterialSerializer
    
    def perform_update(self, serializer):
        material = serializer.save()
        logger.info(f"Updated raw material: {material.material_name} by user {self.request.user.id}")
    
    def perform_destroy(self, instance):
        logger.info(f"Deleted raw material: {instance.material_name} by user {self.request.user.id}")
        instance.delete()


class MaterialQuantityUpdateView(APIView):
    """
    Update material quantity with timestamp.
    PATCH: Admin/Operator access
    
    Validates: Requirements 13.3, 13.4
    """
    permission_classes = (IsAdminOrOperator,)
    
    def patch(self, request, material_id):
        try:
            material = RawMaterial.objects.get(id=material_id)
        except RawMaterial.DoesNotExist:
            return Response(
                {'error': 'Raw material not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = MaterialQuantityUpdateSerializer(data=request.data)
        if serializer.is_valid():
            with transaction.atomic():
                # Update quantity - last_updated is auto-updated by model
                material.current_quantity = serializer.validated_data['current_quantity']
                material.save()
                
                logger.info(
                    f"Updated material quantity for {material.material_name}: "
                    f"{serializer.validated_data['current_quantity']} by user {request.user.id}"
                )
            
            # Return updated material data
            response_serializer = RawMaterialSerializer(material)
            return Response(response_serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MaterialTypeListCreateView(generics.ListCreateAPIView):
    """
    List all material types or create a new material type.
    GET: Admin/Operator access
    POST: Admin only
    """
    queryset = MaterialType.objects.all().order_by('material_type_name')
    serializer_class = MaterialTypeSerializer
    permission_classes = (IsAdminOrOperator,)
    
    def perform_create(self, serializer):
        material_type = serializer.save()
        logger.info(f"Created material type: {material_type.material_type_name} by user {self.request.user.id}")


class MaterialTypeDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a material type.
    GET: Admin/Operator access
    PUT/PATCH/DELETE: Admin only
    """
    queryset = MaterialType.objects.all()
    serializer_class = MaterialTypeSerializer
    permission_classes = (IsAdminOrOperator,)


class SupplierListCreateView(generics.ListCreateAPIView):
    """
    List all suppliers or create a new supplier.
    GET: Admin/Operator access
    POST: Admin only
    
    Validates: Requirements 13.2
    """
    queryset = Supplier.objects.all().select_related('city').order_by('supplier_name')
    permission_classes = (IsAdminOrOperator,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ('supplier_name', 'contact_person', 'email')
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return SupplierCreateSerializer
        return SupplierSerializer
    
    def perform_create(self, serializer):
        supplier = serializer.save()
        logger.info(f"Created supplier: {supplier.supplier_name} by user {self.request.user.id}")


class SupplierDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a supplier.
    GET: Admin/Operator access
    PUT/PATCH/DELETE: Admin only
    
    Validates: Requirements 13.2
    """
    queryset = Supplier.objects.all().select_related('city')
    permission_classes = (IsAdminOrOperator,)
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return SupplierCreateSerializer
        return SupplierSerializer


class MaterialSupplierListCreateView(generics.ListCreateAPIView):
    """
    List all material-supplier associations or create a new association.
    GET: Admin/Operator access
    POST: Admin only
    
    Validates: Requirements 13.2
    """
    queryset = MaterialSupplier.objects.all().select_related(
        'material', 'material__material_type', 'supplier'
    ).order_by('-created_at')
    serializer_class = MaterialSupplierSerializer
    permission_classes = (IsAdminOrOperator,)
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('material', 'supplier', 'is_preferred')
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return MaterialSupplierCreateSerializer
        return MaterialSupplierSerializer
    
    def perform_create(self, serializer):
        material_supplier = serializer.save()
        logger.info(
            f"Created material-supplier association: {material_supplier.material.material_name} - "
            f"{material_supplier.supplier.supplier_name} by user {self.request.user.id}"
        )


class MaterialSupplierDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a material-supplier association.
    GET: Admin/Operator access
    PUT/PATCH/DELETE: Admin only
    
    Validates: Requirements 13.2
    """
    queryset = MaterialSupplier.objects.all().select_related(
        'material', 'material__material_type', 'supplier'
    )
    permission_classes = (IsAdminOrOperator,)
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return MaterialSupplierCreateSerializer
        return MaterialSupplierSerializer


class InventoryViewAPIView(APIView):
    """
    Get inventory view with reorder alerts.
    GET: Admin/Operator access
    
    Validates: Requirements 13.4, 13.5
    """
    permission_classes = (IsAdminOrOperator,)
    
    def get(self, request):
        # Get all materials with their type information
        materials = RawMaterial.objects.all().select_related('material_type')
        
        inventory_data = []
        
        for material in materials:
            # Check if below reorder level
            material_suppliers = MaterialSupplier.objects.filter(
                material=material,
                reorder_level__isnull=False
            ).select_related('supplier')
            
            is_below_reorder = False
            reorder_level = None
            shortage = None
            preferred_supplier_info = None
            
            for ms in material_suppliers:
                if material.current_quantity < ms.reorder_level:
                    is_below_reorder = True
                    reorder_level = ms.reorder_level
                    shortage = ms.reorder_level - material.current_quantity
                    
                    # Get preferred supplier
                    preferred = MaterialSupplier.objects.filter(
                        material=material,
                        is_preferred=True
                    ).select_related('supplier').first()
                    
                    if preferred:
                        preferred_supplier_info = {
                            'supplier_id': preferred.supplier.id,
                            'supplier_name': preferred.supplier.supplier_name,
                            'supplier_price': float(preferred.supplier_price) if preferred.supplier_price else None,
                            'min_order_quantity': float(preferred.min_order_quantity) if preferred.min_order_quantity else None,
                            'lead_time_days': preferred.lead_time_days
                        }
                    break
            
            inventory_item = {
                'material_id': material.id,
                'material_name': material.material_name,
                'material_type': material.material_type.material_type_name,
                'unit_of_measurement': material.material_type.unit_of_measurement,
                'unit_price': material.unit_price,
                'current_quantity': material.current_quantity,
                'is_below_reorder': is_below_reorder,
                'reorder_level': reorder_level,
                'shortage': shortage,
                'preferred_supplier': preferred_supplier_info,
                'last_updated': material.last_updated
            }
            
            inventory_data.append(inventory_item)
        
        # Filter by reorder alerts if requested
        show_alerts_only = request.query_params.get('alerts_only', 'false').lower() == 'true'
        if show_alerts_only:
            inventory_data = [item for item in inventory_data if item['is_below_reorder']]
        
        serializer = InventoryViewSerializer(inventory_data, many=True)
        
        return Response({
            'count': len(inventory_data),
            'results': serializer.data
        })


class ManufacturingSpecificationListCreateView(generics.ListCreateAPIView):
    """
    List all manufacturing specifications or create a new specification.
    GET: Admin/Operator access
    POST: Admin only
    
    Validates: Requirements 10.1
    """
    queryset = ManufacturingSpecification.objects.all().select_related(
        'variant_size', 'variant_size__variant', 'variant_size__variant__product',
        'variant_size__size', 'material', 'material__material_type'
    ).order_by('-created_at')
    permission_classes = (IsAdminOrOperator,)
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('variant_size', 'material')
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ManufacturingSpecificationCreateSerializer
        return ManufacturingSpecificationSerializer
    
    def perform_create(self, serializer):
        spec = serializer.save()
        logger.info(
            f"Created manufacturing specification: {spec.variant_size} requires "
            f"{spec.quantity_required} of {spec.material.material_name} by user {self.request.user.id}"
        )


class ManufacturingSpecificationDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a manufacturing specification.
    GET: Admin/Operator access
    PUT/PATCH/DELETE: Admin only
    
    Validates: Requirements 10.1
    """
    queryset = ManufacturingSpecification.objects.all().select_related(
        'variant_size', 'variant_size__variant', 'variant_size__variant__product',
        'variant_size__size', 'material', 'material__material_type'
    )
    permission_classes = (IsAdminOrOperator,)
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return ManufacturingSpecificationCreateSerializer
        return ManufacturingSpecificationSerializer


class ReorderAlertsView(APIView):
    """
    Get materials below reorder level.
    GET: Admin/Operator access
    
    Validates: Requirements 10.4, 13.5
    """
    permission_classes = (IsAdminOrOperator,)
    
    def get(self, request):
        alerts = ManufacturingService.get_reorder_alerts()
        
        # Convert Decimal values to float for JSON serialization
        serializable_alerts = []
        for alert in alerts:
            serializable_alert = {
                'material_id': alert['material_id'],
                'material_name': alert['material_name'],
                'current_quantity': float(alert['current_quantity']),
                'reorder_level': float(alert['reorder_level']),
                'shortage': float(alert['shortage']),
                'unit_price': float(alert['unit_price']),
            }
            
            if alert.get('preferred_supplier'):
                ps = alert['preferred_supplier']
                serializable_alert['preferred_supplier'] = {
                    'supplier_id': ps['supplier_id'],
                    'supplier_name': ps['supplier_name'],
                    'supplier_price': float(ps['supplier_price']) if ps['supplier_price'] else None,
                    'min_order_quantity': float(ps['min_order_quantity']) if ps['min_order_quantity'] else None,
                    'lead_time_days': ps['lead_time_days']
                }
            else:
                serializable_alert['preferred_supplier'] = None
            
            serializable_alerts.append(serializable_alert)
        
        return Response({
            'count': len(serializable_alerts),
            'alerts': serializable_alerts
        })
