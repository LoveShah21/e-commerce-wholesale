from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.views import View
from django.contrib import messages
from .models import User

class WebLoginView(View):
    def get(self, request):
        return render(request, 'auth/login.html')

    def post(self, request):
        email = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        if user:
            login(request, user)
            return redirect('/')
        else:
            messages.error(request, 'Invalid email or password')
            return render(request, 'auth/login.html')

class WebRegisterView(View):
    def get(self, request):
        return render(request, 'auth/register.html')

    def post(self, request):
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        confirm_pass = request.POST.get('confirm_password')

        if password != confirm_pass:
            messages.error(request, 'Passwords do not match')
            return render(request, 'auth/register.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered')
            return render(request, 'auth/register.html')

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            full_name=full_name,
            phone=phone
        )
        login(request, user)
        messages.success(request, 'Registration successful!')
        return redirect('/')

def web_logout(request):
    logout(request)
    return redirect('/login/')
