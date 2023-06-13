from django.contrib import admin
from django.urls import path
from .views import *

urlpatterns = [
    path('login/', LoginView.as_view()),
    path('register/', RegisterView.as_view()),
    path('refresh/', RefreshView.as_view()),
    path("getdata/", GetSecuredData.as_view()),
    path("organize_quiz/", OrganizeQuizView.as_view()),
    path("join_quiz/", JoinQuizView.as_view()),
    path('quiz_status/', QuizStatus.as_view()),
    path('quiz_users/', JoinedUserView.as_view()),
    path('quiz_questions', QuizQuestionView.as_view()),
    path('quiz_set_score/', QuizScoreView.as_view())
]
