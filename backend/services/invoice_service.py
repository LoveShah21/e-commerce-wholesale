"""
Invoice Service

Handles invoice generation including PDF creation, invoice number generation,
tax calculation, and invoice storage.
"""

import logging
import os
from decimal import Decimal
from typing import Dict, Any, Optional
from datetime import datetime
from django.db import transaction
from django.core.exceptions import ValidationError
from django.conf import settings
from django.db.models import Q

from apps.finance.models import Invoice, TaxConfiguration
from apps.orders.models import Order
from services.base import BaseService
from services.utils import calculate_total_with_tax


logger = logging.getLogger(__name__)


class InvoiceService(BaseService):
    """
    Service class for managing invoice operations.
    
    Provides methods for:
    - Generating unique invoice numbers
    - Calculating invoice totals with tax
    - Generating PDF invoices using ReportLab
    - Storing and retrieving invoices
    """
    
    @classmethod
    def generate_invoice_number(cls) -> str:
        """
        Generate a unique invoice number.
        
        Format: INV-YYYYMMDD-NNNN
        Where NNNN is a sequential number for the day.
        
        Returns:
            A unique invoice number string
        """
        # Get current date
        today = datetime.now()
        date_str = today.strftime("%Y%m%d")
        
        # Get count of invoices created today
        today_start = today.replace(hour=0, minute=0, second=0, microsecond=0)
        today_count = Invoice.objects.filter(
            invoice_date__gte=today_start
        ).count()
        
        # Generate sequential number (padded to 4 digits)
        sequence = str(today_count + 1).zfill(4)
        
        invoice_number = f"INV-{date_str}-{sequence}"
        
        # Ensure uniqueness (in case of race condition)
        while Invoice.objects.filter(invoice_number=invoice_number).exists():
            today_count += 1
            sequence = str(today_count + 1).zfill(4)
            invoice_number = f"INV-{date_str}-{sequence}"
        
        cls.log_info(f"Generated invoice number: {invoice_number}")
        return invoice_number
    
    @classmethod
    def get_active_tax_config(cls, date=None) -> Optional[TaxConfiguration]:
        """
        Get the active tax configuration for a specific date.
        
        Args:
            date: The date to get tax configuration for (defaults to today)
            
        Returns:
            The active TaxConfiguration for the date, or None if not found
        """
        if date is None:
            date = datetime.now().date()
        
        # Find tax config where date is between effective_from and effective_to
        # or effective_to is null (ongoing)
        tax_config = TaxConfiguration.objects.filter(
            is_active=True,
            effective_from__lte=date
        ).filter(
            Q(effective_to__gte=date) | Q(effective_to__isnull=True)
        ).order_by('-effective_from').first()
        
        if tax_config:
            cls.log_info(f"Found active tax config: {tax_config.tax_name} ({tax_config.tax_percentage}%)")
        else:
            cls.log_warning(f"No active tax configuration found for date: {date}")
        
        return tax_config
    
    @classmethod
    def calculate_invoice_totals(cls, order_id: int) -> Dict[str, Decimal]:
        """
        Calculate invoice totals including subtotal, tax, and grand total.
        
        Args:
            order_id: The order ID to calculate totals for
            
        Returns:
            Dictionary with 'subtotal', 'tax_amount', 'tax_percentage', and 'total_amount'
            
        Raises:
            ValidationError: If order not found or no active tax configuration
        """
        try:
            order = Order.objects.prefetch_related('items__variant_size').get(id=order_id)
        except Order.DoesNotExist:
            raise ValidationError(f"Order with ID {order_id} not found")
        
        # Calculate subtotal from order items
        subtotal = Decimal('0.00')
        for item in order.items.all():
            item_total = item.snapshot_unit_price * item.quantity
            subtotal += item_total
        
        # Get active tax configuration
        tax_config = cls.get_active_tax_config()
        if not tax_config:
            raise ValidationError("No active tax configuration found")
        
        # Calculate tax and total
        tax_amount, total_amount = calculate_total_with_tax(subtotal, tax_config.tax_percentage)
        
        cls.log_info(
            f"Calculated invoice totals for order {order_id}: "
            f"subtotal={subtotal}, tax={tax_amount}, total={total_amount}"
        )
        
        return {
            'subtotal': subtotal,
            'tax_amount': tax_amount,
            'tax_percentage': tax_config.tax_percentage,
            'total_amount': total_amount
        }
    
    @classmethod
    @transaction.atomic
    def generate_invoice(cls, order_id: int) -> Invoice:
        """
        Generate an invoice for an order.
        
        Creates an invoice record with unique invoice number and calculated totals.
        
        Args:
            order_id: The order ID to generate invoice for
            
        Returns:
            The created Invoice object
            
        Raises:
            ValidationError: If order not found, invoice already exists, or calculation fails
        """
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            raise ValidationError(f"Order with ID {order_id} not found")
        
        # Check if invoice already exists
        if Invoice.objects.filter(order=order).exists():
            existing_invoice = Invoice.objects.get(order=order)
            cls.log_info(f"Invoice already exists for order {order_id}: {existing_invoice.invoice_number}")
            return existing_invoice
        
        # Calculate totals
        totals = cls.calculate_invoice_totals(order_id)
        
        # Generate unique invoice number
        invoice_number = cls.generate_invoice_number()
        
        # Create invoice record
        invoice = Invoice.objects.create(
            order=order,
            invoice_number=invoice_number,
            total_amount=totals['total_amount']
        )
        
        cls.log_info(f"Generated invoice {invoice_number} for order {order_id}")
        
        return invoice
    
    @classmethod
    def generate_invoice_pdf(cls, invoice_id: int) -> str:
        """
        Generate a PDF invoice using ReportLab.
        
        Args:
            invoice_id: The invoice ID to generate PDF for
            
        Returns:
            The file path to the generated PDF
            
        Raises:
            ValidationError: If invoice not found
        """
        try:
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.lib import colors
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.enums import TA_CENTER, TA_RIGHT
        except ImportError:
            raise ValidationError("ReportLab library not installed. Install with: pip install reportlab")
        
        try:
            invoice = Invoice.objects.select_related('order__user', 'order__delivery_address').get(id=invoice_id)
        except Invoice.DoesNotExist:
            raise ValidationError(f"Invoice with ID {invoice_id} not found")
        
        order = invoice.order
        
        # Create PDF file path
        invoice_dir = os.path.join(settings.MEDIA_ROOT, 'invoices')
        os.makedirs(invoice_dir, exist_ok=True)
        pdf_filename = f"{invoice.invoice_number}.pdf"
        pdf_path = os.path.join(invoice_dir, pdf_filename)
        
        # Create PDF document
        doc = SimpleDocTemplate(pdf_path, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        elements.append(Paragraph("INVOICE", title_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Invoice details
        invoice_info = [
            ['Invoice Number:', invoice.invoice_number],
            ['Invoice Date:', invoice.invoice_date.strftime('%Y-%m-%d %H:%M')],
            ['Order ID:', f"#{order.id}"],
            ['Order Date:', order.order_date.strftime('%Y-%m-%d')],
        ]
        
        invoice_table = Table(invoice_info, colWidths=[2*inch, 3*inch])
        invoice_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(invoice_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Customer details
        elements.append(Paragraph("<b>Bill To:</b>", styles['Heading3']))
        customer_info = f"""
        {order.user.full_name}<br/>
        {order.user.email}<br/>
        {order.delivery_address.address_line1}<br/>
        {order.delivery_address.address_line2 or ''}<br/>
        {order.delivery_address.city.city_name}, {order.delivery_address.state.state_name}<br/>
        {order.delivery_address.postal_code.postal_code}, {order.delivery_address.country.country_name}
        """
        elements.append(Paragraph(customer_info, styles['Normal']))
        elements.append(Spacer(1, 0.3*inch))
        
        # Order items table
        elements.append(Paragraph("<b>Order Items:</b>", styles['Heading3']))
        elements.append(Spacer(1, 0.1*inch))
        
        # Table header
        items_data = [['Item', 'Quantity', 'Unit Price', 'Total']]
        
        # Calculate totals
        totals = cls.calculate_invoice_totals(order.id)
        
        # Add order items
        for item in order.items.all():
            variant = item.variant_size.variant
            size = item.variant_size.size
            item_name = f"{variant.product.product_name} - {variant.fabric.fabric_name} {variant.color.color_name} ({size.size_code})"
            item_total = item.snapshot_unit_price * item.quantity
            
            items_data.append([
                item_name,
                str(item.quantity),
                f"₹{item.snapshot_unit_price}",
                f"₹{item_total}"
            ])
        
        # Add subtotal, tax, and total rows
        items_data.append(['', '', 'Subtotal:', f"₹{totals['subtotal']}"])
        items_data.append(['', '', f"Tax ({totals['tax_percentage']}%):", f"₹{totals['tax_amount']}"])
        items_data.append(['', '', 'Total Amount:', f"₹{totals['total_amount']}"])
        
        items_table = Table(items_data, colWidths=[3.5*inch, 1*inch, 1.5*inch, 1.5*inch])
        items_table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            
            # Data rows
            ('FONTNAME', (0, 1), (-1, -4), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -4), 10),
            ('BOTTOMPADDING', (0, 1), (-1, -4), 8),
            
            # Subtotal, tax, total rows
            ('FONTNAME', (0, -3), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -3), (-1, -1), 10),
            ('ALIGN', (2, -3), (-1, -1), 'RIGHT'),
            
            # Grid
            ('GRID', (0, 0), (-1, -4), 1, colors.black),
            ('LINEABOVE', (2, -3), (-1, -3), 1, colors.black),
            ('LINEABOVE', (2, -1), (-1, -1), 2, colors.black),
            
            # Alignment
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),
            ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
        ]))
        elements.append(items_table)
        elements.append(Spacer(1, 0.5*inch))
        
        # Payment information
        from apps.finance.models import Payment
        payments = Payment.objects.filter(order=order, payment_status='success').order_by('created_at')
        
        if payments.exists():
            elements.append(Paragraph("<b>Payment Information:</b>", styles['Heading3']))
            payment_data = [['Payment Type', 'Amount', 'Date', 'Status']]
            
            for payment in payments:
                payment_data.append([
                    payment.get_payment_type_display(),
                    f"₹{payment.amount}",
                    payment.paid_at.strftime('%Y-%m-%d') if payment.paid_at else 'N/A',
                    payment.get_payment_status_display()
                ])
            
            payment_table = Table(payment_data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1.5*inch])
            payment_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
            ]))
            elements.append(payment_table)
        
        # Build PDF
        doc.build(elements)
        
        # Update invoice with PDF URL
        invoice.invoice_url = f"/media/invoices/{pdf_filename}"
        invoice.save()
        
        cls.log_info(f"Generated PDF for invoice {invoice.invoice_number} at {pdf_path}")
        
        return pdf_path