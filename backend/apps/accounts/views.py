from django.contrib.auth import authenticate, get_user_model, login, logout
from django.middleware.csrf import get_token
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from .emails import send_password_reset_email, send_verification_email
from .serializers import (
    ForgotPasswordSerializer,
    LoginSerializer,
    ProfileUpdateSerializer,
    RegisterSerializer,
    ResendVerificationSerializer,
    ResetPasswordSerializer,
    UserSerializer,
    VerifyEmailSerializer,
)
from .tokens import email_verification_token_generator, password_reset_token_generator

User = get_user_model()

NEUTRAL_LOGIN_ERROR = "ایمیل یا رمز عبور نادرست است."
NEUTRAL_RESET_REQUESTED = "اگر این ایمیل در سفرچین ثبت شده باشد، لینک بازیابی رمز عبور برای آن ارسال شد."
NEUTRAL_VERIFICATION_SENT = "اگر این ایمیل ثبت شده و هنوز تایید نشده باشد، ایمیل تاییدیه ارسال شد."


def _decode_uid(uid: str):
    try:
        pk = force_str(urlsafe_base64_decode(uid))
        return User.objects.get(pk=pk)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return None


def _transfer_guest_trips(request, user) -> None:
    """Reassigns any trips owned by the anonymous request's session to the
    now-authenticated user. Must run before django.contrib.auth.login(),
    which rotates the session key."""
    from apps.trips.models import Trip

    session_key = request.session.session_key
    if not session_key:
        return
    Trip.objects.filter(owner__isnull=True, guest_session_key=session_key).update(
        owner=user, guest_session_key=""
    )


class CsrfBootstrapView(APIView):
    """Forces Django to set the csrftoken cookie (get_token marks it as used
    for this response). The frontend calls this once on load so the cookie
    is guaranteed to exist before any POST/PATCH/DELETE, including for
    guest sessions and page reloads where the cookie may have expired."""

    permission_classes = [AllowAny]

    def get(self, request):
        get_token(request)
        return Response({"detail": "ok"})


class RegisterView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth-write"

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        user = User.objects.create_user(
            email=data["email"], password=data["password"], full_name=data.get("full_name", "")
        )
        send_verification_email(user)
        _transfer_guest_trips(request, user)
        login(request, user)
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class VerifyEmailView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth-write"

    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = _decode_uid(serializer.validated_data["uid"])
        if user is None:
            return Response({"detail": "لینک تایید نامعتبر یا منقضی شده است."}, status=status.HTTP_400_BAD_REQUEST)
        # The token's hash includes is_email_verified, so it deliberately stops validating
        # the moment it's used once -- re-opening the same email (or its link twice) hits
        # this, and it's a success, not an error. Check it before the token so a correct
        # but now-stale token doesn't get reported as "invalid/expired".
        if user.is_email_verified:
            return Response({"detail": "ایمیل شما قبلاً تایید شده است."})
        if not email_verification_token_generator.check_token(user, serializer.validated_data["token"]):
            return Response({"detail": "لینک تایید نامعتبر یا منقضی شده است."}, status=status.HTTP_400_BAD_REQUEST)
        user.is_email_verified = True
        user.save(update_fields=["is_email_verified"])
        return Response({"detail": "ایمیل با موفقیت تایید شد."})


class ResendVerificationView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth-sensitive"

    def post(self, request):
        serializer = ResendVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = User.objects.get(email__iexact=serializer.validated_data["email"])
            if not user.is_email_verified:
                send_verification_email(user)
        except User.DoesNotExist:
            pass
        return Response({"detail": NEUTRAL_VERIFICATION_SENT})


class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth-write"

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(
            request,
            username=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
        )
        if user is None:
            return Response({"detail": NEUTRAL_LOGIN_ERROR}, status=status.HTTP_401_UNAUTHORIZED)
        _transfer_guest_trips(request, user)
        login(request, user)
        return Response(UserSerializer(user).data)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth-sensitive"

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = User.objects.get(email__iexact=serializer.validated_data["email"], is_active=True)
            send_password_reset_email(user)
        except User.DoesNotExist:
            pass
        return Response({"detail": NEUTRAL_RESET_REQUESTED})


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth-sensitive"

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        user = _decode_uid(data["uid"])
        if user is None or not password_reset_token_generator.check_token(user, data["token"]):
            return Response({"detail": "لینک بازیابی نامعتبر یا منقضی شده است."}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(data["new_password"])
        user.save(update_fields=["password"])
        return Response({"detail": "رمز عبور با موفقیت تغییر کرد. اکنون می‌توانید وارد شوید."})


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def patch(self, request):
        serializer = ProfileUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(request.user).data)
