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

import fitz  # PyMuPDF
from io import BytesIO
from django.http import HttpResponse
from django.shortcuts import render, redirect
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
from django.conf import settings

def convert_pdf(request):
    if request.method == 'POST':
        if request.FILES.get('pdf_file'):
            pdf_file = request.FILES['pdf_file']

            # Step 1: Extract text from PDF
            doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
            extracted_text = ""
            for page in doc:
                extracted_text += page.get_text()

            # Step 2: Create a new dyslexia-friendly PDF
            buffer = BytesIO()
            c = canvas.Canvas(buffer, pagesize=A4)
            width, height = A4

            # Step 3: Register OpenDyslexic font (provide full path)
            font_path = os.path.join(settings.BASE_DIR, 'read_app', 'static', 'fonts', 'open-dyslexic.ttf')
            
            if os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont('OpenDyslexic', font_path))
                c.setFont("OpenDyslexic", 12)
            else:
                c.setFont("Helvetica-Bold", 12)

            # Step 4: Write text
            y = height - 40
            for line in extracted_text.split('\n'):
                if y < 50:
                    c.showPage()
                    y = height - 40
                    c.setFont("OpenDyslexic", 12)
                c.drawString(40, y, line)
                y -= 18

            c.save()
            buffer.seek(0)

            # Step 5: Return the PDF as response
            return HttpResponse(buffer, content_type='application/pdf')

    return render(request, 'features/convert_pdf.html')

