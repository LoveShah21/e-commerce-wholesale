from rest_framework import generics, permissions, status, viewsets, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import Order, Cart, CartItem
from .serializers import OrderSerializer, OrderCreateSerializer, CartSerializer, CartItemSerializer
from services.cart_service import CartService
from apps.users.permissions import IsAdmin

class OrderListCreateView(generics.ListCreateAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    filter_backends = (filters.OrderingFilter,)
    ordering_fields = ('order_date', 'status')
    ordering = ('-order_date',)
    
    def get_queryset(self):
        """
        Optimized queryset with select_related and prefetch_related.
        """
        return Order.objects.filter(
            user=self.request.user
        ).select_related(
            'user',
            'delivery_address',
            'delivery_address__postal_code',
            'delivery_address__postal_code__city',
            'delivery_address__postal_code__city__state',
            'delivery_address__postal_code__city__state__country'
        ).prefetch_related(
            'items__variant_size__variant__product',
            'items__variant_size__variant__fabric',
            'items__variant_size__variant__color',
            'items__variant_size__variant__pattern',
            'items__variant_size__size'
        ).order_by('-order_date')
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return OrderCreateSerializer
        return OrderSerializer
    
    def create(self, request, *args, **kwargs):
        # Use OrderCreateSerializer for creation
        serializer = OrderCreateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        
        # Use OrderSerializer for response
        response_serializer = OrderSerializer(order)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

class OrderDetailView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = (permissions.IsAuthenticated,)
    
    def get_queryset(self):
        """
        Optimized queryset with select_related and prefetch_related.
        Allow admin users to access any order, regular users only their own orders.
        """
        base_queryset = Order.objects.select_related(
            'user',
            'delivery_address',
            'delivery_address__postal_code',
            'delivery_address__postal_code__city',
            'delivery_address__postal_code__city__state',
            'delivery_address__postal_code__city__state__country'
        ).prefetch_related(
            'items__variant_size__variant__product',
            'items__variant_size__variant__fabric',
            'items__variant_size__variant__color',
            'items__variant_size__variant__pattern',
            'items__variant_size__size',
            'items__variant_size__stock_record'
        )
        
        # Admin users can access any order, regular users only their own
        if self.request.user.is_staff:
            return base_queryset
        else:
            return base_queryset.filter(user=self.request.user)

class CartViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = CartSerializer
    
    def get_queryset(self):
        """
        Optimized queryset with prefetch_related for cart items.
        """
        return Cart.objects.filter(
            user=self.request.user,
            status='active'
        ).prefetch_related(
            'items__variant_size__variant__product',
            'items__variant_size__variant__fabric',
            'items__variant_size__variant__color',
            'items__variant_size__variant__pattern',
            'items__variant_size__size',
            'items__variant_size__stock_record'
        )
    
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
        """
        Optimized queryset with select_related and prefetch_related.
        """
        return CartItem.objects.filter(
            cart__user=self.request.user,
            cart__status='active'
        ).select_related(
            'cart',
            'variant_size__variant__product',
            'variant_size__variant__fabric',
            'variant_size__variant__color',
            'variant_size__variant__pattern',
            'variant_size__size',
            'variant_size__stock_record'
        )
    
    def create(self, request, *args, **kwargs):
        """Add item to cart using CartService"""
        variant_size_id = request.data.get('variant_size_id') or request.data.get('variant_size')
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
