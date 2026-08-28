from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

class Command(BaseCommand):
    help = 'Create groups and assign permissions'

    def handle(self, *args, **kwargs):
        # Define groups
        groups = ['Admin', 'Coordinator', 'Teacher', 'Student']
        for g in groups:
            group, created = Group.objects.get_or_create(name=g)
            if created:
                self.stdout.write(f"Created group: {g}")
            else:
                self.stdout.write(f"Group {g} already exists")

        # Assign permissions (optional – we'll use group‑based view restrictions)
        self.stdout.write("Groups created. Now use @group_required decorator in views.")