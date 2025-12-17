import pyotp
from django.contrib.auth import authenticate, login, logout as django_logout
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from django.db.models import Count
import io
from openpyxl import Workbook
from docx import Document
from rest_framework import permissions, serializers, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from library.models import Library, Book, Genre, Member, Loan, UserProfile, User
from library.serializers import (LibrarySerializer, BookSerializer, GenreSerializer, LoanSerializer, UserSerializer)
from rest_framework.permissions import IsAuthenticated
from library.permissions import IsSuperuserOrReadOnly

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
        if self.action == "login_second_factor":
            return SecondLoginSerializer
        return LoginSerializer

    @action(detail=False, url_path="info", methods=["GET"])
    def info(self, request, *args, **kwargs):
        data = {
            "username": request.user.username if request.user.is_authenticated else "",
            "is_authenticated": request.user.is_authenticated,
            "is_superuser": request.user.is_superuser if request.user.is_authenticated else False,
            "second_factor": request.session.get("second_factor") or False
        }
        return Response(data)

    @action(detail=False, url_path="login", methods=["POST"])
    def login_first_factor(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(
            username=serializer.validated_data["username"],
            password=serializer.validated_data["password"]
        )
        if user is None:
            return Response({"success": False, "error": "Неверные учетные данные"}, status=status.HTTP_401_UNAUTHORIZED)
        
        login(request, user)
        request.session["second_factor"] = False
        request.session.modified = True
        profile, _ = UserProfile.objects.get_or_create(user=user)
        
        if not profile.totp_key:
            profile.totp_key = pyotp.random_base32()
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
        code = serializer.validated_data["key"].strip()
        profile = UserProfile.objects.filter(user=request.user).first()
        
        if not profile or not profile.totp_key:
            return Response({"success": False, "error": "Профиль не найден"})
        
        totp = pyotp.TOTP(profile.totp_key)
        if totp.verify(code, valid_window=1):
            request.session["second_factor"] = True
            request.session.set_expiry(600)
            return Response({
                "success": True,
                "is_authenticated": True,
                "second_factor": True,
                "is_superuser": request.user.is_superuser
            })
        
        return Response({"success": False, "error": "Неверный OTP код"})

    @action(detail=False, url_path="totp-url", methods=["GET"], permission_classes=[IsAuthenticated])
    def totp_url(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        if not profile.totp_key:
            profile.totp_key = pyotp.random_base32()
            profile.save()
        
        totp = pyotp.TOTP(profile.totp_key)
        otp_uri = totp.provisioning_uri(name=request.user.username, issuer_name="MyLibraryApp")
        return Response({"url": otp_uri})

    @action(detail=False, url_path="logout", methods=["POST"], permission_classes=[IsAuthenticated])
    def logout(self, request, *args, **kwargs):
        django_logout(request)
        request.session["second_factor"] = False
        request.session.modified = True
        return Response({"success": True})

class OTPRequiredForDelete(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.session.get("second_factor", False)

class BaseExportMixin:
    def export_queryset(self, queryset, columns, filename_base):
        file_type = self.request.query_params.get('type', 'excel')
        
        if file_type == 'excel':
            workbook = Workbook()
            sheet = workbook.active
            sheet.title = filename_base
            sheet.append(columns)
            
            for data_row in queryset:
                row_data = [data_row.get(col, '') for col in columns]
                sheet.append(row_data)
            
            excel_file = io.BytesIO()
            workbook.save(excel_file)
            excel_file.seek(0)
            file_response = HttpResponse(
                excel_file,
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            file_response['Content-Disposition'] = f'attachment; filename="{filename_base}.xlsx"'
            return file_response
        
        elif file_type == 'word':
            document = Document()
            document.add_heading(filename_base, 0)
            
            for data_row in queryset:
                row_values = [str(data_row.get(col, '')) for col in columns]
                text_line = ' | '.join(row_values)
                document.add_paragraph(text_line)
            
            word_file = io.BytesIO()
            document.save(word_file)
            word_file.seek(0)
            file_response = HttpResponse(
                word_file,
                content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            )
            file_response['Content-Disposition'] = f'attachment; filename="{filename_base}.docx"'
            return file_response
        
        return Response({"error": "Unknown file type"}, status=400)

class GenreViewSet(ModelViewSet, BaseExportMixin):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [IsAuthenticated, OTPRequiredForDelete, IsSuperuserOrReadOnly]

    @action(detail=False, methods=['GET'])
    def stats(self, request):
        queryset = self.get_queryset()
        total = queryset.count()
        top_genre = Genre.objects.annotate(book_count=Count('book')).order_by('-book_count').first()
        top_name = top_genre.name if top_genre else None
        return Response({'count': total, 'top': top_name})

    @action(detail=False, methods=['GET'])
    def export(self, request):
        if not request.user.is_superuser:
            return Response({"error": "Только администраторы могут экспортировать данные"}, status=403)
        
        queryset = self.get_queryset()
        data_list = [{'ID': g.id, 'Name': g.name, 'User': g.user.username if g.user else ''} for g in queryset]
        columns = ['ID', 'Name', 'User']
        return self.export_queryset(data_list, columns, 'Genres')

class LibraryViewSet(ModelViewSet, BaseExportMixin):
    queryset = Library.objects.all().order_by('name')
    serializer_class = LibrarySerializer
    permission_classes = [IsAuthenticated, OTPRequiredForDelete, IsSuperuserOrReadOnly]

    def perform_create(self, serializer):
        if not self.request.user.is_superuser:
            raise PermissionError("Только админы могут добавлять библиотеки")
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        if not self.request.user.is_superuser:
            raise PermissionError("Только админы могут редактировать библиотеки")
        serializer.save()

    def perform_destroy(self, instance):
        if not self.request.user.is_superuser:
            raise PermissionError("Только админы могут удалять библиотеки")
        instance.delete()

    @action(detail=False, methods=['GET'])
    def stats(self, request):
        queryset = self.get_queryset()
        total = queryset.count()
        top_library = Library.objects.annotate(loan_count=Count('book__loan')).order_by('-loan_count').first()
        top_name = top_library.name if top_library else None
        return Response({'count': total, 'top': top_name})

    @action(detail=False, methods=['GET'])
    def export(self, request):
        if not request.user.is_superuser:
            return Response({"error": "Только администраторы могут экспортировать данные"}, status=403)
        
        queryset = self.get_queryset()
        data_list = [{'ID': l.id, 'Name': l.name, 'User': l.user.username if l.user else ''} for l in queryset]
        columns = ['ID', 'Name', 'User']
        return self.export_queryset(data_list, columns, 'Libraries')

class BookViewSet(ModelViewSet, BaseExportMixin):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [IsAuthenticated, OTPRequiredForDelete, IsSuperuserOrReadOnly]

    @action(detail=False, methods=['GET'])
    def stats(self, request):
        queryset = self.get_queryset()
        total = queryset.count()
        most_borrowed = Loan.objects.values('book__id', 'book__title').annotate(borrow_count=Count('book')).order_by('-borrow_count').first()
        
        if most_borrowed:
            most_borrowed_book = {
                'id': most_borrowed['book__id'],
                'title': most_borrowed['book__title'],
                'borrow_count': most_borrowed['borrow_count']
            }
        else:
            most_borrowed_book = None
        
        return Response({'count': total, 'most_borrowed': most_borrowed_book})

    @action(detail=False, methods=['GET'])
    def export(self, request):
        if not request.user.is_superuser:
            return Response({"error": "Только администраторы могут экспортировать книги"}, status=403)
        
        queryset = self.get_queryset()
        data_list = [{
            'ID': b.id,
            'Title': b.title,
            'Genre': b.genre.name if b.genre else '',
            'Library': b.library.name if b.library else '',
            'Status': 'Available' if b.is_available else 'Borrowed'
        } for b in queryset]
        
        columns = ['ID', 'Title', 'Genre', 'Library', 'Status']
        return self.export_queryset(data_list, columns, 'Books')

class LoanViewSet(ModelViewSet, BaseExportMixin):
    queryset = Loan.objects.select_related('book', 'member', 'user')
    serializer_class = LoanSerializer
    permission_classes = [IsAuthenticated, OTPRequiredForDelete]

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_superuser:
            return queryset.filter(member__user=self.request.user)
        return queryset

    def get_permissions(self):
        if self.action == 'return_book':
            return [IsAuthenticated()]
        return super().get_permissions()

    @action(detail=True, methods=['POST'], url_path='return')
    def return_book(self, request, pk=None):
        loan = self.get_object()
        
        if not request.user.is_superuser and loan.member.user != request.user:
            return Response({'detail': 'Только свои книги'}, status=403)
        
        if loan.return_date:
            return Response({'detail': 'Уже возвращена'}, status=400)
        
        from datetime import date
        loan.return_date = date.today()
        loan.save()
        serializer = self.get_serializer(loan)
        return Response({'detail': 'Книга возвращена', 'loan': serializer.data})

    @action(detail=False, methods=['GET'])
    def stats(self, request):
        queryset = self.get_queryset()
        total = queryset.count()
        top_reader = queryset.values('member__id', 'member__first_name').annotate(loan_count=Count('id')).order_by('-loan_count').first()
        
        if top_reader:
            top_reader_data = {
                'name': top_reader['member__first_name'],
                'loan_count': top_reader['loan_count']
            }
        else:
            top_reader_data = {'name': None, 'loan_count': 0}
        
        return Response({'count': total, 'topReader': top_reader_data})

    @action(detail=False, methods=['GET'])
    def export(self, request):
        if not request.user.is_superuser:
            return Response({"error": "Только администраторы могут экспортировать данные"}, status=403)
        
        queryset = self.get_queryset()
        data_list = [{
            'ID': l.id,
            'Book': l.book.title if l.book else '',
            'Member': l.member.first_name if l.member else '',
            'User': l.user.username if l.user else '',
            'Loan Date': l.loan_date,
            'Return Date': l.return_date or 'Not returned'
        } for l in queryset]
        
        columns = ['ID', 'Book', 'Member', 'User', 'Loan Date', 'Return Date']
        return self.export_queryset(data_list, columns, 'Loans')

class MemberViewSet(ModelViewSet, BaseExportMixin):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, OTPRequiredForDelete, IsSuperuserOrReadOnly]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)

    @action(detail=False, methods=['GET'])
    def stats(self, request):
        queryset = self.get_queryset()
        total_users = queryset.count()
        total_admins = queryset.filter(is_superuser=True).count()
        return Response({'count_users': total_users, 'count_admins': total_admins})

    def create(self, request, *args, **kwargs):
        data = request.data
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        age = data.get('age', None)
        is_superuser = data.get('is_superuser', False)
        is_staff = data.get('is_staff', False)
        
        if not username or not email or not password:
            return Response({"error": "Заполните все обязательные поля"}, status=400)
        
        if User.objects.filter(username=username).exists():
            return Response({"error": "Пользователь с таким именем уже существует"}, status=400)
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            is_superuser=is_superuser,
            is_staff=is_staff
        )
        
        UserProfile.objects.get_or_create(user=user, defaults={'age': age})
        Member.objects.get_or_create(user=user, defaults={'first_name': username, 'library': None})
        
        serializer = self.get_serializer(user)
        return Response(serializer.data, status=201)

    def update(self, request, *args, **kwargs):
        user = self.get_object()
        data = request.data
        password = data.get('password', None)
        
        if password:
            user.set_password(password)
        
        user.username = data.get('username', user.username)
        user.email = data.get('email', user.email)
        user.is_superuser = data.get('is_superuser', user.is_superuser)
        user.is_staff = data.get('is_staff', user.is_staff)
        user.save()
        
        age = data.get('age', None)
        profile, _ = UserProfile.objects.get_or_create(user=user)
        
        if age is not None:
            profile.age = age
            profile.save()
        
        member, _ = Member.objects.get_or_create(user=user, defaults={'first_name': user.username})
        member.first_name = user.username
        member.save()
        
        serializer = self.get_serializer(user)
        return Response(serializer.data)

    @action(detail=False, methods=['GET'])
    def export(self, request):
        if not request.user.is_superuser:
            return Response({"error": "Только администраторы могут экспортировать данные"}, status=403)
        
        queryset = self.get_queryset()
        data_list = []
        
        for u in queryset:
            age = ''
            if hasattr(u, 'userprofile'):
                age = u.userprofile.age if u.userprofile.age else ''
            
            data_list.append({
                'ID': u.id,
                'Username': u.username,
                'Email': u.email,
                'Role': 'Администратор' if u.is_superuser else 'Читатель',
                'Age': age
            })
        
        columns = ['ID', 'Username', 'Email', 'Role', 'Age']
        return self.export_queryset(data_list, columns, 'Members')