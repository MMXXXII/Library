from django.db import models
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db.models.signals import post_save
import pyotp


# Create your models here.
class Genre(models.Model):
    name = models.TextField("Жанр")
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Пользователь")
    
    class Meta:
        verbose_name = "Жанр"
        verbose_name_plural = "Жанры"

    def __str__(self) -> str:
        return self.name

class Library(models.Model):
    name = models.TextField("Название библиотеки")
    address = models.TextField("Адрес")
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Пользователь")

    class Meta:
        verbose_name = "Библиотека"
        verbose_name_plural = "Библиотеки"

    def __str__(self) -> str:
        return self.name


class Book(models.Model):
    title = models.TextField("Название книги")
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE, verbose_name="Жанр")
    library = models.ForeignKey(Library, on_delete=models.CASCADE, verbose_name="Библиотека")

    class Meta:
        verbose_name = "Книга"
        verbose_name_plural = "Книги"

    def __str__(self) -> str:
        return self.title
    
    def is_available(self):
        return not Loan.objects.filter(book=self, return_date__isnull=True).exists()


class Member(models.Model):
    first_name = models.TextField("Имя")
    library = models.ForeignKey(Library, on_delete=models.CASCADE, verbose_name="Библиотека")
    photo = models.ImageField("Фото", upload_to="members", null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Пользователь")

    class Meta:
        verbose_name = "Читатель"
        verbose_name_plural = "Читатели"

    def __str__(self) -> str:
        return self.first_name


class Loan(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, verbose_name="Книга")
    member = models.ForeignKey(Member, on_delete=models.CASCADE, verbose_name="Читатель")
    loan_date = models.DateField("Дата выдачи")
    return_date = models.DateField(null=True, blank=True, verbose_name="Дата возврата")
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Пользователь")

    class Meta:
        verbose_name = "Выдача книги"
        verbose_name_plural = "Выдачи книг"

    def __str__(self) -> str:
        return f"{self.book} → {self.member}"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    age = models.IntegerField(null=True, blank=True, verbose_name='Возраст')
    totp_key = models.CharField(max_length=128, null=True, blank=True, default=pyotp.random_hex)
    
    class Meta:
        verbose_name = 'Профиль пользователя'
        verbose_name_plural = 'Профили пользователей'

    def __str__(self):
        return f'Профиль {self.user.username}'

    def save(self, *args, **kwargs):
        if self.id is None: 
            self.totp_key = pyotp.random_base32()
        super().save(*args, **kwargs)


    @receiver(post_save, sender=User)
    def create_user_profile(sender, instance, created, **kwargs):
        if created:
            UserProfile.objects.create(user=instance)