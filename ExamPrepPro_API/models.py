from django.db import models
from django.contrib.auth.models import User
import random
import requests


class OrganizeQuiz(models.Model):
    organiser_id = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    subject = models.CharField(max_length=255)
    quiz_id = models.IntegerField(unique=True)
    past = models.BooleanField(default=False)
    status = models.BooleanField(default=False)
    questions = models.TextField()
    students = models.IntegerField(default=0)
    quiz_title = models.CharField(
        max_length=255, default=f"Quiz-{quiz_id}", unique=True)

    def save(self, *args, **kwargs):
        self.quiz_id = random.randrange(100000, 899999)
        if self.subject:
            url = f"https://the-trivia-api.com/api/questions?categories={self.subject}&limit=20"
            response = requests.get(url=url)
            self.questions = response.json()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quiz_title} - {self.organiser_id.username}"

# Model for access token and refresh token


class JoinQuiz(models.Model):
    quiz_id = models.IntegerField()
    name = models.CharField(max_length=255)
    score = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.name} - {self.quiz_id}"


class Jwt(models.Model):
    user = models.OneToOneField(
        User, related_name="login_user", on_delete=models.CASCADE)
    access = models.TextField()
    refresh = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{User.objects.get(id=self.user.id)}"
