import io
from datetime import date
from django.contrib.auth import authenticate, login, logout as django_logout
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from django.db.models import Count
from openpyxl import Workbook
from rest_framework import permissions, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework.permissions import IsAuthenticated
from library.models import Library, Book, Genre, Member, Loan, UserProfile, User
from library.serializers import LibrarySerializer, BookSerializer, GenreSerializer, LoanSerializer, MemberSerializer

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

class UserProfileViewSet(GenericViewSet):
    permission_classes = [permissions.AllowAny]
    serializer_class = LoginSerializer

    @method_decorator(ensure_csrf_cookie)
    @action(detail=False, url_path="csrf", methods=["GET"])
    def csrf(self, request, *args, **kwargs):
        return Response({"ok": True})

    @action(detail=False, url_path="info", methods=["GET"])
    def info(self, request, *args, **kwargs):
        user = request.user
        return Response({
            "id": user.id,
            "username": user.username if user.is_authenticated else "",
            "is_authenticated": user.is_authenticated,
            "is_superuser": user.is_superuser if user.is_authenticated else False
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
        UserProfile.objects.get_or_create(user=user)
        return Response({
            "success": True,
            "is_authenticated": True,
            "username": user.username,
            "email": user.email,
            "is_superuser": user.is_superuser
        })


    @action(detail=False, url_path="logout", methods=["POST"], permission_classes=[IsAuthenticated])
    def logout(self, request, *args, **kwargs):
        django_logout(request)
        return Response({"success": True})

class BaseExportMixin:
    def export_queryset(self, queryset, columns, filename_base):
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = filename_base
        sheet.append(columns)
        for row in queryset:
            sheet.append([row.get(col, "") for col in columns])
        buffer = io.BytesIO()
        workbook.save(buffer)
        buffer.seek(0)
        return HttpResponse(buffer, content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

class GenreViewSet(ModelViewSet, BaseExportMixin):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["GET"])
    def stats(self, request):
        top = Genre.objects.annotate(c=Count("book")).order_by("-c").first()
        return Response({"count": self.get_queryset().count(), "top": top.name if top else None})

    @action(detail=False, methods=["GET"])
    def export(self, request):
        data = [{"ID": g.id, "Name": g.name, "User": g.user.username if g.user else ""} for g in self.get_queryset()]
        return self.export_queryset(data, ["ID", "Name", "User"], "Genres")


class LibraryViewSet(ModelViewSet, BaseExportMixin):
    queryset = Library.objects.order_by("name")
    serializer_class = LibrarySerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["GET"])
    def stats(self, request):
        top = Library.objects.annotate(c=Count("book__loan")).order_by("-c").first()
        return Response({"count": self.get_queryset().count(), "top": top.name if top else None})

    @action(detail=False, methods=["GET"])
    def export(self, request):
        data = [{"ID": l.id, "Name": l.name, "User": l.user.username if l.user else ""} for l in self.get_queryset()]
        return self.export_queryset(data, ["ID", "Name", "User"], "Libraries")


class BookViewSet(ModelViewSet, BaseExportMixin):
    queryset = Book.objects
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
    queryset = Loan.objects.all()
    serializer_class = LoanSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Loan.objects.all()
        return qs if self.request.user.is_superuser else qs.filter(member__user=self.request.user)
    
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


class MemberViewSet(ModelViewSet):
    queryset = Member.objects
    serializer_class = MemberSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"])
    def stats(self, request):
        qs = self.get_queryset()
        return Response({
            "count_users": qs.count(),
            "count_admins": qs.filter(user__is_superuser=True).count()
        })

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        age = data.pop("age", None)
        user, _ = User.objects.get_or_create(
            username=data.get("username"),
            defaults={
                "email": data.get("email", ""),
                "is_superuser": data.get("is_superuser", False),
                "is_staff": data.get("is_staff", False),
            }
        )
        member, _ = Member.objects.get_or_create(user=user)
        if age is not None:
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.age = age
            profile.save()
        return Response(self.get_serializer(member).data, status=201)

    def update(self, request, *args, **kwargs):
        member = self.get_object()
        user = member.user
        data = request.data.copy()

        if "username" in data:
            user.username = data["username"]
        if "email" in data:
            user.email = data["email"]
        if "password" in data:
            user.set_password(data["password"])
        if "is_superuser" in data:
            user.is_superuser = data["is_superuser"]
        if "is_staff" in data:
            user.is_staff = data["is_staff"]
        
        user.save()

        if "age" in data:
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.age = data["age"]
            profile.save()

        return Response(self.get_serializer(member).data)

    @action(detail=False, methods=["GET"])
    def export(self, request):
        data = []
        for u in self.get_queryset():
            profile = UserProfile.objects.filter(user=u).first()
            data.append({
                "ID": u.id,
                "Username": u.username,
                "Email": u.email,
                "Role": "Администратор" if u.is_superuser else "Читатель",
                "Age": profile.age if profile and profile.age else ""
            })
        return self.export_queryset(data, ["ID", "Username", "Email", "Role", "Age"], "Members")
