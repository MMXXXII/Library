from rest_framework import serializers
from library.models import Library, Book, Genre, Member, Loan, UserProfile
from django.contrib.auth.models import User


class BookSerializer(serializers.ModelSerializer):
    genre_name = serializers.StringRelatedField(source='genre', read_only=True)
    library_name = serializers.StringRelatedField(source='library', read_only=True)
    is_available = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = ['id', 'title', 'genre', 'library', 'genre_name', 'library_name', 'is_available']
        read_only_fields = ['user']

    def get_is_available(self, obj):
        return obj.is_available()


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ['id', 'name', 'user']
        read_only_fields = ['user']

    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['user'] = request.user
        return super().create(validated_data)


class LibrarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Library
        fields = ['id', 'name', 'user']
        read_only_fields = ['user']

    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['user'] = request.user
        return super().create(validated_data)


class MemberSerializer(serializers.ModelSerializer):
    library_name = serializers.CharField(source='library.name', read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)
    photo_url = serializers.SerializerMethodField()

    class Meta:
        model = Member
        fields = ['id', 'user', 'user_name', 'library', 'library_name', 'first_name', 'photo', 'photo_url']
        read_only_fields = ['user']

    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['user'] = request.user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        photo = validated_data.pop('photo', None)
        if photo:
            instance.photo = photo
        return super().update(instance, validated_data)


class LoanSerializer(serializers.ModelSerializer):
    book_title = serializers.CharField(source='book.title', read_only=True)
    member_name = serializers.CharField(source='member.first_name', read_only=True)

    class Meta:
        model = Loan
        fields = ['id', 'book', 'member', 'loan_date', 'return_date', 'book_title', 'member_name']
        read_only_fields = ['return_date']

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)


class UserSerializer(serializers.ModelSerializer):
    age = serializers.IntegerField(source='userprofile.age', required=False, allow_null=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'is_superuser', 'age']
        read_only_fields = ['id']

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('userprofile', {})
        age = profile_data.get('age')

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if age is not None:
            profile, _ = UserProfile.objects.get_or_create(user=instance)
            profile.age = age
            profile.save()
        return instance