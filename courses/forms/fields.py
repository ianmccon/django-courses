from django import forms

from courses.models import Subject, Instructor, Course, Department
from courses.forms.widgets import *

def get_subjects_choices(majors, description=None):
    if not description:
        description = "major" if majors else "minor"
    return [("choose", "-- Choose a %s" % description)] + list(Subject.objects.filter(major=majors).values_list('id', 'name'))

def _get_subjects_choice_field(major):
    class SubjectsChoiceField(forms.ChoiceField):
        def __init__(self, description=None, *args, **kwargs):
            kwargs['choices'] = get_subjects_choices(major, description)
            kwargs['initial'] = "choose"
            super(SubjectsChoiceField, self).__init__(*args, **kwargs)
        
        def clean(self, value):
            if value in (None, "choose"):
                return None
            try:
                return Subject.objects.get(id=int(value))
            except ValueError:
                raise forms.ValidationError("Subject is invalid")
            except Subject.DoesNotExist:
                raise forms.ValidationError("Subject is invalid")
            
    return SubjectsChoiceField

MajorsChoiceField = _get_subjects_choice_field(True)
MinorsChoiceField = _get_subjects_choice_field(False)

class InstructorAutocompleteField(forms.CharField):
    def __init__(self, *args, **kwargs):
        kwargs['widget'] = InstructorAutocomplete()
        super(InstructorAutocompleteField, self).__init__(*args, **kwargs)

    def clean(self, value):
        name, id = value.split("|")
        try:
            id = int(id)
            return Instructor.objects.get(pk=id)
        except ValueError:
            pass
        
        name = name.strip()
        if not name:
            return super(InstructorAutocompleteField, self).clean(None)

        insts = Instructor.objects.ft_query(name)
        if len(insts) == 0:
            raise forms.ValidationError("Instructor '%s' not found!" % name)
        elif len(insts) > 1:
            raise forms.ValidationError("Too many matches for instructor '%s'!" % name)
        return insts[0]
 
class CourseAutocompleteField(forms.Field):
    def __init__(self, *args, **kwargs):
        kwargs['widget'] = CourseAutocomplete()
        super(CourseAutocompleteField, self).__init__(*args, **kwargs)

    def clean(self, value):
        (coursenumber, course_id) = value[1].split("|")
        coursenumber = coursenumber.strip()
        if not coursenumber:
            return super(CourseAutocompleteField, self).clean(None)

        try:
            course_id = int(course_id)
            return Course.objects.get(pk=course_id)
        except ValueError:
            pass
        except Course.DoesNotExist:
            pass

        (department_name, department_id) = value[0].split("|")
        department_name = department_name.strip()
        if not department_name:
            return super(CourseAutocompleteField, self).clean(None)

        try:
            department_id = int(department_id)
            department = Department.objects.get(pk=department_id)
        except (ValueError, Department.DoesNotExist):
            departments = Department.objects.ft_query_name(department_name)
            if len(departments) == 0:
                departments = Department.objects.ft_query_all(department_name)
            if len(departments) == 0:
                raise forms.ValidationError("Could not match department '%s'" % department_name)
            if len(departments) > 1:
                raise forms.ValidationError("Too many matches for department '%s'" % department_name)
            department = departments[0]
        
        dept_abbr = department.abbr
        courses = Course.objects.query_exact(dept_abbr, coursenumber)
        if len(courses) == 0:
            raise forms.ValidationError("Could not match course '%s %s'" % (department.name, coursenumber))
        if len(courses) > 1:
            raise forms.ValidationError("Too many matches for course '%s %s'" % (department.name, coursenumber))
        return courses[0]

def _make_many_field(clazz, name):
    class ManyField(forms.Field):
        widget = ElementList

        def clean(self, value):
            if self.required and not value:
                raise forms.ValidationError("Please input at least one %s" % name)
            if not isinstance(value, (tuple, list)):
                raise forms.ValidationError("Please supply a list of values")

            elements = []
            for element_id, element_display in value:
                try:
                    elements.append(clazz._default_manager.get(pk=int(element_id)))
                except (ValueError, clazz.DoesNotExist):
                    raise forms.ValidationError("Invalid %s with id %s" % (name, element_id))
            return elements
    return ManyField

ManyCoursesField = _make_many_field(Course, 'course')
ManySubjectsField = _make_many_field(Subject, 'subject')
