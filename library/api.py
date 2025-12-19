import pyotp
import io
from datetime import date
from django.contrib.auth import authenticate, login, logout as django_logout
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from django.db.models import Count
from openpyxl import Workbook
from docx import Document
from rest_framework import permissions, serializers, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework.permissions import IsAuthenticated
from library.models import Library, Book, Genre, Member, Loan, UserProfile, User
from library.serializers import LibrarySerializer, BookSerializer, GenreSerializer, LoanSerializer, UserSerializer

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

class SecondLoginSerializer(serializers.Serializer):
    key = serializers.CharField()

class UserProfileViewSet(GenericViewSet):
    permission_classes = [permissions.AllowAny]
    serializer_class = LoginSerializer

    @method_decorator(ensure_csrf_cookie)
    @action(detail=False, url_path="csrf", methods=["GET"])
    def csrf(self, request, *args, **kwargs):
        return Response({"ok": True})

    def get_serializer_class(self):
        return SecondLoginSerializer if self.action == "login_second_factor" else LoginSerializer

    @action(detail=False, url_path="info", methods=["GET"])
    def info(self, request, *args, **kwargs):
        return Response({
            "username": getattr(request.user, "username", ""),
            "is_authenticated": request.user.is_authenticated,
            "is_superuser": getattr(request.user, "is_superuser", False),
            "second_factor": request.session.get("second_factor", False)
        })

    @action(detail=False, url_path="login", methods=["POST"])
    def login_first_factor(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(
            username=serializer.validated_data["username"],
            password=serializer.validated_data["password"]
        )
        login(request, user)
        request.session["second_factor"] = False
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.totp_key = profile.totp_key or pyotp.random_base32()
        profile.save()
        return Response({
            "success": True,
            "is_authenticated": True,
            "first_factor": True,
            "second_factor": False,
            "username": user.username,
            "email": user.email,
            "is_superuser": user.is_superuser
        })

    @action(detail=False, url_path="otp-login", methods=["POST"], serializer_class=SecondLoginSerializer)
    def login_second_factor(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        profile = UserProfile.objects.get(user=request.user)
        totp = pyotp.TOTP(profile.totp_key)
        totp.verify(serializer.validated_data["key"])
        request.session["second_factor"] = True
        request.session.set_expiry(60)
        return Response({
            "success": True,
            "is_authenticated": True,
            "second_factor": True,
            "is_superuser": request.user.is_superuser
        })

    @action(detail=False, url_path="totp-url", methods=["GET"], permission_classes=[IsAuthenticated])
    def totp_url(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        profile.totp_key = profile.totp_key or pyotp.random_base32()
        profile.save()
        totp = pyotp.TOTP(profile.totp_key)
        return Response({"url": totp.provisioning_uri(name=request.user.username, issuer_name="MyLibraryApp")})

    @action(detail=False, url_path="logout", methods=["POST"], permission_classes=[IsAuthenticated])
    def logout(self, request, *args, **kwargs):
        django_logout(request)
        request.session["second_factor"] = False
        return Response({"success": True})

class BaseExportMixin:
    def export_queryset(self, queryset, columns, filename_base):
        file_type = self.request.query_params.get("type", "excel")

        if file_type == "excel":
            workbook = Workbook()
            sheet = workbook.active
            sheet.title = filename_base
            sheet.append(columns)
            for row in queryset:
                sheet.append([row.get(col, "") for col in columns])
            buffer = io.BytesIO()
            workbook.save(buffer)
            buffer.seek(0)
            return HttpResponse(
                buffer,
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        document = Document()
        for row in queryset:
            document.add_paragraph(" | ".join(str(row.get(col, "")) for col in columns))
        buffer = io.BytesIO()
        document.save(buffer)
        buffer.seek(0)
        return HttpResponse(
            buffer,
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

class GenreViewSet(ModelViewSet, BaseExportMixin):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["GET"])
    def stats(self, request):
        top = Genre.objects.annotate(c=Count("book")).order_by("-c").first()
        return Response({"count": self.get_queryset().count(), "top": getattr(top, "name", None)})

    @action(detail=False, methods=["GET"])
    def export(self, request):
        data = [{"ID": g.id, "Name": g.name, "User": g.user.username if g.user else ""} for g in self.get_queryset()]
        return self.export_queryset(data, ["ID", "Name", "User"], "Genres")

class LibraryViewSet(ModelViewSet, BaseExportMixin):
    queryset = Library.objects.all().order_by("name")
    serializer_class = LibrarySerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["GET"])
    def stats(self, request):
        top = Library.objects.annotate(c=Count("book__loan")).order_by("-c").first()
        return Response({"count": self.get_queryset().count(), "top": getattr(top, "name", None)})

    @action(detail=False, methods=["GET"])
    def export(self, request):
        data = [{"ID": l.id, "Name": l.name, "User": l.user.username if l.user else ""} for l in self.get_queryset()]
        return self.export_queryset(data, ["ID", "Name", "User"], "Libraries")

class BookViewSet(ModelViewSet, BaseExportMixin):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["GET"])
    def stats(self, request):
        most = Loan.objects.values("book__id", "book__title").annotate(c=Count("book")).order_by("-c").first()
        return Response({"count": self.get_queryset().count(), "most_borrowed": most})

    @action(detail=False, methods=["GET"])
    def export(self, request):
        data = [{
            "ID": b.id,
            "Title": b.title,
            "Genre": b.genre.name if b.genre else "",
            "Library": b.library.name if b.library else "",
            "Status": "Available" if b.is_available else "Borrowed"
        } for b in self.get_queryset()]
        return self.export_queryset(data, ["ID", "Title", "Genre", "Library", "Status"], "Books")

class LoanViewSet(ModelViewSet, BaseExportMixin):
    queryset = Loan.objects.select_related("book", "member", "user")
    serializer_class = LoanSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=["POST"], url_path="return")
    def return_book(self, request, pk=None):
        loan = self.get_object()
        loan.return_date = date.today()
        loan.save()
        return Response(self.get_serializer(loan).data)

    @action(detail=False, methods=["GET"])
    def stats(self, request):
        top = self.get_queryset().values("member__first_name").annotate(c=Count("id")).order_by("-c").first()
        return Response({"count": self.get_queryset().count(), "topReader": top})

    @action(detail=False, methods=["GET"])
    def export(self, request):
        data = [{
            "ID": l.id,
            "Book": l.book.title if l.book else "",
            "Member": l.member.first_name if l.member else "",
            "User": l.user.username if l.user else "",
            "Loan Date": l.loan_date,
            "Return Date": l.return_date
        } for l in self.get_queryset()]
        return self.export_queryset(data, ["ID", "Book", "Member", "User", "Loan Date", "Return Date"], "Loans")

class MemberViewSet(ModelViewSet, BaseExportMixin):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["GET"])
    def stats(self, request):
        return Response({
            "count_users": self.get_queryset().count(),
            "count_admins": self.get_queryset().filter(is_superuser=True).count()
        })

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        age = data.pop("age", None)
        user, created = User.objects.get_or_create(
            username=data.get("username"),
            defaults=data
        )
        if created and age is not None:
            profile = UserProfile.objects.get(user=user)
            profile.age = age
            profile.save()
        return Response(self.get_serializer(user).data, status=201)



    def update(self, request, *args, **kwargs):
        user = self.get_object()
        data = request.data.copy()
        age = data.pop("age", None)
        for k, v in data.items():
            setattr(user, k, v)
        user.save()
        profile, _ = UserProfile.objects.get_or_create(user=user)
        if age is not None:
            profile.age = age
            profile.save()
        return Response(self.get_serializer(user).data)

    @action(detail=False, methods=["GET"])
    def export(self, request):
        data = [{
            "ID": u.id,
            "Username": u.username,
            "Email": u.email,
            "Role": "Администратор" if u.is_superuser else "Читатель",
            "Age": getattr(getattr(u, "userprofile", None), "age", "")
        } for u in self.get_queryset()]
        return self.export_queryset(data, ["ID", "Username", "Email", "Role", "Age"], "Members")
