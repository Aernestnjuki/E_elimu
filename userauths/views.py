from django.shortcuts import render
from django.contrib.auth.hashers import check_password

import random
from django.shortcuts import render
from django.core.mail import EmailMultiAlternatives
from E_elimu.settings import EMAIL_HOST_USER

from django.template.loader import render_to_string
from userauths import serializers as api_serializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import generics, status
from userauths.models import User, Profile
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = api_serializer.MyTokenObtainPairSerializer

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes =[AllowAny]
    serializer_class = api_serializer.RegisterSerializer


def generate_random_otp(length=7):
    otp = ''.join([str(random.randint(0, 9)) for _ in range(length)])
    return otp

class PasswordResetEmailVerifyAPIView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    serializer_class = api_serializer.UserSerializer

    def get_object(self):
        email = self.kwargs['email'] # /api/v1/user/password-reset/aernest@gmail.com/

        user = User.objects.get(email=email)

        if user:

            uuidb64 = user.pk
            refresh = RefreshToken.for_user(user)
            refresh_token = str(refresh.access_token)

            user.refresh_token = refresh_token
            user.otp = generate_random_otp()
            user.save()

            link = f"https://localhost:5173/create-new-password/?otp={user.otp}&uuidb64={uuidb64}&refresh_token={refresh_token}"
            print(link)

            context = {
                "link": link,
                "username": user.username
            }

            subject = "Password Rest Email"

            text_body = render_to_string("email/password_reset.txt", context)
            html_body = render_to_string("email/password_reset.html", context)

            msg = EmailMultiAlternatives(
                subject=subject,
                from_email=EMAIL_HOST_USER,
                to=[user.email],
                body=text_body
            )
            msg.attach_alternative(html_body, 'text/html')
            msg.send()

        return user


class PasswordChangeAPIView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = api_serializer.UserSerializer

    def create(self, request, *args, **kwargs):
        otp = request.data['otp']
        uuidb64 = request.data['uuidb64']
        password = request.data['password']

        user = User.objects.get(id=uuidb64, otp=otp)
        if user:
            user.set_password(password)
            user.otp = ''
            user.save()

            return Response({"messaga": "Password changed successfully!"}, status=status.HTTP_201_CREATED)
        else:
            return Response({"error": "Password not found!"}, status=status.HTTP_400_BAD_REQUEST)
        
class ChangePasswordAPIView(generics.CreateAPIView):
    serializer_class = api_serializer.UserSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        user_id = request.data['user_id']
        old_password = request.data['old_password']
        new_password = request.data['new_password']

        user = User.objects.get(id=user_id)

        if user is not None:
            if check_password(old_password, user.password):
                user.set_password(new_password)
                user.save()
                return Response({'Messages': 'Paasword changed successfully', 'icon': 'success'}, status=status.HTTP_201_CREATED)
            else:
                return Response({'Messages': 'Old Paasword is incorrect',  'icon': 'warning'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'Messages': 'User does not exist',  'icon': 'error'}, status=status.HTTP_400_BAD_REQUEST)