"""
Email Service

Handles email operations including sending notifications for orders,
payments, and other system events using Django's email framework.
"""

import logging
from typing import Dict, Any, List, Optional
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.contrib.auth import get_user_model

from services.base import BaseService

User = get_user_model()
logger = logging.getLogger('services.email_service')


class EmailService(BaseService):
    """
    Service class for managing email operations.
    
    Provides methods for:
    - Sending order notifications
    - Payment reminders
    - System notifications
    - Template-based emails
    """
    
    @classmethod
    def send_final_payment_notification(
        cls,
        order_id: int,
        payment_amount: float,
        razorpay_order_id: str
    ) -> Dict[str, Any]:
        """
        Send final payment notification email to customer.
        
        Args:
            order_id: The ID of the order
            payment_amount: Amount for final payment
            razorpay_order_id: Razorpay order ID for payment
            
        Returns:
            A dictionary containing:
                - success: Boolean indicating if email was sent
                - message: Success or error message
                
        Raises:
            ValidationError: If order not found or email fails
        """
        cls.log_info(f"Sending final payment notification for order {order_id}")
        
        try:
            # Get order details
            from apps.orders.models import Order
            order = Order.objects.select_related('user', 'delivery_address').get(id=order_id)
            
            # Prepare email context
            domain = settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else '127.0.0.1:8000'
            context = {
                'order': order,
                'customer_name': order.user.full_name or order.user.email,
                'order_id': order.id,
                'payment_amount': payment_amount,
                'razorpay_order_id': razorpay_order_id,
                'payment_url': f"http://{domain}/orders/{order.id}/final-payment/",
                'orders_url': f"http://{domain}/orders/",
                'company_name': 'Vaitikan City',
                'support_email': settings.DEFAULT_FROM_EMAIL,
            }
            
            # Render email templates
            html_content = render_to_string('emails/final_payment_notification.html', context)
            text_content = strip_tags(html_content)
            
            # Create email
            subject = f'Final Payment Required - Order #{order.id}'
            from_email = settings.DEFAULT_FROM_EMAIL
            to_email = [order.user.email]
            
            # Send email
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=from_email,
                to=to_email
            )
            email.attach_alternative(html_content, "text/html")
            
            email.send()
            
            cls.log_info(f"Final payment notification sent to {order.user.email}")
            
            # Log email transaction
            logger.info(
                f"EMAIL_SENT | "
                f"Type: final_payment_notification | "
                f"OrderID: {order.id} | "
                f"Recipient: {order.user.email} | "
                f"Amount: Rs.{payment_amount} | "
                f"RazorpayOrderID: {razorpay_order_id}"
            )
            
            return {
                'success': True,
                'message': 'Final payment notification sent successfully'
            }
            
        except Order.DoesNotExist:
            cls.log_error(f"Order {order_id} not found")
            return {
                'success': False,
                'message': 'Order not found'
            }
        except Exception as e:
            cls.log_error(f"Failed to send final payment notification: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': f'Failed to send email: {str(e)}'
            }
    
    @classmethod
    def send_order_confirmation_email(
        cls,
        order_id: int
    ) -> Dict[str, Any]:
        """
        Send order confirmation email to customer.
        
        Args:
            order_id: The ID of the order
            
        Returns:
            A dictionary containing success status and message
        """
        cls.log_info(f"Sending order confirmation for order {order_id}")
        
        try:
            from apps.orders.models import Order
            order = Order.objects.select_related('user', 'delivery_address').prefetch_related('items__variant_size__variant__product').get(id=order_id)
            
            context = {
                'order': order,
                'customer_name': order.user.full_name or order.user.email,
                'company_name': 'Vaitikan City',
                'support_email': settings.DEFAULT_FROM_EMAIL,
                'order_tracking_url': f"{settings.ALLOWED_HOSTS[0]}/order-tracking/{order.id}/",
            }
            
            html_content = render_to_string('emails/order_confirmation.html', context)
            text_content = strip_tags(html_content)
            
            subject = f'Order Confirmation - Order #{order.id}'
            from_email = settings.DEFAULT_FROM_EMAIL
            to_email = [order.user.email]
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=from_email,
                to=to_email
            )
            email.attach_alternative(html_content, "text/html")
            email.send()
            
            cls.log_info(f"Order confirmation sent to {order.user.email}")
            
            return {
                'success': True,
                'message': 'Order confirmation sent successfully'
            }
            
        except Exception as e:
            cls.log_error(f"Failed to send order confirmation: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': f'Failed to send email: {str(e)}'
            }
    
    @classmethod
    def send_payment_success_email(
        cls,
        order_id: int,
        payment_type: str,
        payment_amount: float
    ) -> Dict[str, Any]:
        """
        Send payment success notification email.
        
        Args:
            order_id: The ID of the order
            payment_type: 'advance' or 'final'
            payment_amount: Amount paid
            
        Returns:
            A dictionary containing success status and message
        """
        cls.log_info(f"Sending payment success notification for order {order_id}")
        
        try:
            from apps.orders.models import Order
            order = Order.objects.select_related('user').get(id=order_id)
            
            context = {
                'order': order,
                'customer_name': order.user.full_name or order.user.email,
                'payment_type': payment_type,
                'payment_amount': payment_amount,
                'company_name': 'Vaitikan City',
                'support_email': settings.DEFAULT_FROM_EMAIL,
                'order_tracking_url': f"{settings.ALLOWED_HOSTS[0]}/order-tracking/{order.id}/",
            }
            
            html_content = render_to_string('emails/payment_success.html', context)
            text_content = strip_tags(html_content)
            
            subject = f'Payment Received - Order #{order.id}'
            from_email = settings.DEFAULT_FROM_EMAIL
            to_email = [order.user.email]
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=from_email,
                to=to_email
            )
            email.attach_alternative(html_content, "text/html")
            email.send()
            
            cls.log_info(f"Payment success notification sent to {order.user.email}")
            
            return {
                'success': True,
                'message': 'Payment success notification sent successfully'
            }
            
        except Exception as e:
            cls.log_error(f"Failed to send payment success notification: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': f'Failed to send email: {str(e)}'
            }
    
    @classmethod
    def send_quotation_notification(
        cls,
        quotation_price_id: int
    ) -> Dict[str, Any]:
        """
        Send quotation notification email to customer.
        
        Args:
            quotation_price_id: The ID of the quotation price
            
        Returns:
            A dictionary containing success status and message
        """
        cls.log_info(f"Sending quotation notification for quotation price {quotation_price_id}")
        
        try:
            from apps.support.models import QuotationPrice
            quotation_price = QuotationPrice.objects.select_related(
                'quotation__inquiry__user',
                'quotation__variant_size__variant__product',
                'quotation__variant_size__size'
            ).get(id=quotation_price_id)
            
            inquiry = quotation_price.quotation.inquiry
            user = inquiry.user
            
            # Prepare email context
            domain = settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else '127.0.0.1:8000'
            total_price = (float(quotation_price.unit_price) + float(quotation_price.customization_charge_per_unit)) * quotation_price.quoted_quantity
            
            context = {
                'inquiry': inquiry,
                'quotation_price': quotation_price,
                'customer_name': user.full_name or user.email,
                'inquiry_id': inquiry.id,
                'total_price': total_price,
                'inquiries_url': f"http://{domain}/inquiries/",
                'company_name': 'Vaitikan City',
                'support_email': settings.DEFAULT_FROM_EMAIL,
            }
            
            # Render email templates
            html_content = render_to_string('emails/quotation_notification.html', context)
            text_content = strip_tags(html_content)
            
            # Create email
            subject = f'Quotation Ready - Inquiry #{inquiry.id}'
            from_email = settings.DEFAULT_FROM_EMAIL
            to_email = [user.email]
            
            # Send email
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=from_email,
                to=to_email
            )
            email.attach_alternative(html_content, "text/html")
            
            email.send()
            
            cls.log_info(f"Quotation notification sent to {user.email}")
            
            # Log email transaction
            logger.info(
                f"EMAIL_SENT | "
                f"Type: quotation_notification | "
                f"InquiryID: {inquiry.id} | "
                f"Recipient: {user.email} | "
                f"QuotationPriceID: {quotation_price_id}"
            )
            
            return {
                'success': True,
                'message': 'Quotation notification sent successfully'
            }
            
        except Exception as e:
            cls.log_error(f"Failed to send quotation notification: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': f'Failed to send email: {str(e)}'
            }

    @classmethod
    def send_complaint_status_notification(
        cls,
        complaint_id: int
    ) -> Dict[str, Any]:
        """
        Send complaint status update notification email to customer.
        
        Args:
            complaint_id: The ID of the complaint
            
        Returns:
            A dictionary containing success status and message
        """
        cls.log_info(f"Sending complaint status notification for complaint {complaint_id}")
        
        try:
            from apps.support.models import Complaint
            complaint = Complaint.objects.select_related('user', 'order').get(id=complaint_id)
            
            user = complaint.user
            
            # Prepare email context
            domain = settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else '127.0.0.1:8000'
            
            context = {
                'complaint': complaint,
                'customer_name': user.full_name or user.email,
                'complaint_id': complaint.id,
                'complaints_url': f"http://{domain}/complaints/",
                'order_url': f"http://{domain}/order-tracking/{complaint.order.id}/" if complaint.order else None,
                'company_name': 'Vaitikan City',
                'support_email': settings.DEFAULT_FROM_EMAIL,
            }
            
            # Render email templates
            html_content = render_to_string('emails/complaint_status_notification.html', context)
            text_content = strip_tags(html_content)
            
            # Create email
            subject = f'Complaint Update - Complaint #{complaint.id}'
            from_email = settings.DEFAULT_FROM_EMAIL
            to_email = [user.email]
            
            # Send email
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=from_email,
                to=to_email
            )
            email.attach_alternative(html_content, "text/html")
            
            email.send()
            
            cls.log_info(f"Complaint status notification sent to {user.email}")
            
            # Log email transaction
            logger.info(
                f"EMAIL_SENT | "
                f"Type: complaint_status_notification | "
                f"ComplaintID: {complaint.id} | "
                f"Recipient: {user.email} | "
                f"Status: {complaint.status}"
            )
            
            return {
                'success': True,
                'message': 'Complaint status notification sent successfully'
            }
            
        except Exception as e:
            cls.log_error(f"Failed to send complaint status notification: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': f'Failed to send email: {str(e)}'
            }

    @classmethod
    def send_custom_notification(
        cls,
        recipient_email: str,
        subject: str,
        message: str,
        html_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a custom notification email.
        
        Args:
            recipient_email: Email address of recipient
            subject: Email subject
            message: Plain text message
            html_message: Optional HTML message
            
        Returns:
            A dictionary containing success status and message
        """
        cls.log_info(f"Sending custom notification to {recipient_email}")
        
        try:
            from_email = settings.DEFAULT_FROM_EMAIL
            
            if html_message:
                email = EmailMultiAlternatives(
                    subject=subject,
                    body=message,
                    from_email=from_email,
                    to=[recipient_email]
                )
                email.attach_alternative(html_message, "text/html")
                email.send()
            else:
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=from_email,
                    recipient_list=[recipient_email],
                    fail_silently=False
                )
            
            cls.log_info(f"Custom notification sent to {recipient_email}")
            
            return {
                'success': True,
                'message': 'Notification sent successfully'
            }
            
        except Exception as e:
            cls.log_error(f"Failed to send custom notification: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': f'Failed to send email: {str(e)}'
            }
    
    @classmethod
    def test_email_configuration(cls) -> Dict[str, Any]:
        """
        Test email configuration by sending a test email.
        
        Returns:
            A dictionary containing test results
        """
        cls.log_info("Testing email configuration")
        
        try:
            # Check if email settings are configured
            if not settings.EMAIL_HOST_USER:
                return {
                    'success': False,
                    'message': 'EMAIL_HOST_USER not configured'
                }
            
            # Send test email
            subject = 'Vaitikan City - Email Configuration Test'
            message = 'This is a test email to verify email configuration is working correctly.'
            from_email = settings.DEFAULT_FROM_EMAIL
            recipient_list = [settings.EMAIL_HOST_USER]  # Send to self
            
            send_mail(
                subject=subject,
                message=message,
                from_email=from_email,
                recipient_list=recipient_list,
                fail_silently=False
            )
            
            cls.log_info("Email configuration test successful")
            
            return {
                'success': True,
                'message': 'Email configuration is working correctly'
            }
            
        except Exception as e:
            cls.log_error(f"Email configuration test failed: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': f'Email configuration test failed: {str(e)}'
            }