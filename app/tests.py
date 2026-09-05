from django.test import TestCase
from django.contrib.auth.models import User
from datetime import date
from library.models import Genre, Library, Book, Member, Loan

class ModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.genre = Genre.objects.create(
            name='Фантастика',
            user=self.user
        )
        self.library = Library.objects.create(
            name='Центральная библиотека',
            address='ул. Ленина, 1',
            user=self.user
        )
        self.book = Book.objects.create(
            title='Война и мир',
            genre=self.genre,
            library=self.library
        )
        self.member = Member.objects.create(
            first_name='Иван Петров',
            library=self.library,
            user=self.user
        )

    def test_genre_creation(self):
        self.assertEqual(self.genre.name, 'Фантастика')

    def test_library_creation(self):
        self.assertEqual(self.library.name, 'Центральная библиотека')

    def test_book_creation(self):
        self.assertEqual(self.book.title, 'Война и мир')
        self.assertTrue(self.book.is_available())

    def test_member_creation(self):
        self.assertEqual(self.member.first_name, 'Иван Петров')

    def test_book_availability_after_loan(self):
        loan = Loan.objects.create(
            book=self.book,
            member=self.member,
            loan_date=date.today(),
            user=self.user
        )
        self.book.refresh_from_db()
        self.assertFalse(self.book.is_available())

    def test_loan_creation(self):
        loan = Loan.objects.create(
            book=self.book,
            member=self.member,
            loan_date=date.today(),
            user=self.user
        )
        self.assertEqual(loan.book.title, 'Война и мир')

    def test_book_str_method(self):
        self.assertEqual(str(self.book), 'Война и мир')

    def test_genre_str_method(self):
        self.assertEqual(str(self.genre), 'Фантастика')