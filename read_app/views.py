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
                    if user.is_superuser:
                        return redirect('admin_dashboard')
                    elif user.account.role == 'student':
                        return redirect('student_dashboard')
                    elif user.account.role == 'publisher':
                        return redirect('publisher_dashboard')
                    elif user.account.role == 'instructor':
                        return redirect('instructor_dashboard')
                    else:
                        return redirect('student_dashboard')
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

def student_dashboard(request):
    if request.user.is_authenticated:
        return render(request, 'dashboards/student_dashboard.html')
    else:
        return redirect('login')

def publisher_dashboard(request):
    if request.user.is_authenticated:
        return render(request, 'dashboards/publisher_dashboard.html')
    else:
        return redirect('login')

def instructor_dashboard(request):
    if request.user.is_authenticated:
        return render(request, 'dashboards/instructor_dashboard.html')
    else:
        return redirect('login')

def admin_dashboard(request):
    if request.user.is_authenticated:
        studentsCount = Account.objects.filter(role='student').count()
        publishersCount = Account.objects.filter(role='publisher').count()
        instructorsCount = Account.objects.filter(role='instructor').count()
        usersCount = Account.objects.all().count()  
        return render(request, 'dashboards/admin_dashboard.html',{'studentsCount': studentsCount, 'publishersCount': publishersCount, 'instructorsCount': instructorsCount, 'usersCount': usersCount})
    else:
        return redirect('login')

def manage_students(request):
    if request.user.is_authenticated:
        students = Account.objects.filter(role='student')
        return render(request, 'admin/manage_students.html', {'students': students})
    else:
        return redirect('login')
    
def manage_publishers(request):
    if request.user.is_authenticated:
        publishers = Account.objects.filter(role='publisher')
        return render(request, 'admin/manage_publishers.html', {'publishers': publishers})
    else:
        return redirect('login')
    
def manage_instructors(request):
    if request.user.is_authenticated:
        instructors = Account.objects.filter(role='instructor')
        return render(request, 'admin/manage_instructors.html', {'instructors': instructors})
    else:
        return redirect('login')
    
def edit_student(request, user_id):
    if request.user.is_authenticated:
        student = User.objects.get(id=user_id)
        if request.method == 'POST':
            form = RegisterForm(request.POST, instance=student.user)
            if form.is_valid():
                form.save()
                return redirect('manage_students')
        else:
            form = RegisterForm(instance=student)
        return render(request, 'edit_student.html', {'form': form})
    else:
        return redirect('login')
    
def delete_student(request, user_id):
    if request.user.is_authenticated:
        student = User.objects.get(id=user_id)
        student.delete()
        return redirect('manage_students')
    else:
        return redirect('login')
