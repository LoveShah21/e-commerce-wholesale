from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    RegisterView, UserProfileView, LogoutView,
    AddressListCreateView, AddressDetailView
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    # Address endpoints
    path('addresses/', AddressListCreateView.as_view(), name='address-list-create'),
    path('addresses/<int:pk>/', AddressDetailView.as_view(), name='address-detail'),
]
