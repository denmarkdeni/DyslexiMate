from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from .forms import RegisterForm, LoginForm
from .models import Account
from django.contrib.auth.models import User

def home(request):
    return render(request, 'home.html')

def login_register(request):
    if request.method == 'POST':
        if 'register' in request.POST:
            reg_form = RegisterForm(request.POST)
            login_form = LoginForm()
            if reg_form.is_valid():
                user = User.objects.create_user(
                    username=reg_form.cleaned_data['username'],
                    password=reg_form.cleaned_data['password'],
                    email=reg_form.cleaned_data['email']
                )
                Account.objects.create(
                    user=user,
                    role=reg_form.cleaned_data['role']
                )
                return redirect('login')
        elif 'login' in request.POST:
            login_form = LoginForm(request.POST)
            reg_form = RegisterForm()
            if login_form.is_valid():
                user = authenticate(
                    username=login_form.cleaned_data['username'],
                    password=login_form.cleaned_data['password']
                )
                if user:
                    login(request, user)
                    return redirect('dashboard')
    else:
        reg_form = RegisterForm()
        login_form = LoginForm()

    return render(request, 'login_reg.html', {
        'reg_form': reg_form,
        'login_form': login_form
    })

def logout_view(request):
    logout(request)
    return redirect('login')

def dashboard(request):
    if request.user.is_authenticated:
        return render(request, 'dashboard.html')
    else:
        return redirect('login')

