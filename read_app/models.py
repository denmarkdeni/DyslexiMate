from django.db import models
from django.contrib.auth.models import User

class Account(models.Model):
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('publisher', 'Publisher'),
        ('instructor', 'Instructor'),   
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    profile_picture = models.ImageField(upload_to='profile_pics/', default='profile_pics/default.jpg')
    
    def __str__(self):
        return f"{self.user.username} ({self.role})"

class StudentProfile(models.Model):
    account = models.OneToOneField(Account, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    age = models.PositiveIntegerField()
    education_level = models.CharField(max_length=100)
    school = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"Student: {self.name}"

class InstructorProfile(models.Model):
    account = models.OneToOneField(Account, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    qualification = models.CharField(max_length=200)
    years_of_experience = models.PositiveIntegerField()
    specialization = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"Instructor: {self.name}"

class PublisherProfile(models.Model):
    account = models.OneToOneField(Account, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    company_name = models.CharField(max_length=200)
    work_details = models.TextField()
    website = models.URLField(blank=True)

    def __str__(self):
        return f"Publisher: {self.name}"