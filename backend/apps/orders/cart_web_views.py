from django.shortcuts import render
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin

class CartView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'cart/cart.html')

class CheckoutView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'checkout/checkout.html')

class OrderTrackingView(LoginRequiredMixin, View):
    def get(self, request, order_id):
        return render(request, 'orders/tracking.html', {'order_id': order_id})
