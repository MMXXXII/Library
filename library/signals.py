from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User

from .models import Member, Library, UserProfile


@receiver(post_save, sender=User)
def create_member_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)
        library = Library.objects.first()
        
        if library:
            Member.objects.get_or_create(
                user=instance,
                defaults={
                    'first_name': instance.username,
                    'library': library
                }
            )
