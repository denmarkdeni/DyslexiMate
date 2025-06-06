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

    path('admin-dashboard/students/', views.manage_students, name='manage_students'),
    path('admin-dashboard/publishers/', views.manage_publishers, name='manage_publishers'),
    path('admin-dashboard/instructors/', views.manage_instructors, name='manage_instructors'),

    path('admin-dashboard/edit-student/<int:user_id>/', views.edit_student, name='edit_student'),
    path('admin-dashboard/delete-student/<int:user_id>/', views.delete_student, name='delete_student'),

    path('convert-pdf-to-dyslexic/', views.convert_pdf, name='convert_pdf'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)