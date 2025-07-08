"""
URL configuration for DyslexiMate project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from read_app import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('auth/', views.login_register, name='login'),
    path('logout/', views.logout_view, name='logout'),

    path('student-dashboard/', views.student_dashboard, name='student_dashboard'),
    path('instructor-dashboard/', views.instructor_dashboard, name='instructor_dashboard'),
    path('publisher-dashboard/', views.publisher_dashboard, name='publisher_dashboard'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),

    path('student/profile/', views.student_profile, name='student_profile'),
    path('instructor/profile/', views.instructor_profile, name='instructor_profile'),
    path('publisher/profile/', views.publisher_profile, name='publisher_profile'),

    path('admin-dashboard/students/', views.manage_students, name='manage_students'),
    path('admin-dashboard/publishers/', views.manage_publishers, name='manage_publishers'),
    path('admin-dashboard/instructors/', views.manage_instructors, name='manage_instructors'),

    path('convert-pdf-to-dyslexic/', views.convert_pdf, name='convert_pdf'),
    path('convert-text-to-dyslexic/', views.convert_text, name='convert_text'),

    path('publisher/upload/', views.upload_book, name='upload_book'),
    path('publisher/books/', views.book_list, name='book_list'),
    path('remove/books/<int:book_id>', views.remove_book, name='remove_book'),
    path('instructor/share/<int:book_id>/', views.share_book, name='share_book'),
    path('student/assigned-books/', views.assigned_books, name='assigned_books'),

    path('instructor/upload-quiz/', views.upload_quiz, name='upload_quiz'),
    path('instructor/quizzes/', views.quiz_list, name='quiz_list'),
    path('student/unattended-quizzes/', views.unattended_quizzes, name='unattended_quizzes'),
    path('student/take-quiz/<int:quiz_id>/', views.take_quiz, name='take_quiz'),
    path('student/quiz-results/<int:quiz_id>/', views.quiz_results, name='quiz_results'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)