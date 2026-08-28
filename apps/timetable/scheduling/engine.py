import uuid
import random
import time
import logging
from collections import defaultdict
from typing import List, Dict, Tuple, Set, Optional, Any
from dataclasses import dataclass, field
from django.db import transaction

from apps.academic.models import Section, PeriodDefinition, AcademicSession, Room
from apps.teachers.models import Teacher, TeacherSubjectAssignment
from apps.timetable.models import TimetableEntry

# Flexible GeneticOptimizer import — works in both scheduling/ and timetable/ locations
try:
    from apps.timetable.scheduling.genetic import GeneticOptimizer
except ImportError:
    try:
        from apps.timetable.genetic import GeneticOptimizer
    except ImportError:
        GeneticOptimizer = None

logger = logging.getLogger(__name__)


@dataclass
class Task:
    idx: int
    teacher_id: int
    class_id: int
    section_id: int
    subject_id: int
    teacher: Any
    class_subject: Any
    section: Any
    total_weekly_periods: int
    is_class_teacher_slot: bool
    is_combined: bool = False
    is_double: bool = False
    is_practical: bool = False
    combined_group: Optional[str] = None
    target_sections: Optional[List[Any]] = None


@dataclass
class CombinedGroup:
    teacher_id: int
    subject_id: int
    teacher: Any
    subject: Any
    target_sections: List[Any]
    group_name: str
    weekly_periods: int
    assignments: List[Any] = field(default_factory=list)


class ConstraintEngine:
    def __init__(self, solver: "TimetableSolver"):
        self.solver = solver

    def teacher_conflict(self, t1: Task, v1: Tuple[int, int], t2: Task, v2: Tuple[int, int]) -> bool:
        return t1.teacher_id == t2.teacher_id and v1 == v2

    def section_conflict(self, t1: Task, v1: Tuple[int, int], t2: Task, v2: Tuple[int, int]) -> bool:
        if v1 != v2:
            return False
        t1_sections = {s.id for s in (t1.target_sections or [])} or {t1.section_id}
        t2_sections = {s.id for s in (t2.target_sections or [])} or {t2.section_id}
        return bool(t1_sections & t2_sections)

    def hard_conflict(self, t1: Task, v1: Tuple[int, int], t2: Task, v2: Tuple[int, int]) -> bool:
        return self.teacher_conflict(t1, v1, t2, v2) or self.section_conflict(t1, v1, t2, v2)

    def exceeds_daily_load(self, teacher_id: int, day: int, daily_load: Dict[int, Dict[int, int]]) -> bool:
        return daily_load[teacher_id][day] >= self.solver.teacher_max_daily_load_dict.get(teacher_id, 8)

    def exceeds_weekly_load(self, teacher_id: int, total_load: Dict[int, int]) -> bool:
        return total_load[teacher_id] >= self.solver.teacher_max_weekly_load_dict.get(teacher_id, 40)

    def get_affected_indices(self, task: Task, unassigned: Set[int]) -> List[int]:
        affected = []
        task_sections = {s.id for s in (task.target_sections or [])} or {task.section_id}
        for other_idx in unassigned:
            if other_idx == task.idx:
                continue
            other = self.solver.tasks[other_idx]
            if task.teacher_id == other.teacher_id:
                affected.append(other_idx)
                continue
            other_sections = {s.id for s in (other.target_sections or [])} or {other.section_id}
            if task_sections & other_sections:
                affected.append(other_idx)
        return affected


class DomainStore:
    def __init__(self, tasks: List[Task], initial_domains: Dict[int, List[Tuple[int, int]]]):
        self.tasks = tasks
        self.domains: Dict[int, List[Tuple[int, int]]] = {
            t.idx: list(initial_domains[t.idx]) for t in tasks
        }
        self._history: List[Dict[int, List[Tuple[int, int]]]] = []

    def push(self):
        self._history.append({})

    def pop(self):
        if not self._history:
            return
        removed = self._history.pop()
        for idx, vals in removed.items():
            self.domains[idx].extend(vals)
            self.domains[idx] = sorted(set(self.domains[idx]), key=lambda x: (x[0], x[1]))

    def prune(self, task_idx: int, value: Tuple[int, int], affected: List[int], engine: ConstraintEngine) -> bool:
        if not self._history:
            self.push()
        state = self._history[-1]
        this_task = self.tasks[task_idx]
        for other_idx in affected:
            other_task = self.tasks[other_idx]
            to_remove = [v for v in self.domains[other_idx]
                         if engine.hard_conflict(this_task, value, other_task, v)]
            if to_remove:
                if other_idx not in state:
                    state[other_idx] = []
                for v in to_remove:
                    self.domains[other_idx].remove(v)
                    state[other_idx].append(v)
                if not self.domains[other_idx]:
                    return False
        return True

    def size(self, task_idx: int) -> int:
        return len(self.domains[task_idx])

    def values(self, task_idx: int) -> List[Tuple[int, int]]:
        return self.domains[task_idx]


class LocalSearchOptimizer:
    def __init__(self, solver: "TimetableSolver", max_iter: int = 20000):
        self.solver = solver
        self.engine = ConstraintEngine(solver)
        self.max_iter = max_iter
        self.initial_domains = solver.initial_domains

    def optimize(self, partial: Dict[int, Tuple[int, int]]) -> Optional[Dict[int, Tuple[int, int]]]:
        solution = dict(partial)
        unassigned = set(range(len(self.solver.tasks))) - set(solution.keys())
        for idx in sorted(unassigned, key=lambda i: len(self.initial_domains[i])):
            best_val, best_score = None, float("inf")
            for val in self.initial_domains[idx]:
                sc = self._conflict_score(idx, val, solution)
                if sc < best_score:
                    best_score, best_val = sc, val
            if best_val is None:
                return None
            solution[idx] = best_val
        for _ in range(self.max_iter):
            conflicted = self._conflicted_indices(solution)
            if not conflicted:
                return solution
            idx = random.choice(conflicted)
            best_val, best_score = None, float("inf")
            for val in self.initial_domains[idx]:
                sc = self._conflict_score(idx, val, solution)
                if sc < best_score:
                    best_score, best_val = sc, val
            if best_val is not None:
                solution[idx] = best_val
        return solution if not self._conflicted_indices(solution) else None

    def _conflict_score(self, idx: int, val: Tuple[int, int], solution: Dict[int, Tuple[int, int]]) -> int:
        task = self.solver.tasks[idx]
        score = 0
        for other_idx, other_val in solution.items():
            if other_idx == idx:
                continue
            other = self.solver.tasks[other_idx]
            if self.engine.hard_conflict(task, val, other, other_val):
                score += 1
        return score

    def _conflicted_indices(self, solution: Dict[int, Tuple[int, int]]) -> List[int]:
        bad = []
        items = list(solution.items())
        for i, (a_idx, a_val) in enumerate(items):
            a_task = self.solver.tasks[a_idx]
            for b_idx, b_val in items[i + 1:]:
                b_task = self.solver.tasks[b_idx]
                if self.engine.hard_conflict(a_task, a_val, b_task, b_val):
                    bad.append(a_idx)
                    break
        return bad


class TimetableSolver:
    def __init__(self, school_id, session_id):
        self.school_id = school_id
        self.session_id = session_id
        self.variables: List[Dict] = []
        self.combined_variables: List[Dict] = []
        self.tasks: List[Task] = []
        self.combined_groups: List[CombinedGroup] = []
        self.initial_domains: Dict[int, List[Tuple[int, int]]] = {}
        self._load_data()
        self._build_domains()
        self._build_legacy_lists()
        self.constraints = ConstraintEngine(self)
        self.local_search = LocalSearchOptimizer(self)

    def _load_data(self):
        self.session = AcademicSession.objects.get(id=self.session_id, school_id=self.school_id)
        self.periods = PeriodDefinition.objects.filter(school_id=self.school_id).order_by("period_number")
        self.period_numbers = list(self.periods.values_list("period_number", flat=True))
        self.teaching_slots: Set[Tuple[int, int]] = set()
        self.day_first_teaching_period: Dict[int, int] = {}
        self.day_periods: Dict[int, List[int]] = defaultdict(list)

        for p in self.periods:
            days_list = [int(d) for d in p.days] if p.days else list(range(0, 7))
            for day in days_list:
                self.day_periods[day].append(p.period_number)
                if not p.is_assembly and not p.is_lunch and not p.is_break:
                    self.teaching_slots.add((p.period_number, day))
                    if day not in self.day_first_teaching_period or p.period_number < self.day_first_teaching_period[day]:
                        self.day_first_teaching_period[day] = p.period_number

        self.class_teacher_sections: Dict[int, Set[int]] = defaultdict(set)
        for teacher in Teacher.objects.filter(school_id=self.school_id, is_class_teacher=True):
            if teacher.class_teacher_for:
                for sec in Section.objects.filter(class_instance=teacher.class_teacher_for):
                    self.class_teacher_sections[teacher.id].add(sec.id)

        assignments = TeacherSubjectAssignment.objects.filter(
            teacher__school_id=self.school_id
        ).select_related("teacher", "class_subject__class_instance", "class_subject__subject")

        combined_map: Dict[Tuple[int, int, str], List[Any]] = defaultdict(list)
        task_idx = 0

        for assignment in assignments:
            class_subject = assignment.class_subject
            class_obj = class_subject.class_instance

            if getattr(assignment, "is_combined", False):
                group_key = (
                    assignment.teacher_id,
                    class_subject.subject_id,
                    getattr(assignment, "combined_group_name", None) or "JointGroup"
                )
                combined_map[group_key].append(assignment)
            else:
                # SECTION-SPECIFIC SUPPORT (from engine_final)
                if hasattr(assignment, "target_sections") and assignment.target_sections.exists():
                    sections = assignment.target_sections.filter(is_active=True)
                else:
                    sections = Section.objects.filter(class_instance=class_obj, is_active=True)

                for section in sections:
                    is_ct = section.id in self.class_teacher_sections.get(assignment.teacher_id, set())
                    for _ in range(assignment.weekly_periods):
                        task = Task(
                            idx=task_idx,
                            teacher_id=assignment.teacher_id,
                            class_id=class_obj.id,
                            section_id=section.id,
                            subject_id=class_subject.subject_id,
                            teacher=assignment.teacher,
                            class_subject=class_subject,
                            section=section,
                            total_weekly_periods=assignment.weekly_periods,
                            is_class_teacher_slot=is_ct,
                            is_double=getattr(assignment, "is_double_period", False),
                            is_practical=getattr(assignment, "is_practical", False),
                        )
                        self.tasks.append(task)
                        task_idx += 1

        for (teacher_id, subject_id, group_name), group_assignments in combined_map.items():
            first = group_assignments[0]
            target_sections = []
            for ga in group_assignments:
                sec = Section.objects.filter(
                    class_instance=ga.class_subject.class_instance, is_active=True
                ).first()
                if sec and sec not in target_sections:
                    target_sections.append(sec)

            cg = CombinedGroup(
                teacher_id=teacher_id,
                subject_id=subject_id,
                teacher=first.teacher,
                subject=first.class_subject.subject,
                target_sections=target_sections,
                group_name=group_name,
                weekly_periods=first.weekly_periods,
                assignments=group_assignments,
            )
            self.combined_groups.append(cg)

            for _ in range(first.weekly_periods):
                task = Task(
                    idx=task_idx,
                    teacher_id=teacher_id,
                    class_id=target_sections[0].class_instance_id if target_sections else None,
                    section_id=target_sections[0].id if target_sections else None,
                    subject_id=subject_id,
                    teacher=first.teacher,
                    class_subject=first.class_subject,
                    section=target_sections[0] if target_sections else None,
                    total_weekly_periods=first.weekly_periods,
                    is_class_teacher_slot=False,
                    is_combined=True,
                    combined_group=group_name,
                    target_sections=target_sections,
                )
                self.tasks.append(task)
                task_idx += 1

        self.teacher_availability: Dict[int, Set[Tuple[int, int]]] = defaultdict(set)
        teachers = Teacher.objects.filter(school_id=self.school_id)
        for teacher in teachers:
            for day in range(0, 6):
                for period in self.period_numbers:
                    un_days = teacher.unavailable_days or []
                    un_periods = teacher.unavailable_periods or []
                    if day not in un_days and period not in un_periods:
                        self.teacher_availability[teacher.id].add((day, period))

        self.fixed_section_occupied: Set[Tuple[int, int, int, int]] = set()
        self.fixed_teacher_occupied: Set[Tuple[int, int, int]] = set()

        fixed_entries = TimetableEntry.objects.filter(
            session_id=self.session_id, is_fixed=True
        ).select_related("teacher")

        for entry in fixed_entries:
            self.fixed_section_occupied.add(
                (entry.class_instance_id, entry.section_id, entry.day_of_week, entry.period_number)
            )
            self.fixed_teacher_occupied.add(
                (entry.teacher_id, entry.day_of_week, entry.period_number)
            )

        self.class_working_days: Dict[int, List[int]] = defaultdict(list)
        for section in Section.objects.filter(class_instance__school_id=self.school_id):
            self.class_working_days[section.class_instance.id] = section.working_days or list(range(0, 6))

        self.rooms = list(Room.objects.filter(school_id=self.school_id, is_active=True))

        self.teacher_max_daily_load_dict: Dict[int, int] = {}
        self.teacher_max_weekly_load_dict: Dict[int, int] = {}
        for teacher in teachers:
            self.teacher_max_daily_load_dict[teacher.id] = getattr(teacher, "max_daily_load", None) or 8
            self.teacher_max_weekly_load_dict[teacher.id] = getattr(teacher, "max_weekly_load", None) or 40

        # Load targets for scoring (from engine.py)
        self.teacher_load_targets: Dict[int, int] = defaultdict(int)
        for task in self.tasks:
            self.teacher_load_targets[task.teacher_id] += 1

    def _build_domains(self):
        for task in self.tasks:
            self.initial_domains[task.idx] = self._compute_domain(task)

    def _compute_domain(self, task: Task) -> List[Tuple[int, int]]:
        domain = []
        if task.is_combined:
            for day in range(6):
                for period in self.period_numbers:
                    if (period, day) not in self.teaching_slots:
                        continue
                    if (day, period) not in self.teacher_availability.get(task.teacher_id, set()):
                        continue
                    if (task.teacher_id, day, period) in self.fixed_teacher_occupied:
                        continue
                    collision = any(
                        (sec.class_instance_id, sec.id, day, period) in self.fixed_section_occupied
                        for sec in (task.target_sections or [])
                    )
                    if not collision:
                        domain.append((day, period))
        else:
            class_id = task.class_id
            section_id = task.section_id
            teacher_id = task.teacher_id
            for day in self.class_working_days.get(class_id, list(range(0, 6))):
                for period in self.period_numbers:
                    if (period, day) not in self.teaching_slots:
                        continue
                    if (day, period) not in self.teacher_availability.get(teacher_id, set()):
                        continue
                    if (class_id, section_id, day, period) in self.fixed_section_occupied:
                        continue
                    if (teacher_id, day, period) in self.fixed_teacher_occupied:
                        continue
                    domain.append((day, period))
        return domain

    def _build_legacy_lists(self):
        """Maintain legacy variable lists for external consumers (e.g. genetic optimizer)."""
        self.variables = []
        self.combined_variables = []
        for t in self.tasks:
            d = {
                "teacher_id": t.teacher_id,
                "class_id": t.class_id,
                "section_id": t.section_id,
                "subject_id": t.subject_id,
                "teacher": t.teacher,
                "class_subject": t.class_subject,
                "section": t.section,
                "total_weekly_periods": t.total_weekly_periods,
                "is_class_teacher_slot": t.is_class_teacher_slot,
                "is_combined": t.is_combined,
                "is_double": t.is_double,
                "is_practical": t.is_practical,
            }
            if t.is_combined:
                d.update({"target_sections": t.target_sections, "group_name": t.combined_group})
                self.combined_variables.append(d)
            else:
                self.variables.append(d)

    def solve(self, use_genetic=True, time_limit_seconds=60):
        t0 = time.time()

        # 1. Pre-schedule combined classes (FIXED: handles weekly_periods > 1 correctly)
        combined_assignments = self._schedule_combined_classes()

        # 2. Setup backtracking state
        store = DomainStore(self.tasks, self.initial_domains)
        assignment: Dict[int, Tuple[int, int]] = dict(combined_assignments)
        unassigned: Set[int] = set(t.idx for t in self.tasks) - set(combined_assignments.keys())

        # 3. Systematic backtracking (MRV + forward checking + LCV scoring)
        solution = None
        try:
            solution = self._backtrack(
                assignment=assignment, unassigned=unassigned, store=store,
                daily_load=defaultdict(lambda: defaultdict(int)),
                total_load=defaultdict(int),
                subject_daily_dist=defaultdict(int),
                start_time=t0, time_limit=time_limit_seconds, depth=0,
            )
        except TimeoutError:
            logger.warning("Systematic search timed out; falling back to local search.")

        # 4. Local-search repair fallback
        if solution is None:
            logger.info("Attempting local-search repair...")
            solution = self.local_search.optimize(assignment)

        if solution is None:
            logger.error("No solution found.")
            return None

        # 5. Optional genetic polish
        if use_genetic and GeneticOptimizer is not None:
            try:
                max_period = max(self.period_numbers) if self.period_numbers else 7
                ga = GeneticOptimizer(self.tasks, max_period=max_period)
                sol_list = [solution.get(i, (None, None)) for i in range(len(self.tasks))]
                improved = ga.improve(sol_list)
                if improved:
                    solution = {i: improved[i] for i in range(len(self.tasks))}
            except Exception as e:
                logger.warning(f"Genetic optimizer failed: {e}")

        # 6. Save
        return self._save_solution(solution)

    def _schedule_combined_classes(self) -> Dict[int, Tuple[int, int]]:
        """
        Greedy pre-scheduler for combined groups.
        Returns a dict mapping task.idx -> (day, period).
        Handles weekly_periods > 1 correctly.
        """
        pre_assignments: Dict[int, Tuple[int, int]] = {}

        scored_groups = [(len(self._combined_domain(cg)), cg) for cg in self.combined_groups]
        scored_groups.sort(key=lambda x: x[0])

        for _, cg in scored_groups:
            group_tasks = [
                t for t in self.tasks
                if t.is_combined
                and t.teacher_id == cg.teacher_id
                and t.subject_id == cg.subject_id
                and t.combined_group == cg.group_name
            ]

            domain = self._combined_domain(cg)
            if len(domain) < len(group_tasks):
                logger.warning(
                    f"Combined group {cg.group_name} needs {len(group_tasks)} slots but only {len(domain)} available."
                )
                continue

            selected_slots = []
            remaining_domain = list(domain)

            for _ in range(len(group_tasks)):
                if not remaining_domain:
                    break
                best_slot = min(remaining_domain, key=lambda slot: self._combined_impact(cg, *slot))
                day, period = best_slot
                selected_slots.append(best_slot)
                remaining_domain = [s for s in remaining_domain if s != best_slot]

                self.fixed_teacher_occupied.add((cg.teacher_id, day, period))
                for sec in cg.target_sections:
                    self.fixed_section_occupied.add((sec.class_instance_id, sec.id, day, period))

            if len(selected_slots) < len(group_tasks):
                # Rollback occupied state on partial failure
                for day, period in selected_slots:
                    self.fixed_teacher_occupied.discard((cg.teacher_id, day, period))
                    for sec in cg.target_sections:
                        self.fixed_section_occupied.discard((sec.class_instance_id, sec.id, day, period))
                logger.warning(f"Could only schedule {len(selected_slots)}/{len(group_tasks)} for {cg.group_name}")
                continue

            for i, (day, period) in enumerate(selected_slots):
                task = group_tasks[i]
                pre_assignments[task.idx] = (day, period)

        return pre_assignments

    def _combined_domain(self, cg: CombinedGroup) -> List[Tuple[int, int]]:
        domain = []
        for day in range(6):
            for period in self.period_numbers:
                if (period, day) not in self.teaching_slots:
                    continue
                if (day, period) not in self.teacher_availability.get(cg.teacher_id, set()):
                    continue
                if (cg.teacher_id, day, period) in self.fixed_teacher_occupied:
                    continue
                if any(
                    (sec.class_instance_id, sec.id, day, period) in self.fixed_section_occupied
                    for sec in cg.target_sections
                ):
                    continue
                domain.append((day, period))
        return domain

    def _combined_impact(self, cg: CombinedGroup, day: int, period: int) -> int:
        impact = 0
        for task in self.tasks:
            if task.is_combined:
                continue
            if task.teacher_id == cg.teacher_id:
                if (day, period) in self.initial_domains.get(task.idx, []):
                    impact += 1
            for sec in cg.target_sections:
                if task.section_id == sec.id and (day, period) in self.initial_domains.get(task.idx, []):
                    impact += 1
        impact += day * 2 + period * 5
        return impact

    def _backtrack(self, assignment, unassigned, store,
                   daily_load, total_load, subject_daily_dist,
                   start_time, time_limit, depth):
        if time.time() - start_time > time_limit:
            raise TimeoutError("Time limit exceeded")
        if not unassigned:
            return assignment

        # MRV: choose task with smallest remaining domain
        mrv_task = None
        mrv_idx = None
        min_size = float("inf")
        for idx in unassigned:
            sz = store.size(idx)
            if sz < min_size:
                min_size = sz
                mrv_idx = idx
                mrv_task = self.tasks[idx]
                if sz == 0:
                    return None

        if mrv_task is None or min_size == 0:
            return None

        unassigned.remove(mrv_idx)

        # Order values by heuristic score (LCV + preferences)
        scored_values = []
        for val in store.values(mrv_idx):
            sc = self._value_score(mrv_task, val, unassigned, store,
                                   daily_load, total_load, subject_daily_dist)
            scored_values.append((sc, val))
        scored_values.sort(key=lambda x: x[0])

        for _, val in scored_values:
            day, period = val
            if not self._is_consistent(mrv_task, val, assignment):
                continue
            if daily_load[mrv_task.teacher_id][day] >= self.teacher_max_daily_load_dict.get(mrv_task.teacher_id, 8):
                continue
            if total_load[mrv_task.teacher_id] >= self.teacher_max_weekly_load_dict.get(mrv_task.teacher_id, 40):
                continue

            assignment[mrv_idx] = val
            store.push()
            daily_load[mrv_task.teacher_id][day] += 1
            total_load[mrv_task.teacher_id] += 1
            subject_daily_dist[(mrv_task.section_id, mrv_task.subject_id, day)] += 1

            affected = self.constraints.get_affected_indices(mrv_task, unassigned)
            if not store.prune(mrv_idx, val, affected, self.constraints):
                store.pop()
                del assignment[mrv_idx]
                daily_load[mrv_task.teacher_id][day] -= 1
                total_load[mrv_task.teacher_id] -= 1
                subject_daily_dist[(mrv_task.section_id, mrv_task.subject_id, day)] -= 1
                continue

            result = self._backtrack(
                assignment, unassigned, store,
                daily_load, total_load, subject_daily_dist,
                start_time, time_limit, depth + 1,
            )
            if result is not None:
                return result

            store.pop()
            del assignment[mrv_idx]
            daily_load[mrv_task.teacher_id][day] -= 1
            total_load[mrv_task.teacher_id] -= 1
            subject_daily_dist[(mrv_task.section_id, mrv_task.subject_id, day)] -= 1

        unassigned.add(mrv_idx)
        return None

    def _is_consistent(self, task: Task, val: Tuple[int, int],
                       assignment: Dict[int, Tuple[int, int]]) -> bool:
        for other_idx, other_val in assignment.items():
            other = self.tasks[other_idx]
            if self.constraints.hard_conflict(task, val, other, other_val):
                return False
        return True

    def _value_score(self, task: Task, val: Tuple[int, int],
                     unassigned: Set[int], store: DomainStore,
                     daily_load, total_load, subject_daily_dist) -> float:
        day, period = val
        score = 0.0

        # Prefer first period for class teacher (from engine.py)
        first_tp = self.day_first_teaching_period.get(day, 2)
        if task.is_class_teacher_slot:
            if period == first_tp:
                score -= 5000
            elif period == first_tp + 1:
                score -= 1000

        # Subject daily distribution preference (from engine.py)
        working_days = len(self.class_working_days.get(task.class_id, list(range(0, 6))))
        current_daily = subject_daily_dist.get((task.section_id, task.subject_id, day), 0)
        if task.total_weekly_periods <= working_days:
            if current_daily >= 1:
                score += 2000
        else:
            if current_daily >= 2:
                score += 2000

        # Teacher load balancing preference (from engine.py)
        current_load = total_load.get(task.teacher_id, 0)
        target_load = self.teacher_load_targets.get(task.teacher_id, 0)
        if current_load < target_load:
            score -= 200

        # LCV: penalize values that constrain many future tasks (from engine_final)
        lcv_penalty = 0
        task_sections = {s.id for s in (task.target_sections or [])} or {task.section_id}
        for other_idx in unassigned:
            if other_idx == task.idx:
                continue
            other = self.tasks[other_idx]
            other_sections = {s.id for s in (other.target_sections or [])} or {other.section_id}
            if task.teacher_id == other.teacher_id or task_sections & other_sections:
                for v in store.values(other_idx):
                    if v == val:
                        lcv_penalty += 1
        score += lcv_penalty * 50

        # Slight preference for later periods (from engine.py)
        score += period * 10
        score += current_daily * 100
        return score

    def _save_solution(self, solution: Dict[int, Tuple[int, int]]):
        entries = []
        room_occupied: Set[Tuple[int, int, int]] = set()

        for task in self.tasks:
            if task.idx not in solution:
                continue
            day, period = solution[task.idx]

            if task.is_combined:
                # One entry per target section, all sharing the same group id
                cid = str(uuid.uuid4())[:8]
                for sec in (task.target_sections or []):
                    entries.append(TimetableEntry(
                        school_id=self.school_id,
                        session_id=self.session_id,
                        class_instance_id=sec.class_instance_id,
                        section=sec,
                        teacher_id=task.teacher_id,
                        subject_id=task.subject_id,
                        day_of_week=day,
                        period_number=period,
                        is_combined=True,
                        combined_group_id=task.combined_group or cid,
                        is_double=False,
                        is_practical=False,
                        room_id=None,
                    ))
            else:
                room_id = None
                if task.is_practical and self.rooms:
                    for room in self.rooms:
                        if (room.id, day, period) not in room_occupied:
                            room_id = room.id
                            room_occupied.add((room.id, day, period))
                            break

                entries.append(TimetableEntry(
                    school_id=self.school_id,
                    session_id=self.session_id,
                    class_instance_id=task.class_id,
                    section_id=task.section_id,
                    teacher_id=task.teacher_id,
                    subject_id=task.subject_id,
                    day_of_week=day,
                    period_number=period,
                    is_double=task.is_double,
                    is_practical=task.is_practical,
                    room_id=room_id,
                    is_combined=False,
                    combined_group_id=None,
                ))

        TimetableEntry.objects.filter(
            school_id=self.school_id, session_id=self.session_id, is_fixed=False,
        ).delete()

        with transaction.atomic():
            TimetableEntry.objects.bulk_create(entries)

        return len(entries)