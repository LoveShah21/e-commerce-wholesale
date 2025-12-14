from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from apps.users.web_views import WebLoginView, WebRegisterView, web_logout
from apps.products.web_views import ProductListView, ProductDetailView
from apps.dashboard.web_views import DashboardWebView
from apps.orders.web_views import OrderListView
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Web Routes
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
    path('login/', WebLoginView.as_view(), name='login'),
    path('register/', WebRegisterView.as_view(), name='register'),
    path('logout/', web_logout, name='logout'), # Changed to function view for logout redirect
    path('products/', ProductListView.as_view(), name='product-list-web'),
    path('products/<int:pk>/', ProductDetailView.as_view(), name='product-detail-web'),
    path('dashboard/', DashboardWebView.as_view(), name='dashboard-web'),
    path('orders/', OrderListView.as_view(), name='order-list-web'),

    # API Routes
    path('api/users/', include('apps.users.urls')),
    path('api/products/', include('apps.products.urls')),
    path('api/', include('apps.orders.urls')),
    path('api/dashboard/', include('apps.dashboard.urls')),
    path('api/support/', include('apps.support.urls')),
    path('api/reports/', include('apps.reports.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
