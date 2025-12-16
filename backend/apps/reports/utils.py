from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Count
from apps.orders.models import Order, OrderItem
from apps.finance.models import Payment
from io import BytesIO
from datetime import datetime, date
from decimal import Decimal

def generate_invoice_pdf(order_id):
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return None

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Header
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, height - 50, "Vaitikan City")
    p.setFont("Helvetica", 12)
    p.drawString(50, height - 70, "Invoice")

    # Order Details
    p.drawString(50, height - 100, f"Order ID: {order.id}")
    p.drawString(50, height - 120, f"Date: {order.order_date.strftime('%Y-%m-%d')}")
    p.drawString(50, height - 140, f"Customer: {order.user.full_name}")

    # Items
    y = height - 180
    p.drawString(50, y, "Item")
    p.drawString(300, y, "Qty")
    p.drawString(400, y, "Price")
    p.drawString(500, y, "Total")
    
    y -= 20
    total = 0
    for item in order.items.all():
        variant_name = str(item.variant_size.variant)
        item_total = item.quantity * item.snapshot_unit_price
        total += item_total
        
        p.drawString(50, y, variant_name[:40]) # Truncate for simple layout
        p.drawString(300, y, str(item.quantity))
        p.drawString(400, y, f"{item.snapshot_unit_price}")
        p.drawString(500, y, f"{item_total}")
        y -= 20

    # Total
    p.line(50, y, 550, y)
    y -= 20
    p.setFont("Helvetica-Bold", 12)
    p.drawString(400, y, "Grand Total:")
    p.drawString(500, y, f"{total}")

    p.showPage()
    p.save()

    buffer.seek(0)
    return buffer

def get_date_range_filter(start_date, end_date, field_name):
    """Helper function to create proper datetime range filters that handle timezones correctly."""
    start_datetime = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
    end_datetime = timezone.make_aware(datetime.combine(end_date, datetime.max.time()))
    
    return {
        f'{field_name}__gte': start_datetime,
        f'{field_name}__lte': end_datetime
    }


def generate_sales_report_pdf(start_date, end_date, status_filter=None):
    """Generate a comprehensive sales report PDF."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    # Container for the 'Flowable' objects
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=1  # Center alignment
    )
    
    title = Paragraph(f"Sales Report<br/>{start_date.strftime('%B %d, %Y')} - {end_date.strftime('%B %d, %Y')}", title_style)
    elements.append(title)
    elements.append(Spacer(1, 12))
    
    # Get data using the same logic as the view
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # Get orders
    date_filter = get_date_range_filter(start_date, end_date, 'order_date')
    orders = Order.objects.filter(**date_filter).select_related('user').prefetch_related('items')
    
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    # Calculate statistics
    total_orders = orders.count()
    total_revenue = sum(order.total_amount for order in orders)
    avg_order_value = total_revenue / total_orders if total_orders > 0 else Decimal('0.00')
    
    # Summary section
    summary_data = [
        ['Metric', 'Value'],
        ['Total Orders', str(total_orders)],
        ['Total Revenue', f'₹{total_revenue:,.2f}'],
        ['Average Order Value', f'₹{avg_order_value:,.2f}'],
        ['Date Range', f'{start_date} to {end_date}'],
    ]
    
    if status_filter:
        summary_data.append(['Status Filter', status_filter.title()])
    
    summary_table = Table(summary_data, colWidths=[2*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(Paragraph("Summary", styles['Heading2']))
    elements.append(summary_table)
    elements.append(Spacer(1, 20))
    
    # Orders details
    if orders.exists():
        elements.append(Paragraph("Order Details", styles['Heading2']))
        
        order_data = [['Order ID', 'Date', 'Customer', 'Status', 'Total']]
        
        for order in orders[:50]:  # Limit to first 50 orders for PDF
            order_data.append([
                f'#{order.id}',
                order.order_date.strftime('%Y-%m-%d'),
                order.user.full_name[:25],  # Truncate long names
                order.status.title(),
                f'₹{order.total_amount:,.2f}'
            ])
        
        if orders.count() > 50:
            order_data.append(['...', '...', f'({orders.count() - 50} more orders)', '...', '...'])
        
        order_table = Table(order_data, colWidths=[1*inch, 1.2*inch, 2*inch, 1*inch, 1.2*inch])
        order_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(order_table)
    else:
        elements.append(Paragraph("No orders found for the selected period.", styles['Normal']))
    
    # Footer
    elements.append(Spacer(1, 30))
    footer_text = f"Generated on {timezone.now().strftime('%Y-%m-%d %H:%M:%S')} | Vaitikan City"
    elements.append(Paragraph(footer_text, styles['Normal']))
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_order_analytics_pdf(period_days=30):
    """Generate an order analytics report PDF."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=1
    )
    
    title = Paragraph(f"Order Analytics Report<br/>Last {period_days} Days", title_style)
    elements.append(title)
    elements.append(Spacer(1, 12))
    
    # Calculate date range
    end_date = timezone.now().date()
    start_date = end_date - timezone.timedelta(days=period_days)
    
    # Check if we have any orders in this range, expand if needed
    orders_in_range = Order.objects.filter(
        **get_date_range_filter(start_date, end_date, 'order_date')
    ).exists()
    
    if not orders_in_range:
        first_order = Order.objects.order_by('order_date').first()
        if first_order:
            start_date = first_order.order_date.date()
            period_days = (end_date - start_date).days
    
    # Get orders
    date_filter = get_date_range_filter(start_date, end_date, 'order_date')
    orders = Order.objects.filter(**date_filter).select_related('user').prefetch_related('items')
    
    # Calculate statistics
    total_orders = orders.count()
    
    # Status breakdown
    status_counts = {}
    for status_code, status_label in Order.STATUS_CHOICES:
        count = orders.filter(status=status_code).count()
        if count > 0:
            status_counts[status_label] = count
    
    # Top customers
    top_customers = orders.values('user__full_name', 'user__email').annotate(
        order_count=Count('id')
    ).order_by('-order_count')[:10]
    
    # Summary
    summary_data = [
        ['Metric', 'Value'],
        ['Analysis Period', f'{start_date} to {end_date} ({period_days} days)'],
        ['Total Orders', str(total_orders)],
        ['Active Customers', str(len(set(order.user_id for order in orders)))],
        ['Average Orders/Day', f'{total_orders/period_days:.1f}' if period_days > 0 else '0'],
    ]
    
    summary_table = Table(summary_data, colWidths=[2.5*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(Paragraph("Summary", styles['Heading2']))
    elements.append(summary_table)
    elements.append(Spacer(1, 20))
    
    # Status breakdown
    if status_counts:
        elements.append(Paragraph("Order Status Distribution", styles['Heading2']))
        status_data = [['Status', 'Count', 'Percentage']]
        
        for status, count in status_counts.items():
            percentage = (count / total_orders * 100) if total_orders > 0 else 0
            status_data.append([status, str(count), f'{percentage:.1f}%'])
        
        status_table = Table(status_data, colWidths=[2*inch, 1*inch, 1.5*inch])
        status_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(status_table)
        elements.append(Spacer(1, 20))
    
    # Top customers
    if top_customers:
        elements.append(Paragraph("Top Customers", styles['Heading2']))
        customer_data = [['Customer', 'Email', 'Orders']]
        
        for customer in top_customers:
            customer_data.append([
                customer['user__full_name'][:25],
                customer['user__email'][:30],
                str(customer['order_count'])
            ])
        
        customer_table = Table(customer_data, colWidths=[2*inch, 2.5*inch, 1*inch])
        customer_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(customer_table)
    
    # Footer
    elements.append(Spacer(1, 30))
    footer_text = f"Generated on {timezone.now().strftime('%Y-%m-%d %H:%M:%S')} | Vaitikan City"
    elements.append(Paragraph(footer_text, styles['Normal']))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_financial_report_pdf(period_days=30):
    """Generate a financial report PDF."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=1
    )
    
    title = Paragraph(f"Financial Report<br/>Last {period_days} Days", title_style)
    elements.append(title)
    elements.append(Spacer(1, 12))
    
    # Calculate date range
    end_date = timezone.now().date()
    start_date = end_date - timezone.timedelta(days=period_days)
    
    # Check if we have any payments in this range, expand if needed
    payments_in_range = Payment.objects.filter(
        **get_date_range_filter(start_date, end_date, 'created_at')
    ).exists()
    
    if not payments_in_range:
        first_payment = Payment.objects.order_by('created_at').first()
        if first_payment:
            start_date = first_payment.created_at.date()
            period_days = (end_date - start_date).days
    
    # Get payments
    date_filter = get_date_range_filter(start_date, end_date, 'created_at')
    payments = Payment.objects.filter(**date_filter).select_related('order')
    
    # Calculate statistics
    total_payments = payments.count()
    successful_payments = payments.filter(payment_status='success')
    total_revenue = sum(payment.amount for payment in successful_payments)
    
    advance_revenue = sum(
        payment.amount for payment in successful_payments.filter(payment_type='advance')
    )
    final_revenue = sum(
        payment.amount for payment in successful_payments.filter(payment_type='final')
    )
    
    # Payment status breakdown
    status_counts = {}
    for status in ['success', 'pending', 'failed']:
        count = payments.filter(payment_status=status).count()
        status_counts[status.title()] = count
    
    # Payment type breakdown
    type_counts = {}
    for payment_type in ['advance', 'final']:
        count = payments.filter(payment_type=payment_type).count()
        type_counts[payment_type.title()] = count
    
    # Summary
    summary_data = [
        ['Metric', 'Value'],
        ['Analysis Period', f'{start_date} to {end_date} ({period_days} days)'],
        ['Total Payments', str(total_payments)],
        ['Successful Payments', str(successful_payments.count())],
        ['Total Revenue', f'₹{total_revenue:,.2f}'],
        ['Advance Payments', f'₹{advance_revenue:,.2f}'],
        ['Final Payments', f'₹{final_revenue:,.2f}'],
    ]
    
    summary_table = Table(summary_data, colWidths=[2.5*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(Paragraph("Summary", styles['Heading2']))
    elements.append(summary_table)
    elements.append(Spacer(1, 20))
    
    # Payment status breakdown
    elements.append(Paragraph("Payment Status Breakdown", styles['Heading2']))
    status_data = [['Status', 'Count', 'Percentage']]
    
    for status, count in status_counts.items():
        percentage = (count / total_payments * 100) if total_payments > 0 else 0
        status_data.append([status, str(count), f'{percentage:.1f}%'])
    
    status_table = Table(status_data, colWidths=[2*inch, 1*inch, 1.5*inch])
    status_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(status_table)
    elements.append(Spacer(1, 20))
    
    # Payment type breakdown
    elements.append(Paragraph("Payment Type Distribution", styles['Heading2']))
    type_data = [['Type', 'Count', 'Percentage']]
    
    for ptype, count in type_counts.items():
        percentage = (count / total_payments * 100) if total_payments > 0 else 0
        type_data.append([ptype, str(count), f'{percentage:.1f}%'])
    
    type_table = Table(type_data, colWidths=[2*inch, 1*inch, 1.5*inch])
    type_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(type_table)
    
    # Recent payments
    if payments.exists():
        elements.append(Spacer(1, 20))
        elements.append(Paragraph("Recent Payments", styles['Heading2']))
        
        payment_data = [['Date', 'Order ID', 'Type', 'Status', 'Amount']]
        
        for payment in payments.order_by('-created_at')[:20]:  # Last 20 payments
            payment_data.append([
                payment.created_at.strftime('%Y-%m-%d'),
                f'#{payment.order.id}',
                payment.payment_type.title(),
                payment.payment_status.title(),
                f'₹{payment.amount:,.2f}'
            ])
        
        payment_table = Table(payment_data, colWidths=[1.2*inch, 1*inch, 1*inch, 1*inch, 1.3*inch])
        payment_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(payment_table)
    
    # Footer
    elements.append(Spacer(1, 30))
    footer_text = f"Generated on {timezone.now().strftime('%Y-%m-%d %H:%M:%S')} | Vaitikan City"
    elements.append(Paragraph(footer_text, styles['Normal']))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer
