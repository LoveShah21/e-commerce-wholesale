from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import Order, Cart, CartItem
from .serializers import OrderSerializer, OrderCreateSerializer, CartSerializer, CartItemSerializer
from services.cart_service import CartService

class OrderListCreateView(generics.ListCreateAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by('-order_date')
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return OrderCreateSerializer
        return OrderSerializer

class OrderDetailView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = (permissions.IsAuthenticated,)
    
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

class CartViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = CartSerializer
    
    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user, status='active')
    
    def list(self, request, *args, **kwargs):
        """Get or create active cart with totals"""
        cart = CartService.get_or_create_cart(request.user)
        serializer = self.get_serializer(cart)
        
        # Add cart totals
        try:
            totals = CartService.calculate_cart_total(cart.id)
            data = serializer.data
            data['totals'] = totals
            return Response(data)
        except DjangoValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['delete'])
    def clear(self, request):
        """Clear all items from cart"""
        CartService.clear_cart(request.user)
        return Response({'message': 'Cart cleared successfully'}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'])
    def validate_stock(self, request):
        """Validate stock availability for all cart items"""
        cart = CartService.get_or_create_cart(request.user)
        try:
            validation_result = CartService.validate_cart_stock(cart.id)
            return Response(validation_result, status=status.HTTP_200_OK)
        except DjangoValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class CartItemViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = CartItemSerializer
    
    def get_queryset(self):
        return CartItem.objects.filter(cart__user=self.request.user, cart__status='active')
    
    def create(self, request, *args, **kwargs):
        """Add item to cart using CartService"""
        variant_size_id = request.data.get('variant_size')
        quantity = request.data.get('quantity', 1)
        
        try:
            result = CartService.add_to_cart(
                user=request.user,
                variant_size_id=variant_size_id,
                quantity=quantity
            )
            serializer = self.get_serializer(result['cart_item'])
            return Response(
                {
                    'data': serializer.data,
                    'message': result['message']
                },
                status=status.HTTP_201_CREATED if result['created'] else status.HTTP_200_OK
            )
        except DjangoValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, *args, **kwargs):
        """Update cart item quantity using CartService"""
        cart_item_id = kwargs.get('pk')
        quantity = request.data.get('quantity')
        
        if not quantity:
            return Response(
                {'error': 'Quantity is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            cart_item = CartService.update_cart_item(
                cart_item_id=cart_item_id,
                quantity=quantity,
                user=request.user
            )
            serializer = self.get_serializer(cart_item)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except DjangoValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, *args, **kwargs):
        """Remove item from cart using CartService"""
        cart_item_id = kwargs.get('pk')
        
        try:
            CartService.remove_cart_item(cart_item_id, request.user)
            return Response(
                {'message': 'Item removed from cart'},
                status=status.HTTP_204_NO_CONTENT
            )
        except DjangoValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
