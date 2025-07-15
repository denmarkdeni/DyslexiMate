from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.shortcuts import render, redirect
from django.db.models import Count, Sum, Q
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ObjectDoesNotExist
from django import forms
from django.core.files.base import ContentFile
from .forms import RegisterForm, LoginForm
from .models import Account, StudentProfile, InstructorProfile, PublisherProfile, Subscription, Message
from .models import Book, BookAssignment, Quiz, Question, QuizSubmission, Review, Performance,ConversionHistory
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os, json, fitz  # PyMuPDF 

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
        context = {
            'points':QuizSubmission.objects.filter(student__user = request.user).aggregate(total=Sum('score'))['total'] or 0 , 
            'feedbacks': Review.objects.filter(student__user = request.user).count(),
            'conversions': request.user.account.conversions,
        }
        return render(request, 'dashboards/student_dashboard.html',context)
    else:
        return redirect('login')

def publisher_dashboard(request):
    if request.user.is_authenticated:
        context = {
            'books':Book.objects.filter(publisher__user = request.user).count() , 
            'reviews': Review.objects.filter(book__publisher__user = request.user).count(),
            'conversions': request.user.account.conversions,
        }
        return render(request, 'dashboards/publisher_dashboard.html',context)
    else:
        return redirect('login')

def instructor_dashboard(request):
    if request.user.is_authenticated:
        context = {
            'questions':Quiz.objects.filter(instructor__user = request.user).count()*5 , 
            'books_shared': BookAssignment.objects.filter(assigned_by__user = request.user).count(),
            'conversions': request.user.account.conversions,
        }
        return render(request, 'dashboards/instructor_dashboard.html',context)
    else:
        return redirect('login')

def admin_dashboard(request):
    if request.user.is_authenticated:
        performance , created = Performance.objects.get_or_create(id=1)
        context = {
            'studentsCount':  Account.objects.filter(role='student').count(), 
            'publishersCount': Account.objects.filter(role='publisher').count(), 
            'instructorsCount': Account.objects.filter(role='instructor').count(), 
            'usersCount': Account.objects.all().count(),
            'books': Book.objects.all().count(),
            'total_conversions': performance.text_conversions + performance.pdf_conversions,
        }
        return render(request, 'dashboards/admin_dashboard.html', context)
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

            # Step 5: Save conversion history
            account = Account.objects.get(user=request.user)
            converted_filename = f"converted_{account.user.username}_{pdf_file.name}"
            converted_file = ContentFile(buffer.getvalue(), name=converted_filename)

            ConversionHistory.objects.create(
                user=account,
                type='pdf',
                original_content=pdf_file,
                converted_content=converted_file,
                original_text=extracted_text
            )

            performance , created = Performance.objects.get_or_create(id=1)
            performance.pdf_conversions += 1
            performance.save()
            account = Account.objects.get(user=request.user)
            account.conversions +=1
            account.save()
            messages.success(request, "Success.")

            # Step 5: Return the PDF as response
            return HttpResponse(buffer, content_type='application/pdf')

    return render(request, 'features/convert_pdf.html')

def convert_text(request):
    if request.user.is_authenticated:
        return render(request, 'features/convert_text.html')
    else:
        return redirect('login')

@csrf_exempt
def log_text_conversion(request):
    if request.method == 'POST':
        account = Account.objects.get(user=request.user)
        data = json.loads(request.body)
        original_text = data.get('original_text', '')
        converted_text = data.get('converted_text', '')

        # Save conversion history
        ConversionHistory.objects.create(
            user=account,
            type='text',
            original_text=original_text,
            converted_text=converted_text
        )
        performance , created = Performance.objects.get_or_create(id=1)
        performance.text_conversions += 1
        performance.save()
        account = Account.objects.get(user=request.user)
        account.conversions +=1
        account.save()
        return JsonResponse({'message': 'Text Conversion Incremented.'})
    
@login_required
def conversion_history(request):
    account = Account.objects.get(user=request.user)
    history = ConversionHistory.objects.filter(user=account).order_by('-converted_at')
    return render(request, 'features/conversion_history.html', {'account': account, 'history': history})

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

def superuser_required(user):
    return user.is_superuser

@user_passes_test(superuser_required, login_url='login')
def manage_students(request):
    students = Account.objects.filter(role='student').select_related('user', 'studentprofile')
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        action = request.POST.get('action')
        user = User.objects.get(id=user_id)
        if action == 'deactivate':
            user.is_active = False
            user.save()
            messages.success(request,"User deactivated")
        elif action == 'activate':
            user.is_active = True
            user.save()
            messages.success(request,"User activated")
        elif action == 'delete':
            user.delete()
            messages.success(request,"User Deleted")
        return redirect('manage_students')
    return render(request, 'admin/manage_students.html', {'students': students})

@user_passes_test(superuser_required, login_url='login')
def manage_instructors(request):
    instructors = Account.objects.filter(role='instructor').select_related('user', 'instructorprofile')
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        action = request.POST.get('action')
        user = User.objects.get(id=user_id)
        if action == 'deactivate':
            user.is_active = False
            user.save()
            messages.success(request,"User deactivated")
        elif action == 'activate':
            user.is_active = True
            user.save()
            messages.success(request,"User activated")
        elif action == 'delete':
            user.delete()
            messages.success(request,"User Deleted")
        return redirect('manage_instructors')
    return render(request, 'admin/manage_instructors.html', {'instructors': instructors})

@user_passes_test(superuser_required, login_url='login')
def manage_publishers(request):
    publishers = Account.objects.filter(role='publisher').select_related('user', 'publisherprofile')
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        action = request.POST.get('action')
        user = User.objects.get(id=user_id)
        if action == 'deactivate':
            user.is_active = False
            user.save()
            messages.success(request,"User deactivated")
        elif action == 'activate':
            user.is_active = True
            user.save()
            messages.success(request,"User activated")
        elif action == 'delete':
            user.delete()
            messages.success(request,"User Deleted")
        return redirect('manage_publishers')
    return render(request, 'admin/manage_publishers.html', {'publishers': publishers})

@login_required
def upload_book(request):
    try:
        account = Account.objects.get(user=request.user, role='publisher')
    except ObjectDoesNotExist:
        return redirect('home')

    if request.method == 'POST':
        name = request.POST.get('name')
        author = request.POST.get('author')
        published_year = request.POST.get('published_year')
        is_dyslexic = request.POST.get('is_dyslexic') == 'on'
        description = request.POST.get('description')
        file = request.FILES.get('file')
        cover_image = request.FILES.get('cover_image')

        if name and author and published_year and file:
            Book.objects.create(
                publisher=account,
                name=name,
                author=author,
                published_year=int(published_year),
                is_dyslexic=is_dyslexic,
                file=file,
                description=description or '',
                cover_image=cover_image
            )
            messages.success(request,"Book Uploaded")
            return redirect('upload_book')

    return render(request, 'publishers/upload_book.html', {'account': account})

@login_required
def book_list(request):
    if request.user.is_superuser or not request.user.account.role == 'publisher':
        books = Book.objects.all().order_by('-uploaded_at')
    else:
        try:
            account = Account.objects.get(user=request.user, role='publisher')
        except ObjectDoesNotExist:
            return redirect('home')
        
        books = Book.objects.filter(publisher=account).order_by('-uploaded_at')

    return render(request, 'publishers/book_list.html', { 'books': books})

@login_required
def remove_book(request, book_id):
    book = Book.objects.get(id=book_id)
    book.delete()
    messages.success(request,"Book Removed")
    return redirect("book_list")

@login_required
def share_book(request, book_id):
    try:
        account = Account.objects.get(user=request.user, role='instructor')
        book = Book.objects.get(id=book_id)
    except ObjectDoesNotExist:
        return redirect('home')

    students = Account.objects.filter(role='student',subscriptions__instructor = account).select_related('studentprofile')
    # print(students[0].__dict__)
    if request.method == 'POST':
        student_ids = request.POST.getlist('students')  # Get list of selected student IDs
        if 'select_all' in request.POST:
            student_ids = [student.id for student in students]
        for student_id in student_ids:
            student = Account.objects.get(id=student_id, role='student')
            BookAssignment.objects.get_or_create(book=book, student=student, assigned_by=account)
        messages.success(request, "Success.")
        return redirect('book_list')

    return render(request, 'instructors/share_book.html', {'account': account, 'book': book, 'students': students})

@login_required
def assigned_books(request):
    try:
        account = Account.objects.get(user=request.user, role='student')
    except ObjectDoesNotExist:
        return redirect('home')

    assignments = BookAssignment.objects.filter(student=account).select_related('book').order_by('-assigned_at')
    return render(request, 'students/assigned_books.html', {'account': account, 'assignments': assignments})

@login_required
def upload_quiz(request):
    try:
        account = Account.objects.get(user=request.user, role='instructor')
    except ObjectDoesNotExist:
        return redirect('home')

    books = Book.objects.all()
    if request.method == 'POST':
        title = request.POST.get('title')
        book_id = request.POST.get('book')
        if title and all(request.POST.get(f'question_{i}') for i in range(1, 6)):
            quiz = Quiz.objects.create(
                instructor=account,
                title=title,
                book=Book.objects.get(id=book_id) if book_id else None
            )
            for i in range(1, 6):
                Question.objects.create(
                    quiz=quiz,
                    question_text=request.POST.get(f'question_{i}'),
                    option_1=request.POST.get(f'option_{i}_1'),
                    option_2=request.POST.get(f'option_{i}_2'),
                    option_3=request.POST.get(f'option_{i}_3'),
                    option_4=request.POST.get(f'option_{i}_4'),
                    correct_option=int(request.POST.get(f'correct_option_{i}'))
                )
            messages.success(request, "Success.")
            return redirect('quiz_list')
    return render(request, 'instructors/upload_quiz.html', {'account': account, 'books': books})

@login_required
def quiz_list(request):
    try:
        account = Account.objects.get(user=request.user, role='instructor')
    except ObjectDoesNotExist:
        return redirect('home')

    quizzes = Quiz.objects.filter(instructor=account).annotate(student_count=Count('quizsubmission')).order_by('-created_at')
    return render(request, 'instructors/quiz_list.html', {'account': account, 'quizzes': quizzes})

@login_required
def unattended_quizzes(request):
    try:
        account = Account.objects.get(user=request.user, role='student')
    except ObjectDoesNotExist:
        return redirect('home')

    submitted_quizzes = QuizSubmission.objects.filter(student=account).values_list('quiz_id', flat=True)
    quizzes = Quiz.objects.exclude(id__in=submitted_quizzes).order_by('-created_at')
    return render(request, 'students/unattended_quizzes.html', {'account': account, 'quizzes': quizzes})

@login_required
def take_quiz(request, quiz_id):
    try:
        account = Account.objects.get(user=request.user, role='student')
        quiz = Quiz.objects.get(id=quiz_id)
    except ObjectDoesNotExist:
        return redirect('home')

    if QuizSubmission.objects.filter(student=account, quiz=quiz).exists():
        return redirect('unattended_quizzes')

    questions = quiz.questions.all()
    if request.method == 'POST':
        answers = {str(q.id): int(request.POST.get(f'answer_{q.id}')) for q in questions}
        score = sum(1 for q in questions if answers[str(q.id)] == q.correct_option)
        QuizSubmission.objects.create(student=account, quiz=quiz, score=score, answers=answers)
        student_profile = account.studentprofile
        student_profile.points += score
        student_profile.save()
        messages.success(request, "Success.")
        return redirect('quiz_results', quiz_id=quiz.id)
    return render(request, 'students/take_quiz.html', {'account': account, 'quiz': quiz, 'questions': questions})

@login_required
def quiz_results(request, quiz_id):
    try:
        account = Account.objects.get(user=request.user, role='student')
        quiz = Quiz.objects.get(id=quiz_id)
    except ObjectDoesNotExist:
        return redirect('home') 

    submission = QuizSubmission.objects.filter(student=account, quiz=quiz).first()
    questions = quiz.questions.all()
    return render(request, 'students/quiz_results.html', {
        'account': account,
        'quiz': quiz,
        'submission': submission,
        'questions': questions,
        'total_points': account.studentprofile.points
    })

@login_required
def review_book(request, book_id):
    try:
        account = Account.objects.get(user=request.user, role='student')
        book = Book.objects.get(id=book_id)
    except ObjectDoesNotExist:
        return redirect('home')

    if Review.objects.filter(student=account, book=book).exists():
        messages.warning(request, "Already Reviewed.")
        return redirect('assigned_books')

    if request.method == 'POST':
        feedback = request.POST.get('feedback')
        rating = request.POST.get('rating')
        if feedback and rating:
            Review.objects.create(
                book=book,
                student=account,
                feedback=feedback,
                rating=int(rating)
            )
            messages.success(request, "Reviewed.")
            return redirect('assigned_books')
    return render(request, 'students/review_book.html', {'account': account, 'book': book})

@login_required
def review_details(request):
    try:
        account = Account.objects.get(user=request.user, role='publisher')
    except ObjectDoesNotExist:
        return redirect('home')

    reviews = Review.objects.filter(book__publisher=account).select_related('book', 'student__studentprofile').order_by('-created_at')
    return render(request, 'publishers/review_details.html', {'account': account, 'reviews': reviews})

@login_required
def subscribed_instructors(request):
    try:
        account = Account.objects.get(user=request.user, role='student')
    except ObjectDoesNotExist:
        return redirect('home')

    subscriptions = Subscription.objects.filter(student=account).select_related('instructor__instructorprofile')
    if request.method == 'POST':
        instructor_id = request.POST.get('instructor_id')
        action = request.POST.get('action')
        if action == 'unsubscribe':
            Subscription.objects.filter(student=account, instructor_id=instructor_id).delete()
        messages.success(request, "Unsubscribed.")
        return redirect('subscribed_instructors')
    return render(request, 'students/subscribed_instructors.html', {'account': account, 'subscriptions': subscriptions})

@login_required
def all_instructors(request):
    try:
        account = Account.objects.get(user=request.user, role='student')
    except ObjectDoesNotExist:
        return redirect('home')

    instructors = Account.objects.filter(role='instructor').select_related('instructorprofile')
    subscribed_instructor_ids = Subscription.objects.filter(student=account).values_list('instructor_id', flat=True)
    if request.method == 'POST':
        instructor_id = request.POST.get('instructor_id')
        action = request.POST.get('action')
        if action == 'subscribe':
            Subscription.objects.get_or_create(student=account, instructor_id=instructor_id)
        messages.success(request, "Subscribed.")
        return redirect('all_instructors')
    return render(request, 'students/all_instructors.html', {
        'account': account,
        'instructors': instructors,
        'subscribed_instructor_ids': subscribed_instructor_ids
    })

@login_required
def subscribed_students(request):
    try:
        account = Account.objects.get(user=request.user, role='instructor')
    except ObjectDoesNotExist:
        return redirect('home')

    subscriptions = Subscription.objects.filter(instructor=account).select_related('student__studentprofile').order_by('-subscribed_at')
    return render(request, 'instructors/subscribed_students.html', {'account': account, 'subscriptions': subscriptions}) 

@login_required
def send_message(request, student_id):
    try:
        account = Account.objects.get(user=request.user, role='instructor')
        student = Account.objects.get(id=student_id, role='student')
    except ObjectDoesNotExist:
        return redirect('home')

    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            Message.objects.create(
                sender=account,
                recipient=student,
                content=content
            )
            return redirect('subscribed_students')
    return render(request, 'instructors/send_message.html', {'account': account, 'student': student})

@login_required
def student_messages(request):
    try:
        account = Account.objects.get(user=request.user, role='student')
    except ObjectDoesNotExist:
        return redirect('home')

    messagess = Message.objects.filter(recipient=account).select_related('sender__instructorprofile')
    if request.method == 'POST':
        message_id = request.POST.get('message_id')
        reply_content = request.POST.get('reply_content')
        if message_id and reply_content:
            message = Message.objects.get(id=message_id, recipient=account, reply__isnull=True)
            Message.objects.create(
                sender=account,
                recipient=message.sender,
                content=reply_content,
                is_reply=True,
                replied_at=timezone.now()
            )
            message.reply = reply_content
            message.replied_at = timezone.now()
            message.save()
            return redirect('student_messages')
    return render(request, 'students/messages.html', {'account': account, 'messagess': messagess})

@login_required
def instructor_messages(request):
    try:
        account = Account.objects.get(user=request.user, role='instructor')
    except ObjectDoesNotExist:
        return redirect('home')

    messages = Message.objects.filter(Q(sender=account) | Q(recipient=account)).select_related('sender__instructorprofile', 'recipient__studentprofile').order_by('-sent_at')
    return render(request, 'instructors/messages.html', {'account': account, 'messages': messages})