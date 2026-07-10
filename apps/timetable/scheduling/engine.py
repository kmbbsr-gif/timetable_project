from collections import defaultdict
from django.db import transaction
from apps.academic.models import Section, PeriodDefinition, AcademicSession
from apps.teachers.models import Teacher, TeacherSubjectAssignment
from apps.timetable.models import TimetableEntry
from .genetic import GeneticOptimizer

class TimetableSolver:
    def __init__(self, school_id, session_id):
        self.school_id = school_id
        self.session_id = session_id
        self.variables = []   # ensure it's a list
        self._load_data()

    def _load_data(self):
        self.session = AcademicSession.objects.get(id=self.session_id, school_id=self.school_id)
        self.periods = PeriodDefinition.objects.filter(school_id=self.school_id).order_by('period_number')
        self.period_numbers = list(self.periods.values_list('period_number', flat=True))

        # Build variables from TeacherSubjectAssignment
        assignments = TeacherSubjectAssignment.objects.filter(
            teacher__school_id=self.school_id
        ).select_related('teacher', 'class_subject__class_instance', 'class_subject__subject')
        print(f"DEBUG: Found {assignments.count()} assignments for school {self.school_id}")

        for a in assignments:
            print(f"  - {a.teacher.name} -> {a.class_subject}")

        for assignment in assignments:
            class_subject = assignment.class_subject
            class_obj = class_subject.class_instance
            sections = Section.objects.filter(class_instance=class_obj)
            print(f"DEBUG: {assignment.teacher.name} -> {class_subject}, sections: {sections.count()}, periods: {assignment.weekly_periods}")
            for section in sections:
                for _ in range(assignment.weekly_periods):
                    self.variables.append({
                        'teacher_id': assignment.teacher_id,
                        'class_id': class_obj.id,
                        'section_id': section.id,
                        'subject_id': class_subject.subject_id,
                        'teacher': assignment.teacher,
                        'class_subject': class_subject,
                        'section': section,
                    })

        # Teacher availability (moved OUTSIDE the loop)
        self.teacher_availability = defaultdict(set)
        teachers = Teacher.objects.filter(school_id=self.school_id)
        for teacher in teachers:
            for day in range(0, 6):
                for period in self.period_numbers:
                    if day not in teacher.unavailable_days and period not in teacher.unavailable_periods:
                        self.teacher_availability[teacher.id].add((day, period))

        # Class working days (moved OUTSIDE the loop)
        self.class_working_days = defaultdict(list)
        sections = Section.objects.filter(class_instance__school_id=self.school_id)
        for section in sections:
            if section.working_days:
                self.class_working_days[section.class_instance.id] = section.working_days
            else:
                self.class_working_days[section.class_instance.id] = list(range(0, 6))

        print(f"Variables: {len(self.variables)} items, type: {type(self.variables)}")

    def _get_domain(self, var):
        teacher_id = var['teacher_id']
        class_id = var['class_id']
        domain = []
        for day in self.class_working_days[class_id]:
            for period in self.period_numbers:
                if (day, period) in self.teacher_availability.get(teacher_id, set()):
                    domain.append((day, period))
        return domain

    def solve(self, use_genetic=True):
        solution = self._backtrack()
        if not solution:
            return None
        if use_genetic:
            ga = GeneticOptimizer(self.variables)   # <-- pass the list
            solution = ga.improve(solution)
        return self._save_solution(solution)

    def _backtrack(self):
        assignment = {}
        variables = list(range(len(self.variables)))
        group_days = {}  # key: (teacher_id, class_id, section_id, subject_id) -> set of days used

        def backtrack(idx):
            if idx == len(variables):
                return True
            var_idx = variables[idx]
            var = self.variables[var_idx]
            group_key = (var['teacher_id'], var['class_id'], var['section_id'], var['subject_id'])
            domain = self._get_domain(var)

            # 🔁 Enforce 1 period per day for this group
            if group_key in group_days:
                used_days = group_days[group_key]
                domain = [(d, p) for d, p in domain if d not in used_days]

            # Try each slot in the domain
            for day, period in domain:
                # Check conflicts with already assigned variables
                conflict = False
                for j in range(idx):
                    prev_idx = variables[j]
                    prev_day, prev_period = assignment[prev_idx]
                    prev_var = self.variables[prev_idx]
                    # Teacher overlap
                    if prev_var['teacher_id'] == var['teacher_id'] and prev_day == day and prev_period == period:
                        conflict = True
                        break
                    # Class-section overlap
                    if prev_var['class_id'] == var['class_id'] and prev_var['section_id'] == var['section_id'] and prev_day == day and prev_period == period:
                        conflict = True
                        break
                if conflict:
                    continue

                # Assign
                assignment[var_idx] = (day, period)
                if group_key not in group_days:
                    group_days[group_key] = set()
                group_days[group_key].add(day)

                if backtrack(idx + 1):
                    return True

                # Backtrack
                del assignment[var_idx]
                group_days[group_key].remove(day)
                if not group_days[group_key]:
                    del group_days[group_key]

            return False

        if backtrack(0):
            return [assignment[i] for i in range(len(variables))]
        return None

    def _save_solution(self, solution):
        entries = []
        for idx, (day, period) in enumerate(solution):
            var = self.variables[idx]
            entries.append(TimetableEntry(
                school_id=self.school_id,
                session_id=self.session_id,
                class_instance_id=var['class_id'],
                section_id=var['section_id'],
                teacher_id=var['teacher_id'],
                subject_id=var['subject_id'],
                day_of_week=day,
                period_number=period,
                is_double=False,
                is_practical=False,
                room_id=None,
            ))
        TimetableEntry.objects.filter(school_id=self.school_id, session_id=self.session_id).delete()
        with transaction.atomic():
            TimetableEntry.objects.bulk_create(entries)
        return len(entries)