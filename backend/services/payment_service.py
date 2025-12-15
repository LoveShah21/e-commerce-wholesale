"""
Payment Service

Handles payment operations including Razorpay integration, payment creation,
signature verification, and payment status management.
"""

import logging
import hmac
import hashlib
from decimal import Decimal
from typing import Dict, Any, Optional
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings
from decouple import config

from apps.finance.models import Payment
from apps.orders.models import Order
from services.base import BaseService


logger = logging.getLogger('services.payment_service')


class PaymentService(BaseService):
    """
    Service class for managing payment operations with Razorpay integration.
    
    Provides methods for:
    - Creating Razorpay orders for advance and final payments
    - Verifying payment signatures
    - Processing successful and failed payments
    - Payment retry functionality
    - Webhook handling
    """
    
    # Razorpay configuration
    RAZORPAY_KEY_ID = config('RAZORPAY_KEY_ID', default='')
    RAZORPAY_KEY_SECRET = config('RAZORPAY_KEY_SECRET', default='')
    
    @classmethod
    def _get_razorpay_client(cls):
        """
        Get Razorpay client instance.
        
        Returns:
            Razorpay client instance
        """
        try:
            import razorpay
            client = razorpay.Client(auth=(cls.RAZORPAY_KEY_ID, cls.RAZORPAY_KEY_SECRET))
            return client
        except ImportError:
            cls.log_error("Razorpay SDK not installed")
            raise ValidationError("Payment gateway not configured")
        except Exception as e:
            cls.log_error(f"Failed to initialize Razorpay client: {str(e)}")
            raise ValidationError("Payment gateway initialization failed")
    
    @classmethod
    def create_razorpay_order(
        cls,
        order_id: int,
        payment_type: str,
        payment_method: str = 'upi'
    ) -> Dict[str, Any]:
        """
        Create a Razorpay order for advance or final payment.
        
        Advance payment: 50% of order total
        Final payment: Remaining 50% of order total
        
        Args:
            order_id: The ID of the order
            payment_type: 'advance' or 'final'
            payment_method: Payment method (default: 'upi')
            
        Returns:
            A dictionary containing:
                - payment: The created Payment instance
                - razorpay_order: Razorpay order details
                - message: Success message
                
        Raises:
            ValidationError: If validation fails or Razorpay API fails
        """
        cls.log_info(f"Creating {payment_type} payment for order {order_id}")
        
        # Validate payment type
        if payment_type not in ['advance', 'final']:
            cls.log_error(f"Invalid payment type: {payment_type}")
            raise ValidationError("Payment type must be 'advance' or 'final'")
        
        # Get order
        try:
            order = Order.objects.prefetch_related('items').get(id=order_id)
        except Order.DoesNotExist:
            cls.log_error(f"Order {order_id} not found")
            raise ValidationError("Order not found")
        
        # Calculate order total
        from services.order_service import OrderService
        order_totals = OrderService.get_order_total(order_id)
        total_amount = order_totals['total']
        
        # Calculate payment amount based on type
        if payment_type == 'advance':
            # 50% advance payment
            payment_amount = (total_amount * Decimal('0.5')).quantize(Decimal('0.01'))
        else:  # final
            # Check if advance payment exists
            advance_payment = Payment.objects.filter(
                order=order,
                payment_type='advance',
                payment_status='success'
            ).first()
            
            if not advance_payment:
                cls.log_error(f"No successful advance payment found for order {order_id}")
                raise ValidationError("Advance payment must be completed before final payment")
            
            # Remaining 50%
            payment_amount = (total_amount - advance_payment.amount).quantize(Decimal('0.01'))
        
        # Validate payment amount
        if payment_amount <= 0:
            cls.log_error(f"Invalid payment amount: {payment_amount}")
            raise ValidationError("Payment amount must be greater than zero")
        
        # Create Razorpay order
        try:
            client = cls._get_razorpay_client()
            
            # Amount in paise (smallest currency unit)
            amount_in_paise = int(payment_amount * 100)
            
            razorpay_order_data = {
                'amount': amount_in_paise,
                'currency': 'INR',
                'receipt': f'order_{order_id}_{payment_type}',
                'notes': {
                    'order_id': str(order_id),
                    'payment_type': payment_type
                }
            }
            
            razorpay_order = client.order.create(data=razorpay_order_data)
            cls.log_info(f"Created Razorpay order: {razorpay_order['id']}")
            
        except Exception as e:
            cls.log_error(f"Razorpay order creation failed: {str(e)}", exc_info=True)
            raise ValidationError(f"Failed to create payment order: {str(e)}")
        
        # Create Payment record
        def _create_payment():
            payment = Payment.objects.create(
                order=order,
                amount=payment_amount,
                payment_type=payment_type,
                payment_method=payment_method,
                payment_status='initiated',
                razorpay_order_id=razorpay_order['id']
            )
            cls.log_info(f"Created payment record {payment.id}")
            
            # Log payment transaction details
            logger.info(
                f"PAYMENT_CREATED | "
                f"PaymentID: {payment.id} | "
                f"OrderID: {order.id} | "
                f"Type: {payment_type} | "
                f"Amount: ₹{payment_amount} | "
                f"Method: {payment_method} | "
                f"RazorpayOrderID: {razorpay_order['id']} | "
                f"Status: initiated"
            )
            
            return payment
        
        payment = cls.execute_in_transaction(_create_payment)
        
        return {
            'payment': payment,
            'razorpay_order': razorpay_order,
            'message': f'{payment_type.capitalize()} payment order created successfully'
        }
    
    @classmethod
    def verify_payment_signature(
        cls,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str
    ) -> bool:
        """
        Verify Razorpay payment signature using HMAC SHA256.
        
        Args:
            razorpay_order_id: Razorpay order ID
            razorpay_payment_id: Razorpay payment ID
            razorpay_signature: Razorpay signature to verify
            
        Returns:
            True if signature is valid, False otherwise
        """
        cls.log_info(f"Verifying payment signature for order {razorpay_order_id}")
        
        try:
            # Create message to sign
            message = f"{razorpay_order_id}|{razorpay_payment_id}"
            
            # Generate expected signature
            expected_signature = hmac.new(
                cls.RAZORPAY_KEY_SECRET.encode('utf-8'),
                message.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures
            is_valid = hmac.compare_digest(expected_signature, razorpay_signature)
            
            if is_valid:
                cls.log_info(f"Payment signature verified successfully")
            else:
                cls.log_warning(f"Payment signature verification failed")
            
            return is_valid
            
        except Exception as e:
            cls.log_error(f"Signature verification error: {str(e)}", exc_info=True)
            return False
    
    @classmethod
    def process_successful_payment(
        cls,
        payment_id: int,
        razorpay_payment_id: str,
        razorpay_signature: str
    ) -> Dict[str, Any]:
        """
        Process a successful payment and update order status.
        
        This method performs the following operations atomically:
        1. Verify payment signature
        2. Update payment status to success
        3. Update order status based on payment type
        
        Args:
            payment_id: The ID of the Payment record
            razorpay_payment_id: Razorpay payment ID
            razorpay_signature: Razorpay signature
            
        Returns:
            A dictionary containing:
                - payment: The updated Payment instance
                - order: The updated Order instance
                - message: Success message
                
        Raises:
            ValidationError: If verification fails or payment not found
        """
        cls.log_info(f"Processing successful payment {payment_id}")
        
        def _process_payment():
            # Get payment
            try:
                payment = Payment.objects.select_related('order').get(id=payment_id)
            except Payment.DoesNotExist:
                cls.log_error(f"Payment {payment_id} not found")
                raise ValidationError("Payment not found")
            
            # Verify signature
            is_valid = cls.verify_payment_signature(
                payment.razorpay_order_id,
                razorpay_payment_id,
                razorpay_signature
            )
            
            if not is_valid:
                cls.log_error(f"Payment signature verification failed for payment {payment_id}")
                raise ValidationError("Payment signature verification failed")
            
            # Update payment record
            payment.razorpay_payment_id = razorpay_payment_id
            payment.razorpay_signature = razorpay_signature
            payment.payment_status = 'success'
            payment.paid_at = timezone.now()
            payment.save()
            
            cls.log_info(f"Updated payment {payment_id} to success")
            
            # Log successful payment transaction
            logger.info(
                f"PAYMENT_SUCCESS | "
                f"PaymentID: {payment.id} | "
                f"OrderID: {payment.order.id} | "
                f"Type: {payment.payment_type} | "
                f"Amount: ₹{payment.amount} | "
                f"Method: {payment.payment_method} | "
                f"RazorpayPaymentID: {razorpay_payment_id} | "
                f"Status: success"
            )
            
            # Update order status based on payment type
            order = payment.order
            
            if payment.payment_type == 'advance':
                # Advance payment successful - confirm order
                order.status = 'confirmed'
                order.save()
                cls.log_info(f"Updated order {order.id} to confirmed")
            elif payment.payment_type == 'final':
                # Final payment successful - order can be dispatched
                # Status update to dispatched should be done by admin
                cls.log_info(f"Final payment completed for order {order.id}")
            
            return payment, order
        
        payment, order = cls.execute_in_transaction(_process_payment)
        
        return {
            'payment': payment,
            'order': order,
            'message': 'Payment processed successfully'
        }
    
    @classmethod
    def handle_payment_failure(
        cls,
        payment_id: int,
        failure_reason: Optional[str] = None
    ) -> Payment:
        """
        Handle a failed payment.
        
        Args:
            payment_id: The ID of the Payment record
            failure_reason: Optional reason for failure
            
        Returns:
            The updated Payment instance
            
        Raises:
            ValidationError: If payment not found
        """
        cls.log_info(f"Handling payment failure for payment {payment_id}")
        
        def _handle_failure():
            try:
                payment = Payment.objects.get(id=payment_id)
            except Payment.DoesNotExist:
                cls.log_error(f"Payment {payment_id} not found")
                raise ValidationError("Payment not found")
            
            payment.payment_status = 'failed'
            payment.failure_reason = failure_reason or 'Payment failed'
            payment.save()
            
            cls.log_info(f"Updated payment {payment_id} to failed")
            
            # Log failed payment transaction
            logger.warning(
                f"PAYMENT_FAILED | "
                f"PaymentID: {payment.id} | "
                f"OrderID: {payment.order.id} | "
                f"Type: {payment.payment_type} | "
                f"Amount: ₹{payment.amount} | "
                f"Method: {payment.payment_method} | "
                f"Reason: {failure_reason or 'Payment failed'} | "
                f"Status: failed"
            )
            
            return payment
        
        return cls.execute_in_transaction(_handle_failure)
    
    @classmethod
    def retry_payment(
        cls,
        order_id: int,
        payment_type: str,
        payment_method: str = 'upi'
    ) -> Dict[str, Any]:
        """
        Retry a failed payment by creating a new payment order.
        
        Args:
            order_id: The ID of the order
            payment_type: 'advance' or 'final'
            payment_method: Payment method (default: 'upi')
            
        Returns:
            A dictionary containing new payment details
            
        Raises:
            ValidationError: If validation fails
        """
        cls.log_info(f"Retrying {payment_type} payment for order {order_id}")
        
        # Check if there's a failed payment
        failed_payment = Payment.objects.filter(
            order_id=order_id,
            payment_type=payment_type,
            payment_status='failed'
        ).first()
        
        if not failed_payment:
            cls.log_warning(f"No failed payment found for order {order_id}, type {payment_type}")
        
        # Create new payment order
        return cls.create_razorpay_order(order_id, payment_type, payment_method)
    
    @classmethod
    def check_payment_completion(cls, order_id: int) -> Dict[str, Any]:
        """
        Check if all required payments for an order are complete.
        
        Args:
            order_id: The ID of the order
            
        Returns:
            A dictionary containing:
                - advance_paid: Boolean indicating if advance is paid
                - final_paid: Boolean indicating if final is paid
                - fully_paid: Boolean indicating if order is fully paid
                - total_paid: Total amount paid
                - total_due: Total amount due
        """
        cls.log_info(f"Checking payment completion for order {order_id}")
        
        # Get order
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            cls.log_error(f"Order {order_id} not found")
            raise ValidationError("Order not found")
        
        # Get successful payments
        advance_payment = Payment.objects.filter(
            order=order,
            payment_type='advance',
            payment_status='success'
        ).first()
        
        final_payment = Payment.objects.filter(
            order=order,
            payment_type='final',
            payment_status='success'
        ).first()
        
        # Calculate totals
        from services.order_service import OrderService
        order_totals = OrderService.get_order_total(order_id)
        total_due = order_totals['total']
        
        total_paid = Decimal('0.00')
        if advance_payment:
            total_paid += advance_payment.amount
        if final_payment:
            total_paid += final_payment.amount
        
        return {
            'advance_paid': advance_payment is not None,
            'final_paid': final_payment is not None,
            'fully_paid': advance_payment is not None and final_payment is not None,
            'total_paid': total_paid,
            'total_due': total_due
        }
    
    @classmethod
    def handle_webhook(cls, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle Razorpay webhook events.
        
        Args:
            webhook_data: Webhook payload from Razorpay
            
        Returns:
            A dictionary containing processing result
        """
        cls.log_info(f"Processing Razorpay webhook: {webhook_data.get('event')}")
        
        event = webhook_data.get('event')
        payload = webhook_data.get('payload', {})
        
        if event == 'payment.captured':
            # Payment successful
            payment_entity = payload.get('payment', {}).get('entity', {})
            razorpay_order_id = payment_entity.get('order_id')
            razorpay_payment_id = payment_entity.get('id')
            
            # Find payment record
            try:
                payment = Payment.objects.get(razorpay_order_id=razorpay_order_id)
                
                # Update payment status
                payment.razorpay_payment_id = razorpay_payment_id
                payment.payment_status = 'success'
                payment.paid_at = timezone.now()
                payment.save()
                
                # Update order status
                order = payment.order
                if payment.payment_type == 'advance':
                    order.status = 'confirmed'
                    order.save()
                
                cls.log_info(f"Webhook processed: payment {payment.id} marked as success")
                
                return {
                    'status': 'success',
                    'message': 'Payment captured successfully'
                }
                
            except Payment.DoesNotExist:
                cls.log_error(f"Payment not found for Razorpay order {razorpay_order_id}")
                return {
                    'status': 'error',
                    'message': 'Payment record not found'
                }
        
        elif event == 'payment.failed':
            # Payment failed
            payment_entity = payload.get('payment', {}).get('entity', {})
            razorpay_order_id = payment_entity.get('order_id')
            error_description = payment_entity.get('error_description', 'Payment failed')
            
            # Find payment record
            try:
                payment = Payment.objects.get(razorpay_order_id=razorpay_order_id)
                
                # Update payment status
                payment.payment_status = 'failed'
                payment.failure_reason = error_description
                payment.save()
                
                cls.log_info(f"Webhook processed: payment {payment.id} marked as failed")
                
                return {
                    'status': 'success',
                    'message': 'Payment failure recorded'
                }
                
            except Payment.DoesNotExist:
                cls.log_error(f"Payment not found for Razorpay order {razorpay_order_id}")
                return {
                    'status': 'error',
                    'message': 'Payment record not found'
                }
        
        else:
            cls.log_info(f"Unhandled webhook event: {event}")
            return {
                'status': 'ignored',
                'message': f'Event {event} not handled'
            }
