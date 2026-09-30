from django.contrib.auth.tokens import PasswordResetTokenGenerator


class EmailVerificationTokenGenerator(PasswordResetTokenGenerator):
    """Same HMAC scheme as Django's password reset tokens, salted differently
    and keyed off is_email_verified so a token is invalidated the moment it's used."""

    key_salt = "apps.accounts.tokens.EmailVerificationTokenGenerator"

    def _make_hash_value(self, user, timestamp):
        return f"{user.pk}{user.is_email_verified}{timestamp}{user.email}"


email_verification_token_generator = EmailVerificationTokenGenerator()


class PasswordResetTokenGeneratorWithEmail(PasswordResetTokenGenerator):
    key_salt = "apps.accounts.tokens.PasswordResetTokenGeneratorWithEmail"

    def _make_hash_value(self, user, timestamp):
        login_timestamp = "" if user.last_login is None else user.last_login.replace(microsecond=0, tzinfo=None)
        return f"{user.pk}{user.password}{login_timestamp}{timestamp}{user.email}"


password_reset_token_generator = PasswordResetTokenGeneratorWithEmail()
