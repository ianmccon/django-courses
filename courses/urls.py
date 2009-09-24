from django.conf.urls.defaults import *

urlpatterns = patterns('',
        url(r'^find_course/$', 'courses.views.find_course', name="course-find-course"),
        url(r'^course_autocomplete/$', 'courses.views.course_autocomplete', name="course-course-autocomplete"),              
        url(r'^department_autocomplete/$', 'courses.views.department_autocomplete', name="course-department-autocomplete"),
        url(r'^subject_autocomplete/$', 'courses.views.subject_autocomplete', name="course-subject-autocomplete"),
        url(r'^major_autocomplete/$', 'courses.views.subject_autocomplete', {'major' : True}, name="course-major-autocomplete"),
        url(r'^minor_autocomplete/$', 'courses.views.subject_autocomplete', {'major' : False}, name="course-minor-autocomplete"),
        url(r'^coursenumber_autocomplete/$', 'courses.views.coursenumber_autocomplete', name="course-coursenumber-autocomplete"),              
        url(r'^instructor_autocomplete/$', 'courses.instructor.instructor_autocomplete', name="course-instructor-autocomplete"), 
        url(r'^department-abbreviations/$', 'courses.views.department_abbreviations', name="course-department-abbreviations"),
    )                        
