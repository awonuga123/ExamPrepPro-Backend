from datetime import datetime, timedelta
from django.conf import settings
import jwt
from rest_framework.authentication import BaseAuthentication
from django.contrib.auth.models import User


class Authentication(BaseAuthentication):

    def authenticate(self, request):
        data = self.validate_request(request.headers)

        if not data:
            return None, None

        return self.get_user(data['user_id']), None

    def get_user(self, user_id):
        try:
            user = User.objects.get(id=user_id)
            return user
        except Exception:
            return None

    def validate_request(self, headers):
        authorization = headers.get('Authorization', None)

        if not authorization:
            return None
        token = headers['Authorization'][7:]
        username = headers['user']
        decoded_data = Authentication.verify_token(token=token)

        if not decoded_data:
            return None
        check_user = User.objects.get(username=username)
        if check_user.id != decoded_data['user_id']:
            return None
        return decoded_data

    @staticmethod
    def verify_token(token):
        try:
            decoded_data = jwt.decode(
                token, settings.SECRET_KEY, algorithms="HS256")
        except Exception:
            return None

        exp = decoded_data['exp']

        if datetime.now().timestamp() > exp:
            return None
        return decoded_data
    