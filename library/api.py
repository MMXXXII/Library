import io
from datetime import date
from django.contrib.auth import authenticate, login, logout as django_logout
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from openpyxl import Workbook
from rest_framework import permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework.permissions import IsAuthenticated
from library.models import Library, Book, Genre, Member, Loan, UserProfile, User
from library.serializers import LibrarySerializer, BookSerializer, GenreSerializer, LoanSerializer, MemberSerializer
from rest_framework import serializers


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()


class UserProfileViewSet(GenericViewSet):
    permission_classes = [permissions.AllowAny]
    serializer_class = LoginSerializer

    # @method_decorator(ensure_csrf_cookie)
    # @action(detail=False, url_path="csrf", methods=["GET"])
    # def csrf(self, request, *args, **kwargs):
    #     return Response({"ok": True})

    @action(detail=False, url_path="info", methods=["GET"])
    def info(self, request, *args, **kwargs):
        user = request.user
        result = {
            "id": user.id,
            "username": "",
            "is_authenticated": user.is_authenticated,
            "is_superuser": False
        }
        if user.is_authenticated:
            result["username"] = user.username
            result["is_superuser"] = user.is_superuser
            result["email"] = user.email  
        return Response(result)

    @action(detail=False, url_path="login", methods=["POST"])
    def login_first_factor(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data["username"]
        password = serializer.validated_data["password"]
        user = authenticate(username=username, password=password)
        if user is None or not user.is_authenticated:
            return Response({"success": False, "is_authenticated": False})
        login(request, user)
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


def export_data(data, columns, filename):
    wb = Workbook()
    ws = wb.active
    ws.title = filename
    ws.append(columns)
    for row in data:
        row_list = []
        for col in columns:
            row_list.append(row.get(col, ""))
        ws.append(row_list)
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    content = buffer.getvalue()
    response = HttpResponse(content, content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = 'attachment; filename="' + filename + '.xlsx"'
    return response


class GenreViewSet(ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["GET"])
    def stats(self, request):
        genres = Genre.objects.all()
        top = None
        max_books = 0
        for g in genres:
            books_count = Book.objects.filter(genre=g).count()
            if books_count > max_books:
                max_books = books_count
                top = g
        return Response({
            "count": genres.count(),
            "top": top.name if top else None
        })

    @action(detail=False, methods=["GET"])
    def export(self, request):
        data = []
        for g in self.get_queryset():
            user_name = ""
            if g.user:
                user_name = g.user.username
            data.append({"ID": g.id, "Name": g.name, "User": user_name})
        return export_data(data, ["ID", "Name", "User"], "Genres")


class LibraryViewSet(ModelViewSet):
    queryset = Library.objects.all()
    serializer_class = LibrarySerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["GET"])
    def stats(self, request):
        libraries = Library.objects.all()
        books = Book.objects.all()
        top = None
        max_loans = 0

        for lib in libraries:
            loans_count = 0
            for book in books:
                if book.library == lib:
                    for loan in Loan.objects.filter(book=book):
                        loans_count += 1
            if loans_count > max_loans:
                max_loans = loans_count
                top = lib

        return Response({
            "count": libraries.count(),
            "top": top.name if top else None
        })

    @action(detail=False, methods=["GET"])
    def export(self, request):
        data = []
        for l in self.get_queryset():
            user_name = ""
            if l.user:
                user_name = l.user.username
            data.append({"ID": l.id, "Name": l.name, "User": user_name})
        return export_data(data, ["ID", "Name", "User"], "Libraries")


class BookViewSet(ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["GET"])
    def stats(self, request):
        books = Book.objects.all()
        top = None
        max_loans = 0
        for b in books:
            loans = Loan.objects.filter(book=b).count()
            if loans > max_loans:
                max_loans = loans
                top = b
        return Response({
            "count": books.count(),
            "most_borrowed": {
                "id": top.id,
                "title": top.title,
                "count": max_loans
            } if top else None
        })

    @action(detail=False, methods=["GET"])
    def export(self, request):
        data = []
        for b in self.get_queryset():
            genre_name = ""
            if b.genre:
                genre_name = b.genre.name
            library_name = ""
            if b.library:
                library_name = b.library.name
            if b.is_available():
                status = "Available"
            else:
                status = "Borrowed"
            data.append({
                "ID": b.id,
                "Title": b.title,
                "Genre": genre_name,
                "Library": library_name,
                "Status": status
            })
        return export_data(data, ["ID", "Title", "Genre", "Library", "Status"], "Books")


class LoanViewSet(ModelViewSet):
    queryset = Loan.objects.all()
    serializer_class = LoanSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        loans = Loan.objects.all()
        if user.is_superuser:
            return loans

        my_loans = []
        for loan in loans:
            if loan.member and loan.member.user == user:
                my_loans.append(loan)
        return my_loans

    @action(detail=True, methods=["POST"], url_path="return")
    def return_book(self, request, pk=None):
        loan = self.get_object()
        loan.return_date = date.today()
        loan.save()
        return Response(self.get_serializer(loan).data)

    @action(detail=False, methods=["GET"])
    def stats(self, request):
        loans = self.get_queryset()
        top_member = None
        max_loans = 0
        members = Member.objects.all()
        for m in members:
            cnt = loans.filter(member=m).count()
            if cnt > max_loans:
                max_loans = cnt
                top_member = m
        return Response({
            "count": loans.count(),
            "topReader": {
                "name": top_member.first_name,
                "count": max_loans
            } if top_member else None
        })

    @action(detail=False, methods=["GET"])
    def export(self, request):
        data = []
        for l in self.get_queryset():
            book_title = ""
            if l.book:
                book_title = l.book.title
            member_name = ""
            if l.member:
                member_name = l.member.first_name
            user_name = ""
            if l.user:
                user_name = l.user.username
            data.append({
                "ID": l.id,
                "Book": book_title,
                "Member": member_name,
                "User": user_name,
                "Loan Date": l.loan_date,
                "Return Date": l.return_date
            })
        return export_data(data, ["ID", "Book", "Member", "User", "Loan Date", "Return Date"], "Loans")


class MemberViewSet(ModelViewSet):
    queryset = Member.objects.all()
    serializer_class = MemberSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["GET"])
    def stats(self, request):
        qs = self.get_queryset()
        count_users = qs.count()
        count_admins = 0
        for member in qs:
            if member.user and member.user.is_superuser:
                count_admins += 1
        return Response({"count_users": count_users, "count_admins": count_admins})

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        age = data.pop("age", None)
        library_id = data.pop("library", None)
        password = data.pop("password", None)
        username = data.get("username")
        user, created = User.objects.get_or_create(username=username, defaults={
            "email": data.get("email", ""),
            "is_superuser": data.get("is_superuser", False),
            "is_staff": data.get("is_staff", False),
        })
        user.set_password(password)
        user.save()
        library = None
        if library_id:
            library = Library.objects.filter(pk=library_id).first()
        if library is None:
            library = Library.objects.order_by("id").first()
        member, created_m = Member.objects.get_or_create(user=user, defaults={"library": library, "first_name": username})
        if not created_m:
            member.library = library
            member.first_name = username
            member.save()
        if age is not None:
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.age = age
            profile.save()
        return Response(self.get_serializer(member).data)

    def update(self, request, *args, **kwargs):
        member = self.get_object()
        data = request.data.copy()
        user = member.user
        if user is None:
            user = User.objects.create_user(
                username=data.get("username", ""),
                email=data.get("email", ""),
                password=data.get("password")
            )
            member.user = user
        if "username" in data:
            user.username = data["username"]
            member.first_name = data["username"]
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
        if "library" in data and data["library"]:
            lib = Library.objects.filter(pk=data["library"]).first()
            if lib:
                member.library = lib
        member.save()
        return Response(self.get_serializer(member).data)

    @action(detail=False, methods=["GET"])
    def export(self, request):
        data = []
        for m in self.get_queryset():
            user = m.user
            username = ""
            email = ""
            role = "Читатель"
            age_val = ""
            if user:
                username = user.username
                email = user.email
                if user.is_superuser:
                    role = "Администратор"
                profile = UserProfile.objects.filter(user=user).first()
                if profile and profile.age is not None:
                    age_val = profile.age
            data.append({
                "ID": m.id,
                "Username": username,
                "Email": email,
                "Role": role,
                "Age": age_val
            })
        return export_data(data, ["ID", "Username", "Email", "Role", "Age"], "Members")