from rest_framework.views import APIView
from .serializers import UserRSerializer, UserLSerializer
from .renderers import UserRenderer
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters
from rest_framework.response import Response
from django.contrib.auth import authenticate, login, logout
from rest_framework import status
from django.middleware.csrf import get_token
from django.contrib.sessions.models import Session
from django.contrib.sessions.backends.db import SessionStore
from django.middleware.csrf import rotate_token
# from rest_framework.authtoken.models import Token
# from rest_framework import permissions
from rest_framework_api_key.permissions import HasAPIKey


def set_refresh_token_to_session(session_key: str, refresh_token: str):
    try:
        session = Session.objects.get(session_key=session_key)
        session_data = session.get_decoded()
        session_data['refresh_token'] = refresh_token
        session.session_data = SessionStore().encode(session_data)
        session.save()
    except Session.DoesNotExist:
        # Create a new session
        session = SessionStore()
        session.create()
        session_data = {'refresh_token': refresh_token}
        session_data_encoded = session.encode(session_data)
        session.session_data = session_data_encoded
        session.save()


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    payload = refresh.payload

    # Remove the 'user_id' field from the payload
    payload.pop('user_id', None)

    # Add 'uid' to the token payload as a string
    payload['uid'] = str(user.uid)

    # Reconstruct the refresh token with the updated payload
    refresh.payload = payload

    # Get the session key for the user
    session_key = user.get_session_auth_hash()

    # Set the refresh token into session storage
    set_refresh_token_to_session(session_key, str(refresh))

    return {'refresh': str(refresh), 'access': str(refresh.access_token)}


# Decorators for security measures
csrf_protect_m = method_decorator(csrf_protect)
csrf_ensure_m = method_decorator(ensure_csrf_cookie)
never_cache_m = method_decorator(never_cache)
sensitive_post_parameters_m = method_decorator(sensitive_post_parameters())
# user registration


class Registration(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [HasAPIKey]

    @csrf_ensure_m
    @never_cache_m
    def post(self, request, format=None):
        reg_serializer = UserRSerializer(data=request.data)
        if reg_serializer.is_valid(raise_exception=True):
            user = reg_serializer.save()
            tokens = get_tokens_for_user(user)
            refresh_token = tokens['refresh']
            access_token = tokens['access']

            response = Response({'token': access_token, 'msg': 'User registration successful'}, status=status.HTTP_201_CREATED)

            # Set the refresh token as an HTTP-only cookie
            response.set_cookie('refresh_token', refresh_token, httponly=True, samesite='None', secure=True)
            return response
        elif reg_serializer.errors:
            return Response(reg_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        else:
            # Check if username or email already exists in the errors
            if 'username' in reg_serializer.errors and 'email' in reg_serializer.errors:
                error_message = 'Username and email are already registered. Please login.'
            elif 'username' in reg_serializer.errors:
                error_message = 'Username is already registered. Please choose a different username.'
            elif 'email' in reg_serializer.errors:
                error_message = 'Email is already registered. Please use a different email.'
            else:
                error_message = 'Registration failed.'

            return Response({'msg': error_message}, status=status.HTTP_400_BAD_REQUEST)


# user login section
class Login(APIView):

    renderer_classes = [UserRenderer]
    permission_classes = [HasAPIKey]

    @csrf_ensure_m
    @never_cache_m
    def post(self, request, format=None):
        serializer = UserLSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            email = serializer.data.get('email')
            password = serializer.data.get('password')
            user = authenticate(email=email, password=password)
            if user is not None:
                login(request, user)  # Logs the user in and creates a session
                # Generate the token
                token = get_tokens_for_user(user)
                # Set the token as an HTTP-only session cookie
                csrf_token = get_token(request)
                session_id = request.session.session_key
                response = Response({'token': token, '_intercom_csrf_token': csrf_token,
                                    '_intercom_session_id': session_id, 'msg': 'Success Login'})
                # response.set_cookie('refresh_token', token['refresh'], httponly=True, samesite='Strict')

                return response
            else:
                print('User authentication failed:', email, password)

                return Response({'errors': {'non_field_errors': ['Email or password is not valid.']}}, status=400)
        else:
            print('Serializer validation failed:', serializer.errors)
            return Response({'errors': serializer.errors}, status=400)

# logout method


class Logout(APIView):

    @csrf_ensure_m
    @never_cache_m
    def post(self, request, format=None):
        logout(request)
        response = Response({'message': 'Logged out successfully.'})
        rotate_token(request)
        response.delete_cookie('refresh_token')
        return response
