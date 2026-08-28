import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

django.setup()

from django.db import connection

MIGRATIONS_DIR = os.path.join('apps', 'teachers', 'migrations')

print("=" * 60)
print("STEP 1: Checking migration files...")
print("=" * 60)

migrations = sorted([f for f in os.listdir(MIGRATIONS_DIR) if f.endswith('.py') and f != '__init__.py'])
for m in migrations:
    print("  " + m)

print("")
print("=" * 60)
print("STEP 2: Cleaning up broken migrations after 0005...")
print("=" * 60)

to_delete = [m for m in migrations if m > '0005_']
for m in to_delete:
    path = os.path.join(MIGRATIONS_DIR, m)
    os.remove(path)
    print("  DELETED: " + m)

if not to_delete:
    print("  No broken migrations found after 0005.")

cache_dir = os.path.join(MIGRATIONS_DIR, '__pycache__')
if os.path.exists(cache_dir):
    for f in os.listdir(cache_dir):
        if f.startswith('0006') or f.startswith('0007') or f.startswith('0008'):
            os.remove(os.path.join(cache_dir, f))
            print("  DELETED pycache: " + f)

print("")
print("=" * 60)
print("STEP 3: Fixing django_migrations table...")
print("=" * 60)

with connection.cursor() as cursor:
    cursor.execute("SELECT name FROM django_migrations WHERE app = 'teachers'")
    db_migs = [row[0] for row in cursor.fetchall()]
    print("  Migrations in DB:")
    for m in db_migs:
        print("    " + m)

    bad = [m for m in db_migs if m > '0005_teachersubjectassignment_combined_group_name_and_more']
    for m in bad:
        cursor.execute(
            "DELETE FROM django_migrations WHERE app = 'teachers' AND name = %s",
            [m]
        )
        print("  DELETED from DB: " + m)

    if not bad:
        print("  No broken entries in django_migrations.")

print("")
print("=" * 60)
print("STEP 4: Verifying model...")
print("=" * 60)

try:
    from apps.teachers.models import TeacherSubjectAssignment
    fields = [f.name for f in TeacherSubjectAssignment._meta.get_fields()]
    required = ['teacher', 'class_subject', 'weekly_periods', 'is_combined', 
                'combined_group_name', 'target_sections']
    missing = [f for f in required if f not in fields]

    if missing:
        print("  ERROR: Missing fields: " + str(missing))
        print("  Fix your models.py before continuing.")
        sys.exit(1)
    else:
        print("  OK: All required fields present.")
        print("  Fields: " + str(fields))
except Exception as e:
    print("  ERROR loading model: " + str(e))
    sys.exit(1)

print("")
print("=" * 60)
print("STEP 5: Creating new migration...")
print("=" * 60)

from django.core.management import call_command
call_command('makemigrations', 'teachers', verbosity=2)

print("")
print("=" * 60)
print("STEP 6: Applying migration...")
print("=" * 60)

try:
    call_command('migrate', 'teachers', verbosity=2)
    print("")
    print("=" * 60)
    print("SUCCESS! Now run: python manage.py runserver")
    print("=" * 60)
except Exception as e:
    print("\nMIGRATE FAILED: " + str(e))
    print("\nIf the error is 'duplicate column name', run:")
    print("  python manage.py migrate --fake teachers")