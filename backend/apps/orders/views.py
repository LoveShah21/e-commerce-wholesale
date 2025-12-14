from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from .models import Order, Cart, CartItem
from .serializers import OrderSerializer, OrderCreateSerializer, CartSerializer, CartItemSerializer

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
        
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class CartItemViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = CartItemSerializer
    
    def get_queryset(self):
        return CartItem.objects.filter(cart__user=self.request.user, cart__status='active')
        
    def perform_create(self, serializer):
        # Ensure cart exists
        cart, _ = Cart.objects.get_or_create(user=self.request.user, status='active')
        serializer.save(cart=cart)
