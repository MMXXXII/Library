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
        result = {"id": user.id, "username": "", "is_authenticated": user.is_authenticated, "is_superuser": False}
        if user.is_authenticated:
            result["username"] = user.username
            result["is_superuser"] = user.is_superuser
        return Response(result)

    @action(detail=False, url_path="login", methods=["POST"])
    def login_first_factor(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(username=serializer.validated_data["username"], password=serializer.validated_data["password"])
        if user is None:
            return Response({"success": False, "is_authenticated": False})
        login(request, user)
        UserProfile.objects.get_or_create(user=user)
        return Response({"success": True, "is_authenticated": True, "username": user.username, "email": user.email, "is_superuser": user.is_superuser})

    @action(detail=False, url_path="logout", methods=["POST"], permission_classes=[IsAuthenticated])
    def logout(self, request, *args, **kwargs):
        django_logout(request)
        return Response({"success": True})


def export_data(data, columns, filename):
    wb = Workbook()
    ws = wb.active
    ws.title = filename
    ws.append(columns)
    for row in data:
        ws.append([row.get(col, "") for col in columns])
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = f'attachment; filename="{filename}.xlsx"'
    return response


class GenreViewSet(ModelViewSet):
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
        return export_data(data, ["ID", "Name", "User"], "Genres")


class LibraryViewSet(ModelViewSet):
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
        return export_data(data, ["ID", "Name", "User"], "Libraries")


class BookViewSet(ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["GET"])
    def stats(self, request):
        most = Loan.objects.values("book__id", "book__title").annotate(c=Count("book")).order_by("-c").first()
        return Response({"count": self.get_queryset().count(), "most_borrowed": most})

    @action(detail=False, methods=["GET"])
    def export(self, request):
        data = []
        for b in self.get_queryset():
            data.append({"ID": b.id, "Title": b.title, "Genre": b.genre.name if b.genre else "", 
                        "Library": b.library.name if b.library else "", "Status": "Borrowed" if not b.is_available else "Available"})
        return export_data(data, ["ID", "Title", "Genre", "Library", "Status"], "Books")


class LoanViewSet(ModelViewSet):
    queryset = Loan.objects.all()
    serializer_class = LoanSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Loan.objects.all()
        if not self.request.user.is_superuser:
            qs = qs.filter(member__user=self.request.user)
        return qs

    @action(detail=True, methods=["POST"], url_path="return")
    def return_book(self, request, pk=None):
        loan = self.get_object()
        loan.return_date = date.today()
        loan.save()
        return Response(self.get_serializer(loan).data)

    @action(detail=False, methods=["GET"])
    def stats(self, request):
        top = self.get_queryset().values("member__first_name").annotate(c=Count("id")).order_by("-c").first()
        top_reader = {"name": top["member__first_name"]} if top else None
        return Response({"count": self.get_queryset().count(), "topReader": top_reader})

    @action(detail=False, methods=["GET"])
    def export(self, request):
        data = []
        for l in self.get_queryset():
            data.append({"ID": l.id, "Book": l.book.title if l.book else "", "Member": l.member.first_name if l.member else "",
                        "User": l.user.username if l.user else "", "Loan Date": l.loan_date, "Return Date": l.return_date})
        return export_data(data, ["ID", "Book", "Member", "User", "Loan Date", "Return Date"], "Loans")


class MemberViewSet(ModelViewSet):
    queryset = Member.objects.all()
    serializer_class = MemberSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["GET"])
    def stats(self, request):
        qs = self.get_queryset()
        return Response({"count_users": qs.count(), "count_admins": qs.filter(user__is_superuser=True).count()})

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        age = data.pop("age", None)
        library_id = data.pop("library", None)
        password = data.pop("password", None)
        user, created = User.objects.get_or_create(username=data.get("username"), 
                                                   defaults={"email": data.get("email", ""), "is_superuser": data.get("is_superuser", False)})
        user.set_password(password)
        user.save()
        library = Library.objects.filter(pk=library_id).first() if library_id else Library.objects.order_by("id").first()
        member, created_m = Member.objects.get_or_create(user=user, defaults={"library": library, "first_name": data.get("username")})
        if not created_m:
            member.library = library
            member.first_name = data.get("username")
            member.save()
        if age:
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.age = age
            profile.save()
        return Response(self.get_serializer(member).data)

    def update(self, request, *args, **kwargs):
        member = self.get_object()
        user = member.user
        data = request.data.copy()
        if not user:
            user = User(username=data.get("username", ""), email=data.get("email", ""))
            user.set_unusable_password()
            user.save()
            member.user = user
            member.save()
        user.username = data.get("username", user.username)
        user.email = data.get("email", user.email)
        if "password" in data:
            user.set_password(data["password"])
        user.is_superuser = data.get("is_superuser", user.is_superuser)
        user.save()
        if "age" in data:
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.age = data["age"]
            profile.save()
        if "library" in data and data["library"]:
            lib = Library.objects.filter(pk=data["library"]).first()
            if lib:
                member.library = lib
                member.save()
        if "username" in data:
            member.first_name = data["username"]
            member.save()
        return Response(self.get_serializer(member).data)

    @action(detail=False, methods=["GET"])
    def export(self, request):
        data = []
        for m in self.get_queryset():
            user = m.user
            profile = UserProfile.objects.filter(user=user).first() if user else None
            data.append({"ID": m.id, "Username": user.username if user else "", "Email": user.email if user else "",
                        "Role": "Администратор" if user and user.is_superuser else "Читатель",
                        "Age": profile.age if profile and profile.age else ""})
        return export_data(data, ["ID", "Username", "Email", "Role", "Age"], "Members")