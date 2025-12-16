from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Q, Count
from .models import User
from django.contrib.auth.hashers import make_password


class AdminUserListView(LoginRequiredMixin, View):
    """Admin view to list all users with search and filtering"""
    
    def get(self, request):
        # Check if user is admin
        if not request.user.is_authenticated or request.user.user_type != 'admin':
            messages.error(request, 'Access denied. Admin privileges required.')
            return redirect('dashboard-web')
        
        # Get search and filter parameters
        search_query = request.GET.get('search', '')
        user_type_filter = request.GET.get('user_type', '')
        status_filter = request.GET.get('status', '')
        
        # Base queryset
        users = User.objects.all().order_by('-date_joined')
        
        # Apply search filter
        if search_query:
            users = users.filter(
                Q(full_name__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(phone__icontains=search_query)
            )
        
        # Apply user type filter
        if user_type_filter:
            users = users.filter(user_type=user_type_filter)
        
        # Apply status filter
        if status_filter:
            users = users.filter(account_status=status_filter)
        
        # Pagination
        paginator = Paginator(users, 20)  # Show 20 users per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'users': page_obj,
            'search_query': search_query,
            'user_type_filter': user_type_filter,
            'status_filter': status_filter,
            'user_type_choices': User.USER_TYPE_CHOICES,
            'status_choices': User.STATUS_CHOICES,
        }
        
        return render(request, 'users/admin/list.html', context)


class AdminUserDetailView(LoginRequiredMixin, View):
    """Admin view to show user details"""
    
    def get(self, request, user_id):
        # Check if user is admin
        if not request.user.is_authenticated or request.user.user_type != 'admin':
            messages.error(request, 'Access denied. Admin privileges required.')
            return redirect('dashboard-web')
        
        user = get_object_or_404(User, id=user_id)
        
        # Get user statistics
        order_count = 0
        recent_orders = []
        total_spent = 0
        try:
            # Import here to avoid circular imports
            from apps.orders.models import Order
            orders = Order.objects.filter(user=user)
            order_count = orders.count()
            recent_orders = orders.order_by('-order_date')[:5]  # Get 5 most recent orders
            
            # Calculate total spent
            for order in orders:
                total_spent += order.total_amount
                
        except ImportError:
            # If orders app is not available, keep defaults
            pass
        
        context = {
            'user_detail': user,
            'addresses': user.addresses.all(),
            'order_count': order_count,
            'recent_orders': recent_orders,
            'total_spent': total_spent,
        }
        
        return render(request, 'users/admin/detail.html', context)


class AdminUserCreateView(LoginRequiredMixin, View):
    """Admin view to create new users"""
    
    def get(self, request):
        # Check if user is admin
        if not request.user.is_authenticated or request.user.user_type != 'admin':
            messages.error(request, 'Access denied. Admin privileges required.')
            return redirect('dashboard-web')
        
        context = {
            'user_type_choices': User.USER_TYPE_CHOICES,
            'status_choices': User.STATUS_CHOICES,
        }
        
        return render(request, 'users/admin/create.html', context)
    
    def post(self, request):
        # Check if user is admin
        if not request.user.is_authenticated or request.user.user_type != 'admin':
            messages.error(request, 'Access denied. Admin privileges required.')
            return redirect('dashboard-web')
        
        try:
            full_name = request.POST.get('full_name')
            email = request.POST.get('email')
            phone = request.POST.get('phone')
            password = request.POST.get('password')
            user_type = request.POST.get('user_type', 'customer')
            account_status = request.POST.get('account_status', 'active')
            
            # Validation
            if not all([full_name, email, password]):
                messages.error(request, 'Full name, email, and password are required.')
                return redirect('admin-user-create')
            
            if User.objects.filter(email=email).exists():
                messages.error(request, 'Email already exists.')
                return redirect('admin-user-create')
            
            if phone and User.objects.filter(phone=phone).exists():
                messages.error(request, 'Phone number already exists.')
                return redirect('admin-user-create')
            
            # Create user
            user = User.objects.create(
                username=email,
                email=email,
                full_name=full_name,
                phone=phone,
                user_type=user_type,
                account_status=account_status,
                password=make_password(password)
            )
            
            messages.success(request, f'User {user.full_name} created successfully.')
            return redirect('admin-user-list')
            
        except Exception as e:
            messages.error(request, f'Error creating user: {str(e)}')
            return redirect('admin-user-create')


class AdminUserEditView(LoginRequiredMixin, View):
    """Admin view to edit user details"""
    
    def get(self, request, user_id):
        # Check if user is admin
        if not request.user.is_authenticated or request.user.user_type != 'admin':
            messages.error(request, 'Access denied. Admin privileges required.')
            return redirect('dashboard-web')
        
        user = get_object_or_404(User, id=user_id)
        
        context = {
            'user_detail': user,
            'user_type_choices': User.USER_TYPE_CHOICES,
            'status_choices': User.STATUS_CHOICES,
        }
        
        return render(request, 'users/admin/edit.html', context)
    
    def post(self, request, user_id):
        # Check if user is admin
        if not request.user.is_authenticated or request.user.user_type != 'admin':
            messages.error(request, 'Access denied. Admin privileges required.')
            return redirect('dashboard-web')
        
        user = get_object_or_404(User, id=user_id)
        
        try:
            user.full_name = request.POST.get('full_name', user.full_name)
            user.email = request.POST.get('email', user.email)
            user.phone = request.POST.get('phone', user.phone)
            user.user_type = request.POST.get('user_type', user.user_type)
            user.account_status = request.POST.get('account_status', user.account_status)
            
            # Update password if provided
            new_password = request.POST.get('password')
            if new_password:
                user.password = make_password(new_password)
            
            user.save()
            
            messages.success(request, f'User {user.full_name} updated successfully.')
            return redirect('admin-user-detail', user_id=user.id)
            
        except Exception as e:
            messages.error(request, f'Error updating user: {str(e)}')
            return redirect('admin-user-edit', user_id=user.id)


class AdminUserDeleteView(LoginRequiredMixin, View):
    """Admin view to delete users"""
    
    def post(self, request, user_id):
        # Check if user is admin
        if not request.user.is_authenticated or request.user.user_type != 'admin':
            messages.error(request, 'Access denied. Admin privileges required.')
            return redirect('dashboard-web')
        
        user = get_object_or_404(User, id=user_id)
        
        # Prevent admin from deleting themselves
        if user.id == request.user.id:
            messages.error(request, 'You cannot delete your own account.')
            return redirect('admin-user-list')
        
        try:
            user_name = user.full_name
            user.delete()
            messages.success(request, f'User {user_name} deleted successfully.')
        except Exception as e:
            messages.error(request, f'Error deleting user: {str(e)}')
        
        return redirect('admin-user-list')


class AdminUserStatusToggleView(LoginRequiredMixin, View):
    """Admin view to toggle user status (active/inactive/suspended)"""
    
    def post(self, request, user_id):
        # Check if user is admin
        if not request.user.is_authenticated or request.user.user_type != 'admin':
            messages.error(request, 'Access denied. Admin privileges required.')
            return redirect('dashboard-web')
        
        user = get_object_or_404(User, id=user_id)
        new_status = request.POST.get('status')
        
        if new_status in ['active', 'inactive', 'suspended']:
            user.account_status = new_status
            user.save()
            messages.success(request, f'User {user.full_name} status updated to {new_status}.')
        else:
            messages.error(request, 'Invalid status.')
        
        return redirect('admin-user-detail', user_id=user.id)