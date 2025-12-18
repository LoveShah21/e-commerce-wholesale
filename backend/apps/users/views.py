from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils.decorators import method_decorator
from utils.rate_limiting import rate_limit_auth, rate_limit_api
from .serializers import (
    UserRegistrationSerializer, UserSerializer, 
    AddressSerializer, AddressCreateSerializer
)
from .models import Address

@method_decorator(rate_limit_auth, name='post')
class RegisterView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = (permissions.AllowAny,)

@method_decorator(rate_limit_api, name='get')
@method_decorator(rate_limit_api, name='put')
@method_decorator(rate_limit_api, name='patch')
class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user

@method_decorator(rate_limit_api, name='post')
class LogoutView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response(status=status.HTTP_400_BAD_REQUEST)

@method_decorator(rate_limit_api, name='get')
@method_decorator(rate_limit_api, name='post')
class AddressListCreateView(generics.ListCreateAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    
    def get_queryset(self):
        return Address.objects.filter(user=self.request.user).select_related(
            'postal_code__city__state__country'
        ).order_by('-is_default', '-created_at')
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AddressCreateSerializer
        return AddressSerializer
    
    def create(self, request, *args, **kwargs):
        # Use AddressCreateSerializer for creation
        serializer = AddressCreateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        address = serializer.save()
        
        # Use AddressSerializer for response
        response_serializer = AddressSerializer(address)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

@method_decorator(rate_limit_api, name='get')
@method_decorator(rate_limit_api, name='put')
@method_decorator(rate_limit_api, name='patch')
@method_decorator(rate_limit_api, name='delete')
class AddressDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = AddressSerializer
    
    def get_queryset(self):
        return Address.objects.filter(user=self.request.user).select_related(
            'postal_code__city__state__country'
        )
