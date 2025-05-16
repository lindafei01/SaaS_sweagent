
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Sets the password for the admin user'

    def handle(self, *args, **options):
        try:
            admin = User.objects.get(username='admin')
        except User.DoesNotExist:
            admin = User.objects.create_superuser('admin', 'admin@example.com', 'admin')
            self.stdout.write(self.style.SUCCESS('Admin user created'))
        else:
            admin.set_password('admin')
            admin.save()
            self.stdout.write(self.style.SUCCESS('Admin password set'))