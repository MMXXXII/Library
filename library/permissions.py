from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsSuperuserOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        if not request.user or not request.user.is_authenticated:
            return False
        return bool(request.user.is_superuser)


class OTPRequiredForDelete(BasePermission):
    message = "Для удаления требуется двухфакторная аутентификация (2FA)."

    def has_permission(self, request, view):
        if request.method != "DELETE":
            return True
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            second_factor = request.session.get("second_factor")
            return bool(second_factor)
        return True

