from rest_framework import serializers


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField()
    email = serializers.EmailField()
    password = serializers.CharField()


class RefreshSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class OrganizeQuizSerializer(serializers.Serializer):
    user = serializers.CharField()
    subject = serializers.CharField()
    quiz_title = serializers.CharField()


class JoinQuizSerializer(serializers.Serializer):
    quiz_id = serializers.IntegerField()
    name = serializers.CharField()
