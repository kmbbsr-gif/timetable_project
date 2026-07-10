from django.core.management.base import BaseCommand
from apps.teachers.models import Teacher
from apps.teachers.utils import get_average_load

class Command(BaseCommand):
    help = 'Update all teachers max_weekly_load to the current average load'

    def handle(self, *args, **options):
        avg = get_average_load()
        if avg == 0:
            self.stdout.write("No data to calculate average.")
            return
        updated = Teacher.objects.filter(is_active=True).update(max_weekly_load=avg)
        self.stdout.write(f"Updated {updated} teachers to max_load = {avg}")