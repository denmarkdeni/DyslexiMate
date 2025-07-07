from django.http import HttpResponse
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django import forms
from .forms import RegisterForm, LoginForm
from .models import Account, StudentProfile, InstructorProfile, PublisherProfile
from .models import Account
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os, fitz  # PyMuPDF 

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
                messages.success(request, 'Registration successful.')
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
                    messages.success(request, 'Login successful.')
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
                    messages.error(request, 'Invalid username or password.')
                    return redirect('login')
    else:
        reg_form = RegisterForm()
        login_form = LoginForm()

    return render(request, 'login_reg.html', {
        'reg_form': reg_form,
        'login_form': login_form
    })

def logout_view(request):
    logout(request)
    messages.success(request, 'Logout successful.')
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
                messages.success(request, 'Updated.')
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
        messages.success(request, 'Deleted successfully.')
        return redirect('manage_students')
    else:
        return redirect('login')

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

def convert_text(request):
    if request.user.is_authenticated:
        return render(request, 'features/convert_text.html')
    else:
        return redirect('login')

@login_required
def student_profile(request):
    try:
        account = Account.objects.get(user=request.user, role='student')
    except ObjectDoesNotExist:
        return redirect('home')

    profile = StudentProfile.objects.filter(account=account).first()

    if request.method == 'POST':
        profile_picture = request.FILES.get('profile_picture')
        name = request.POST.get('name')
        age = request.POST.get('age')
        education_level = request.POST.get('education_level')
        school = request.POST.get('school')

        if profile_picture:
            account.profile_picture = profile_picture
            account.save()

        if name and age and education_level:
            if profile:
                profile.name = name
                profile.age = int(age)
                profile.education_level = education_level
                profile.school = school or ''
                profile.save()
            else:
                StudentProfile.objects.create(
                    account=account,
                    name=name,
                    age=int(age),
                    education_level=education_level,
                    school=school or ''
                )
        messages.success(request,"Profile Updated")
        return redirect('student_profile')

    return render(request, 'profiles/student_profile.html', {'account': account, 'profile': profile})

@login_required
def instructor_profile(request):
    try:
        account = Account.objects.get(user=request.user, role='instructor')
    except ObjectDoesNotExist:
        return redirect('home')

    profile = InstructorProfile.objects.filter(account=account).first()

    if request.method == 'POST':
        profile_picture = request.FILES.get('profile_picture')
        name = request.POST.get('name')
        qualification = request.POST.get('qualification')
        years_of_experience = request.POST.get('years_of_experience')
        specialization = request.POST.get('specialization')

        if profile_picture:
            account.profile_picture = profile_picture
            account.save()

        if name and qualification and years_of_experience:
            if profile:
                profile.name = name
                profile.qualification = qualification
                profile.years_of_experience = int(years_of_experience)
                profile.specialization = specialization or ''
                profile.save()
            else:
                InstructorProfile.objects.create(
                    account=account,
                    name=name,
                    qualification=qualification,
                    years_of_experience=int(years_of_experience),
                    specialization=specialization or ''
                )
        messages.success(request,"Profile Updated")
        return redirect('instructor_profile')

    return render(request, 'profiles/instructor_profile.html', {'account': account, 'profile': profile})

@login_required
def publisher_profile(request):
    try:
        account = Account.objects.get(user=request.user, role='publisher')
    except ObjectDoesNotExist:
        return redirect('home')

    profile = PublisherProfile.objects.filter(account=account).first()

    if request.method == 'POST':
        profile_picture = request.FILES.get('profile_picture')
        name = request.POST.get('name')
        company_name = request.POST.get('company_name')
        work_details = request.POST.get('work_details')
        website = request.POST.get('website')

        if profile_picture:
            account.profile_picture = profile_picture
            account.save()

        if name and company_name and work_details:
            if profile:
                profile.name = name
                profile.company_name = company_name
                profile.work_details = work_details
                profile.website = website or ''
                profile.save()
            else:
                PublisherProfile.objects.create(
                    account=account,
                    name=name,
                    company_name=company_name,
                    work_details=work_details,
                    website=website or ''
                )
        messages.success(request,"Profile Updated")
        return redirect('publisher_profile')

    return render(request, 'profiles/publisher_profile.html', {'account': account, 'profile': profile})