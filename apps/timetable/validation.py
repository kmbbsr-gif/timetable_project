from .models import TimetableEntry
from collections import defaultdict

def validate_timetable(school_id=None, session_id=None):
    entries = TimetableEntry.objects.filter(school_id=school_id, session_id=session_id)
    teacher_overlaps = defaultdict(list)
    class_overlaps = defaultdict(list)
    teacher_load = defaultdict(int)

    for e in entries:
        key = (e.teacher_id, e.day_of_week, e.period_number)
        teacher_overlaps[key].append(e)
        key2 = (e.class_instance_id, e.section_id, e.day_of_week, e.period_number)
        class_overlaps[key2].append(e)
        teacher_load[e.teacher_id] += 1

    conflicts = []
    for key, entries_list in teacher_overlaps.items():
        if len(entries_list) > 1:
            conflicts.append({
                'type': 'Teacher Overlap',
                'teacher': entries_list[0].teacher.name,
                'day': entries_list[0].day_of_week,
                'period': entries_list[0].period_number,
                'entries': entries_list
            })
    for key, entries_list in class_overlaps.items():
        if len(entries_list) > 1:
            conflicts.append({
                'type': 'Class Overlap',
                'class': entries_list[0].class_instance.name,
                'section': entries_list[0].section.name,
                'day': entries_list[0].day_of_week,
                'period': entries_list[0].period_number,
                'entries': entries_list
            })
    return conflicts