from django.urls import path
from . import views
from .views import (
    generate_timetable, view_class_timetable, timetable_index,
    teacher_timetable_index, view_teacher_timetable,
    subject_timetable_index, view_subject_timetable,
    master_timetable, free_periods, debug_timetable, select_class, manage_absence, swap_entries, teacher_load, export_pdf, export_excel, export_csv, export_class_pdf, 
    export_class_excel,
    export_class_csv,
    export_teacher_pdf,
    export_teacher_excel,
    export_teacher_csv,
    export_subject_pdf,
    export_subject_excel,
    export_subject_csv,
    free_slots,
    free_periods_by_date,
    room_timetable_index,   # <-- add
    view_room_timetable,
    create_fixed_entries,
    edit_fixed_entry,       # <-- added
    delete_fixed_entry,     # <-- added 
    class_summary,
    class_summary_list,
    class_summary_detail,
    compare_timetables,
    get_sections,
    get_timetable_version
    
)

urlpatterns = [
    path('', timetable_index, name='timetable_index'),
    path('generate/', generate_timetable, name='generate_timetable'),
    path('view/<int:class_id>/<int:section_id>/', view_class_timetable, name='view_class_timetable'),
    
    # Teacher-wise
    path('teachers/', teacher_timetable_index, name='teacher_timetable_index'),
    path('teachers/<int:teacher_id>/', view_teacher_timetable, name='view_teacher_timetable'),
    
    # Subject-wise
    path('subjects/', subject_timetable_index, name='subject_timetable_index'),
    path('subjects/<int:subject_id>/', view_subject_timetable, name='view_subject_timetable'),
    
    # Master timetable
    path('master/', master_timetable, name='master_timetable'),
    
    # Free periods
    path('free/', free_periods, name='free_periods'),
    path('debug/', debug_timetable, name='debug_timetable'),
    path('select/', select_class, name='select_class'),
    path('absence/', manage_absence, name='manage_absence'),
    path('swap/', swap_entries, name='swap_entries'),
    path('load/<int:teacher_id>/', teacher_load, name='teacher_load'),
    path('export/pdf/', export_pdf, name='export_pdf'),
    path('export/excel/', export_excel, name='export_excel'),
    path('export/csv/', export_csv, name='export_csv'),
    # Class exports
path('export/class/pdf/<int:class_id>/<int:section_id>/', export_class_pdf, name='export_class_pdf'),
path('export/class/excel/<int:class_id>/<int:section_id>/', export_class_excel, name='export_class_excel'),
path('export/class/csv/<int:class_id>/<int:section_id>/', export_class_csv, name='export_class_csv'),

# Teacher exports
path('export/teacher/pdf/<int:teacher_id>/', export_teacher_pdf, name='export_teacher_pdf'),
path('export/teacher/excel/<int:teacher_id>/', export_teacher_excel, name='export_teacher_excel'),
path('export/teacher/csv/<int:teacher_id>/', export_teacher_csv, name='export_teacher_csv'),

# Subject exports
path('export/subject/pdf/<int:subject_id>/', export_subject_pdf, name='export_subject_pdf'),
path('export/subject/excel/<int:subject_id>/', export_subject_excel, name='export_subject_excel'),
path('export/subject/csv/<int:subject_id>/', export_subject_csv, name='export_subject_csv'),
path('free-slots/', free_slots, name='free_slots'),
path('free-by-date/', free_periods_by_date, name='free_periods_by_date'),
path('rooms/', room_timetable_index, name='room_timetable_index'),
path('rooms/<int:room_id>/', view_room_timetable, name='view_room_timetable'),
path('swap/', swap_entries, name='swap_entries'),
path('fixed/', create_fixed_entries, name='manage_fixed_entries'),
path('fixed/edit/<int:entry_id>/', edit_fixed_entry, name='edit_fixed_entry'),
path('fixed/delete/<int:entry_id>/', delete_fixed_entry, name='delete_fixed_entry'),
path('summary/<int:class_id>/<int:section_id>/', class_summary, name='class_summary'),
# path('summary/', class_summary, name='class_summary'),
path('summary/', class_summary_list, name='class_summary'),
path('summary/detail/<int:class_id>/<int:section_id>/', class_summary_detail, name='class_summary_detail'),
path('compare/', compare_timetables, name='compare_timetables'),
path('get-sections/', views.get_sections, name='get_sections'),
path('api/version/', views.get_timetable_version, name='timetable_version'),
path('assign-teacher/', views.assign_teacher_to_slot, name='assign_teacher_to_slot'),
path('delete-entry/', views.delete_entry_view, name='delete_timetable_entry'),
]