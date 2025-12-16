from rest_framework.views import APIView
from rest_framework import permissions
from django.http import HttpResponse
from .utils import generate_invoice_pdf, generate_sales_report_pdf

class InvoiceDownloadView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, order_id):
        pdf_buffer = generate_invoice_pdf(order_id)
        if not pdf_buffer:
            return HttpResponse("Order not found", status=404)
            
        response = HttpResponse(pdf_buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="invoice_{order_id}.pdf"'
        return response

class SalesReportView(APIView):
    permission_classes = (permissions.IsAdminUser,)
    
    def get(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        if not start_date or not end_date:
            return HttpResponse("Missing dates", status=400)
            
        # Convert string dates to date objects
        from datetime import datetime
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        pdf_buffer = generate_sales_report_pdf(start_date_obj, end_date_obj)
        response = HttpResponse(pdf_buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="sales_report.pdf"'
        return response
