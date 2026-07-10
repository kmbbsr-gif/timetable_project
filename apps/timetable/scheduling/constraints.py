"""
Constraint functions for timetable scheduling.
Each function returns True if the constraint is satisfied, False otherwise.
"""

def no_teacher_overlap(entry1, entry2):
    """Two entries cannot have the same teacher at same day and period."""
    if entry1.teacher_id == entry2.teacher_id:
        return not (entry1.day == entry2.day and entry1.period == entry2.period)
    return True

def no_class_overlap(entry1, entry2):
    """Two entries cannot have the same class and section at same day and period."""
    if entry1.class_id == entry2.class_id and entry1.section_id == entry2.section_id:
        return not (entry1.day == entry2.day and entry1.period == entry2.period)
    return True

def teacher_available(entry, availability):
    """Check if teacher is available at given day/period.
       availability: dict {teacher_id: set of (day, period) tuples}
    """
    teacher_id = entry.teacher_id
    if teacher_id in availability:
        return (entry.day, entry.period) in availability[teacher_id]
    return True  # if no availability data, assume available

def class_working_day(entry, working_days):
    """Check if class works on that day.
       working_days: dict {class_id: list of day integers (0=Mon...6=Sun)}
    """
    class_id = entry.class_id
    if class_id in working_days:
        return entry.day in working_days[class_id]
    return True  # assume all days if not specified

def subject_gap_constraint(entries, min_gap, max_gap, subject_id, class_id):
    """
    For a given subject in a given class, enforce min/max gap between consecutive periods.
    entries is a list of (day, period) tuples for that subject.
    """
    if len(entries) < 2:
        return True
    sorted_entries = sorted(entries, key=lambda x: (x[0], x[1]))
    for i in range(len(sorted_entries)-1):
        day1, per1 = sorted_entries[i]
        day2, per2 = sorted_entries[i+1]
        # Convert to absolute period index (day * max_periods + period)
        max_periods = 8  # typical; we'll compute later
        gap = (day2 - day1) * max_periods + (per2 - per1)
        if gap < min_gap or gap > max_gap:
            return False
    return True