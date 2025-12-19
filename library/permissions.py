from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsSuperuserOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        if not request.user or not request.user.is_authenticated:
            return False
        return bool(request.user.is_superuser)


class OTPRequiredForSensitiveAction(BasePermission):
    message = "Для этой операции требуется двухфакторная аутентификация (2FA)."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            if not request.user.is_authenticated:
                return False
            if request.user.is_superuser:
                return request.session.get("second_factor", False)
        return True
