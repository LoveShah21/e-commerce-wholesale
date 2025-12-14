"""
Integration tests for Manufacturing/Inventory Management APIs

Tests the CRUD operations for raw materials, suppliers, and material-supplier associations.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal
import uuid

from apps.manufacturing.models import (
    RawMaterial, MaterialType, Supplier, MaterialSupplier
)
from apps.users.models import City, State, Country

User = get_user_model()


class InventoryManagementAPITest(TestCase):
    """Test inventory management APIs"""
    
    def setUp(self):
        """Set up test data"""
        # Create admin user
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            full_name='Admin User',
            user_type='admin'
        )
        
        # Create operator user
        self.operator_user = User.objects.create_user(
            username='operator',
            email='operator@example.com',
            password='operatorpass123',
            full_name='Operator User',
            user_type='operator'
        )
        
        # Create customer user
        self.customer_user = User.objects.create_user(
            username='customer',
            email='customer@example.com',
            password='customerpass123',
            full_name='Customer User',
            user_type='customer'
        )
        
        # Create material type
        self.material_type = MaterialType.objects.create(
            material_type_name='Fabric',
            unit_of_measurement='meters'
        )
        
        # Create API client
        self.client = APIClient()
    
    def test_raw_material_crud_as_admin(self):
        """Test raw material CRUD operations as admin"""
        self.client.force_authenticate(user=self.admin_user)
        
        # Create raw material
        data = {
            'material_name': 'Cotton Fabric',
            'material_type': self.material_type.id,
            'unit_price': '50.00',
            'current_quantity': '1000.00'
        }
        response = self.client.post('/api/manufacturing/materials/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        material_id = response.data['id']
        
        # List raw materials
        response = self.client.get('/api/manufacturing/materials/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check if paginated or not
        if isinstance(response.data, dict) and 'results' in response.data:
            self.assertGreaterEqual(len(response.data['results']), 1)
        else:
            self.assertGreaterEqual(len(response.data), 1)
        
        # Get raw material detail
        response = self.client.get(f'/api/manufacturing/materials/{material_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['material_name'], 'Cotton Fabric')
        
        # Update raw material
        data = {
            'material_name': 'Premium Cotton Fabric',
            'unit_price': '55.00',
            'current_quantity': '1000.00'
        }
        response = self.client.patch(f'/api/manufacturing/materials/{material_id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['material_name'], 'Premium Cotton Fabric')
        
        # Delete raw material
        response = self.client.delete(f'/api/manufacturing/materials/{material_id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
    
    def test_material_quantity_update(self):
        """Test material quantity update with timestamp"""
        self.client.force_authenticate(user=self.admin_user)
        
        # Create raw material
        material = RawMaterial.objects.create(
            material_name='Test Material',
            material_type=self.material_type,
            unit_price=Decimal('50.00'),
            current_quantity=Decimal('1000.00')
        )
        
        initial_timestamp = material.last_updated
        
        # Update quantity
        data = {'current_quantity': '800.00'}
        response = self.client.patch(
            f'/api/manufacturing/materials/{material.id}/quantity/',
            data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['current_quantity'], '800.00')
        
        # Verify timestamp was updated
        material.refresh_from_db()
        self.assertGreater(material.last_updated, initial_timestamp)
    
    def test_supplier_crud_as_admin(self):
        """Test supplier CRUD operations as admin"""
        self.client.force_authenticate(user=self.admin_user)
        
        # Create supplier
        data = {
            'supplier_name': 'ABC Textiles',
            'contact_person': 'John Doe',
            'email': 'john@abctextiles.com',
            'phone': '1234567890'
        }
        response = self.client.post('/api/manufacturing/suppliers/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        supplier_id = response.data['id']
        
        # List suppliers
        response = self.client.get('/api/manufacturing/suppliers/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check if paginated or not
        if isinstance(response.data, dict) and 'results' in response.data:
            self.assertGreaterEqual(len(response.data['results']), 1)
        else:
            self.assertGreaterEqual(len(response.data), 1)
        
        # Get supplier detail
        response = self.client.get(f'/api/manufacturing/suppliers/{supplier_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['supplier_name'], 'ABC Textiles')
        
        # Update supplier
        data = {'supplier_name': 'ABC Premium Textiles'}
        response = self.client.patch(f'/api/manufacturing/suppliers/{supplier_id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Delete supplier
        response = self.client.delete(f'/api/manufacturing/suppliers/{supplier_id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
    
    def test_material_supplier_association(self):
        """Test material-supplier association CRUD"""
        self.client.force_authenticate(user=self.admin_user)
        
        # Create material and supplier
        material = RawMaterial.objects.create(
            material_name='Test Material',
            material_type=self.material_type,
            unit_price=Decimal('50.00'),
            current_quantity=Decimal('1000.00')
        )
        
        supplier = Supplier.objects.create(
            supplier_name='Test Supplier',
            contact_person='Test Contact',
            email='test@supplier.com'
        )
        
        # Create association
        data = {
            'material': material.id,
            'supplier': supplier.id,
            'supplier_price': '45.00',
            'min_order_quantity': '100.00',
            'reorder_level': '200.00',
            'lead_time_days': 7,
            'is_preferred': True
        }
        response = self.client.post('/api/manufacturing/material-suppliers/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        association_id = response.data['id']
        
        # List associations
        response = self.client.get('/api/manufacturing/material-suppliers/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check if paginated or not
        if isinstance(response.data, dict) and 'results' in response.data:
            self.assertGreaterEqual(len(response.data['results']), 1)
        else:
            self.assertGreaterEqual(len(response.data), 1)
        
        # Get association detail
        response = self.client.get(f'/api/manufacturing/material-suppliers/{association_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['supplier_price'], '45.00')
    
    def test_inventory_view(self):
        """Test inventory view with reorder alerts"""
        self.client.force_authenticate(user=self.admin_user)
        
        # Create material with low quantity
        material = RawMaterial.objects.create(
            material_name='Low Stock Material',
            material_type=self.material_type,
            unit_price=Decimal('50.00'),
            current_quantity=Decimal('50.00')
        )
        
        supplier = Supplier.objects.create(
            supplier_name='Test Supplier',
            contact_person='Test Contact',
            email='test@supplier.com'
        )
        
        # Create association with reorder level
        MaterialSupplier.objects.create(
            material=material,
            supplier=supplier,
            supplier_price=Decimal('45.00'),
            reorder_level=Decimal('100.00'),
            is_preferred=True
        )
        
        # Get inventory view
        response = self.client.get('/api/manufacturing/inventory/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data['count'], 1)
        
        # Check that low stock material is flagged
        low_stock_items = [
            item for item in response.data['results']
            if item['material_id'] == material.id
        ]
        self.assertEqual(len(low_stock_items), 1)
        self.assertTrue(low_stock_items[0]['is_below_reorder'])
        
        # Get only alerts
        response = self.client.get('/api/manufacturing/inventory/?alerts_only=true')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data['count'], 1)
    
    def test_reorder_alerts(self):
        """Test reorder alerts endpoint"""
        self.client.force_authenticate(user=self.admin_user)
        
        # Create material with low quantity
        material = RawMaterial.objects.create(
            material_name='Low Stock Material',
            material_type=self.material_type,
            unit_price=Decimal('50.00'),
            current_quantity=Decimal('50.00')
        )
        
        supplier = Supplier.objects.create(
            supplier_name='Test Supplier',
            contact_person='Test Contact',
            email='test@supplier.com'
        )
        
        # Create association with reorder level
        MaterialSupplier.objects.create(
            material=material,
            supplier=supplier,
            supplier_price=Decimal('45.00'),
            reorder_level=Decimal('100.00'),
            is_preferred=True
        )
        
        # Get reorder alerts
        response = self.client.get('/api/manufacturing/inventory/alerts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data['count'], 1)
        
        # Verify alert contains correct information
        alerts = response.data['alerts']
        material_alert = next(
            (a for a in alerts if a['material_id'] == material.id),
            None
        )
        self.assertIsNotNone(material_alert)
        self.assertEqual(material_alert['current_quantity'], Decimal('50.00'))
        self.assertEqual(material_alert['reorder_level'], Decimal('100.00'))
        self.assertEqual(material_alert['shortage'], Decimal('50.00'))
    
    def test_operator_can_access_inventory(self):
        """Test that operator can access inventory APIs"""
        self.client.force_authenticate(user=self.operator_user)
        
        # Operator should be able to list materials
        response = self.client.get('/api/manufacturing/materials/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Operator should be able to view inventory
        response = self.client.get('/api/manufacturing/inventory/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_customer_cannot_access_inventory(self):
        """Test that customer cannot access inventory APIs"""
        self.client.force_authenticate(user=self.customer_user)
        
        # Customer should not be able to list materials
        response = self.client.get('/api/manufacturing/materials/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Customer should not be able to view inventory
        response = self.client.get('/api/manufacturing/inventory/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
