from django.contrib import admin
from .models import Jwt, OrganizeQuiz, JoinQuiz

admin.site.register((Jwt, OrganizeQuiz, JoinQuiz))
