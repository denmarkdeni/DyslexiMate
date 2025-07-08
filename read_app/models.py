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
    points = models.PositiveIntegerField(default=0)

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
    
class Book(models.Model):
    publisher = models.ForeignKey(Account, on_delete=models.CASCADE, limit_choices_to={'role': 'publisher'})
    name = models.CharField(max_length=200)
    author = models.CharField(max_length=100)
    published_year = models.PositiveIntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_dyslexic = models.BooleanField(default=False, help_text="Is this book dyslexic-friendly?")
    file = models.FileField(upload_to='books/', help_text="Upload PDF file")
    description = models.TextField(blank=True, help_text="Brief description of the book")
    cover_image = models.ImageField(upload_to='book_covers/', blank=True, null=True, default='book_covers/default_cover.jpg')

    def __str__(self):
        return f"{self.name} by {self.author}" 
    
class BookAssignment(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    student = models.ForeignKey(Account, on_delete=models.CASCADE, limit_choices_to={'role': 'student'})
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, limit_choices_to={'role': 'instructor'}, related_name='assignments')

    class Meta:
        unique_together = ('book', 'student')

    def __str__(self):
        return f"{self.book.name} assigned to {self.student.user.username}" 
    
class Quiz(models.Model):
    instructor = models.ForeignKey(Account, on_delete=models.CASCADE, limit_choices_to={'role': 'instructor'})
    title = models.CharField(max_length=200)
    book = models.ForeignKey(Book, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    question_text = models.CharField(max_length=500)
    option_1 = models.CharField(max_length=200)
    option_2 = models.CharField(max_length=200)
    option_3 = models.CharField(max_length=200)
    option_4 = models.CharField(max_length=200)
    correct_option = models.PositiveIntegerField(choices=[(1, 'Option 1'), (2, 'Option 2'), (3, 'Option 3'), (4, 'Option 4')])

    def __str__(self):
        return f"{self.quiz.title}: {self.question_text}"

class QuizSubmission(models.Model):
    student = models.ForeignKey(Account, on_delete=models.CASCADE, limit_choices_to={'role': 'student'})
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    score = models.PositiveIntegerField(default=0)
    submitted_at = models.DateTimeField(auto_now_add=True)
    answers = models.JSONField()  # Stores {question_id: selected_option}

    class Meta:
        unique_together = ('student', 'quiz')

    def __str__(self):
        return f"{self.student.user.username} - {self.quiz.title} ({self.score}/5)" 