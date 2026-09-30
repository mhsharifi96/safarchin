from django.conf import settings
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

from .tokens import email_verification_token_generator, password_reset_token_generator


def _uid_token_link(base_path: str, user) -> str:
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    return f"{settings.FRONTEND_BASE_URL}{base_path}?uid={uid}"


def send_verification_email(user) -> None:
    token = email_verification_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    link = f"{settings.FRONTEND_BASE_URL}/verify-email?uid={uid}&token={token}"
    send_mail(
        subject="تایید ایمیل سفرچین",
        message=(
            "سلام،\n\n"
            "برای تایید ایمیل خود در سفرچین روی لینک زیر کلیک کنید (تا ۲۴ ساعت معتبر است):\n"
            f"{link}\n\n"
            "اگر این درخواست را شما ثبت نکرده‌اید، این ایمیل را نادیده بگیرید."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )


def send_password_reset_email(user) -> None:
    token = password_reset_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    link = f"{settings.FRONTEND_BASE_URL}/reset-password?uid={uid}&token={token}"
    send_mail(
        subject="بازیابی رمز عبور سفرچین",
        message=(
            "سلام،\n\n"
            "برای تنظیم رمز عبور جدید روی لینک زیر کلیک کنید (تا ۱ ساعت معتبر است):\n"
            f"{link}\n\n"
            "اگر این درخواست را شما ثبت نکرده‌اید، این ایمیل را نادیده بگیرید و رمز عبور شما تغییر نخواهد کرد."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )
