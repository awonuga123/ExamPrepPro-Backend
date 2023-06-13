import jwt
from .models import Jwt
from django.contrib.auth.models import User
from datetime import datetime, timedelta
from django.conf import settings
import random
import string
from rest_framework.views import APIView
from .serializers import LoginSerializer, RegisterSerializer, RefreshSerializer, OrganizeQuizSerializer, JoinQuizSerializer
from django.contrib.auth import authenticate
from rest_framework.response import Response
from .authentication import Authentication
from rest_framework.permissions import IsAuthenticated
from .models import OrganizeQuiz, JoinQuiz
import json


def get_rand(length):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

# the function generates access token: an access token hold the information of a logged in user


def get_access_token(payload):
    return jwt.encode(
        {
            "exp": datetime.now() + timedelta(minutes=30), **payload},
        settings.SECRET_KEY,
        algorithm="HS256"
    )

# this function  generates a refresh token for the access tokent to renewed


def get_refresh_token():
    return jwt.encode(
        {
            "exp": datetime.now() + timedelta(days=365), "data": get_rand(10)},
        settings.SECRET_KEY,
        algorithm="HS256"
    )

# Login API


class LoginView(APIView):
    serializer_class = LoginSerializer

    def post(self, request):
        data = json.loads(request.body)
        serializer = self.serializer_class(data=data)
        serializer.is_valid(raise_exception=True)

        user = authenticate(
            username=serializer.validated_data['username'],
            password=serializer.validated_data['password'])

        if not user:
            return Response({"error": "invalid login or password"}, status=400)

        Jwt.objects.filter(user_id=user.pk).delete()

        access = get_access_token({"user_id": user.id})
        refresh = get_refresh_token()

        Jwt.objects.create(user_id=user.id, access=access, refresh=refresh)

        return Response({"access": access, "refresh": refresh, "username": user.username})


class RegisterView(APIView):
    serializer_class = RegisterSerializer

    def post(self, request):
        data = json.loads(request.body)
        serializer = self.serializer_class(data=data)
        serializer.is_valid(raise_exception=True)

        user = authenticate(
            username=serializer.validated_data['username'],)

        if user:
            return Response({"error": "Username or Email already exist"}, status=400)

        try:
            User.objects.create_user(**serializer.validated_data)
            return Response({"success": "Your account has been successfully created"})
        except Exception:
            return Response({"error": "Username or Email already exist"}, status=400)


# the class renews the access token with the refresh token
class RefreshView(APIView):
    serializer_class = RefreshSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            active_jwt = Jwt.objects.get(
                refresh=serializer.validated_data['refresh'])
        except Exception:
            return Response({"error": "Refresh token doesnt exist"}, status=400)

        if not Authentication.verify_token(serializer.validated_data['refresh']):
            return Response({"error": "Token is invalid of has expired"})

        access = get_access_token({"user_id": active_jwt.user.id})
        refresh = get_refresh_token()

        active_jwt.access = access
        active_jwt.refresh = refresh

        active_jwt.save()

        return Response({"access": access, "refresh": refresh})


class GetSecuredData(APIView):
    authentication_classes = [Authentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_id = request.user.id
        quiz_details = OrganizeQuiz.objects.filter(organiser_id=user_id).values(
            'quiz_title', 'subject', 'quiz_id', 'created_at', 'status')
        username = User.objects.get(id=user_id)

        context = {
            "user": username.username,
            "quiz-details": quiz_details
        }
        return Response(context)


class OrganizeQuizView(APIView):
    serializer_class = OrganizeQuizSerializer

    def post(self, request):
        data = json.loads(request.body)

        serializer = self.serializer_class(data=data)
        serializer.is_valid(raise_exception=True)

        user = request.user.id

        subject = serializer.validated_data['subject']
        quiz_title = serializer.validated_data['quiz_title']
        username = serializer.validated_data['user']

        user = User.objects.get(username=username)
        try:
            OrganizeQuiz.objects.create(
                organiser_id_id=user.id, subject=subject, quiz_title=quiz_title)
        except Exception:
            return Response({"error": "Quiz title already exist, please use another quiz title"}, status=400)

        queryset = OrganizeQuiz.objects.filter(
            organiser_id=user.id).values_list('quiz_title', 'subject', 'quiz_id', 'created_at')

        context = {
            "success": "Quiz created",
            "quiz_details":  list(queryset)[-1]
        }

        return Response(context)


class JoinQuizView(APIView):
    serializer_class = JoinQuizSerializer

    def post(self, request):
        data = json.loads(request.body)
        serializer = self.serializer_class(data=data)
        serializer.is_valid(raise_exception=True)

        name = data['name']
        quiz_id = data['quiz_id']

        if not OrganizeQuiz.objects.filter(quiz_id=quiz_id).exists():
            return Response({"error": "Invalid quiz ID, please provide correct Quiz ID"}, status=500)

        if OrganizeQuiz.objects.get(quiz_id=quiz_id).past:
            return Response({"error": "This quiz already elapsed"}, status=500)
        try:
            queryset = JoinQuiz.objects.filter(quiz_id=quiz_id).get(name=name)
            return Response({"success": "Joined room successfully"})
        except Exception:
            JoinQuiz.objects.create(**serializer.validated_data)
            return Response({"success": "Joined room successfully"})


class QuizStatus(APIView):
    authentication_classes = [Authentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user_id = request.user.id
        status = OrganizeQuiz.objects.filter(organiser_id_id=user_id).values_list(
            'quiz_title', 'subject', 'quiz_id', 'created_at', 'status', 'past')
        context = {
            "data": list(status)[-1]
        }
        data = json.loads(request.body)

        if data['status']:
            quiz_id = context['data'][2]
            quiz_status = data['status']
            query = OrganizeQuiz.objects.get(quiz_id=quiz_id)
            query.status = quiz_status
            query.save(update_fields=['status'])

            return Response({"status": "Quiz Started"})

        elif data['past']:
            quiz_id = context['data'][2]
            quiz_past = data['past']
            query = OrganizeQuiz.objects.get(quiz_id=quiz_id)
            query.past = quiz_past
            query.save(update_fields=['past'])
            return Response({"status": "Successfullly passsed"})


class JoinedUserView(APIView):
    def get(self, request):
        quiz_id = request.GET.get('quiz_id')

        quiz_name = OrganizeQuiz.objects.get(quiz_id=quiz_id)

        query = JoinQuiz.objects.filter(
            quiz_id=quiz_id).values_list('quiz_id', 'name')

        status = OrganizeQuiz.objects.get(quiz_id=quiz_id).status
        past = OrganizeQuiz.objects.get(quiz_id=quiz_id).past

        return Response({'data': list(query), "status": status, "quiz_name": quiz_name.quiz_title, "past": past})


class QuizQuestionView(APIView):
    def get(self, request):
        quiz_id = request.GET.get('quiz_id')
        query = OrganizeQuiz.objects.get(quiz_id=quiz_id)
        data = query.questions
        return Response({"data": eval(data)})


class QuizScoreView(APIView):
    def post(self, request):
        data = json.loads(request.body)
        query = JoinQuiz.objects.filter(quiz_id=data['quiz_id'])
        query = query.get(name=data['name'])
        previous_score = query.score
        query.score = data['score'] + previous_score
        query.save()
        return Response({"data": f"your score {query.score}"})

    def get(self, request):
        quiz_id = request.GET.get('quiz_id')
        query = JoinQuiz.objects.filter(
            quiz_id=quiz_id).values_list('name', 'score')
        return Response({"data": list(query.order_by('-score'))})
