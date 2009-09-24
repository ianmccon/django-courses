from django.contrib import admin
from courses.models import Course, Department, Klass, Instructor

class CourseAdmin(admin.ModelAdmin):
    list_display = ('department_abbr', 'coursenumber', 'name')
    search_fields = ('department_abbr', 'coursenumber')

class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'abbr')
    search_fields = ('name', 'abbr')

class KlassAdmin(admin.ModelAdmin):
    list_display = ('course', 'semester')
    search_fields = ('course__department_abbr', 'course__coursenumber', 'semester', )



