from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from django.http import HttpResponse
from apps.orders.models import Order
from io import BytesIO

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

def generate_sales_report(start_date, end_date):
    # Fallback/Placeholder logic for Sales Report PDF
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.drawString(100, 750, f"Sales Report ({start_date} to {end_date})")
    p.drawString(100, 730, "TODO: Implement detailed sales data aggregation here.")
    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer
