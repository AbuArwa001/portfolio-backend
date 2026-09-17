from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

class EmailOrUsernameModelBackend(ModelBackend):
    """
    Custom authentication backend that permits users to authenticate
    using either their username or their email address.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
        if username is None or password is None:
            return None
        try:
            user = UserModel.objects.filter(
                Q(username__iexact=username) | Q(email__iexact=username)
            ).first()
            if user and user.check_password(password) and self.user_can_authenticate(user):
                return user
        except Exception:
            return None
        return None
