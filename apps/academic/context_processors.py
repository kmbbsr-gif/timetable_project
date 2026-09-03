# apps/academic/context_processors.py
from apps.schools.models import School
from apps.academic.models import (
    AcademicSession,
    Class,
    Section,
    Room,
    PeriodDefinition,
    Subject,
    ClassSubject,
)
# Adjust these imports according to your exact app names for Teachers and Timetable
try:
    from apps.timetable.models import FixedPeriodEntry
except ImportError:
    FixedPeriodEntry = None

try:
    from apps.teachers.models import Teacher, TeacherSubjectAssignment
except ImportError:
    Teacher = None
    TeacherSubjectAssignment = None


def wizard_setup_status(request):
    """
    Evaluates real database existence for each setup step for the current school.
    """
    school = getattr(request, 'school', None)
    if not school and request.user.is_authenticated:
        # Fallback for school admins linked to a school profile
        school = getattr(request.user, 'school', None)

    if not school:
        return {'wizard_status': {}}

    # 1. School
    has_school = bool(school.id)

    # 2. Session
    has_session = AcademicSession.objects.filter(school=school).exists()

    # 3. Class
    has_class = Class.objects.filter(school=school).exists()

    # 4. Section
    has_section = Section.objects.filter(class_instance__school=school).exists()

    # 5. Room
    has_room = Room.objects.filter(school=school).exists()

    # 6. Period (Normal period definition)
    has_period = PeriodDefinition.objects.filter(school=school).exists()

    # 7. Subject
    has_subject = Subject.objects.filter(school=school).exists()

    # 8. Fixed Exceptions
    if FixedPeriodEntry:
        has_fixed = FixedPeriodEntry.objects.filter(school=school).exists()
    else:
        has_fixed = False

    # 9. Bulk Period (Optional: complete if >= 5 periods exist)
    has_bulk = PeriodDefinition.objects.filter(school=school).count() >= 5

    # 10. Teachers
    if Teacher:
        has_teacher = Teacher.objects.filter(school=school).exists()
    else:
        has_teacher = False

    # 11. Class-Subject Mapping
    has_class_sub = ClassSubject.objects.filter(class_instance__school=school).exists()

    # 12. Teacher Assignment
    if TeacherSubjectAssignment:
        has_assignment = TeacherSubjectAssignment.objects.filter(teacher__school=school).exists()
    else:
        has_assignment = False

    return {
        'wizard_status': {
            1: has_school,
            2: has_session,
            3: has_class,
            4: has_section,
            5: has_room,
            6: has_period,
            7: has_subject,
            8: has_fixed,
            9: has_bulk,
            10: has_teacher,
            11: has_class_sub,
            12: has_assignment,
        }
    }