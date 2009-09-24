from django.db import models
from django.db.models import Count
from django.db.models.query import QuerySet
from django.db.models.query import Q
from django.conf import settings
from nice_types.db import QuerySetManager, CachingManager
from nice_types.semester import SemesterField, Semester
from courses.constants import PREFIX, SUFFIX, DEPT_ABBRS, DEPT_ABBRS_INV, DEPT_ABBRS_SET
import re, datetime

class DeletionException(Exception):
    pass

class NoDeleteQuerySet(QuerySet):
    def delete(self, force_delete=False):
        if not force_delete:
            raise DeletionException("Attempt to delete QuerySet; pass force_delete=True to force")
        super(NoDeleteQuerySet, self).super()

class CourseManager(QuerySetManager):
    def parse_query(self, *args, **kwargs):
        return self.get_query_set().parse_query(*args, **kwargs)

    def get_canonical(self, *args, **kwargs):
        return self.get_query_set().get_canonical(*args, **kwargs)

    def ft_query(self, *args, **kwargs):
        return self.get_query_set().ft_query(*args, **kwargs)
        
    def query_exact(self, *args, **kwargs):
        return self.get_query_set().query_exact(*args, **kwargs)

class AllDepartmentManager(QuerySetManager):
    def ft_query(self, *args, **kwargs):
        return self.get_query_set().ft_query(*args, **kwargs)
    
    def ft_query_name(self, *args, **kwargs):
        return self.get_query_set().ft_query_name(*args, **kwargs)
    def ft_query_all(self, *args, **kwargs):
        return self.get_query_set().ft_query_all(*args, **kwargs)

    def ft_query_name_fuzzy(self, *args, **kwargs):
        return self.get_query_set().ft_query_name_fuzzy(*args, **kwargs)

    def annotate_exam_count(self, *args, **kwargs):
        return self.get_query_set().annotate_exam_count(*args, **kwargs)

    def get_top_departments_by_published_exams(self, *args, **kwargs):
        return self.get_query_set().get_top_departments_by_published_exams(*args, **kwargs)

class DepartmentManager(AllDepartmentManager):
    def get_query_set(self, *args, **kwargs):
        return super(DepartmentManager, self).get_query_set(*args, **kwargs).filter(hidden=False)
    
class SubjectMajorManager(models.Manager):
    def get_query_set(self):
        return super(SubjectMajorManager, self).get_query_set().filter(major=True)

class SubjectMinorManager(models.Manager):
    def get_query_set(self):
        return super(SubjectMinorManager, self).get_query_set().filter(major=False)

class Subject(models.Model):
    objects = models.Manager()
    majors = SubjectMajorManager()
    minors = SubjectMinorManager()
    
    name = models.CharField(max_length=100)
    major = models.BooleanField()
        
    def __unicode__(self):
        return u'%s: %s' % ('Major' if self.major else 'Minor', self.name)

class Department(models.Model):
    """ Models one of the academic departments. """
    objects = DepartmentManager()
    all = AllDepartmentManager()
    
    id = models.AutoField(primary_key = True)

    name = models.CharField(max_length = 150, unique = True)
    """ Department name: Electrical Engineering, Physics, etc."""
    
    abbr = models.CharField(max_length = 10, unique = True)
    """ PROPER Department abbreviation: COMPSCI, PHYSICS, MATH, etc."""

    hidden = models.BooleanField()
    """ if this department is hidden """

    @property    
    def nice_abbr(self):
        return Department.get_nice_abbr(self.abbr)
    
    def __str__(self):
        return self.name

    def get_all_abbrs(self):
        return DEPT_ABBRS.get(self.abbr, [self.abbr])

    def get_additional_abbrs(self):
        abbrs = list(self.get_all_abbrs())
        if self.abbr in abbrs:
            abbrs.remove(self.abbr)
        if self.nice_abbr in abbrs:
            abbrs.remove(self.nice_abbr)
        return abbrs

    def published_exam_count(self):
        return self.exam_set.filter(publishable=True).count()
    
    @staticmethod
    def get_nice_abbr(abbr):
        """ replaces COMPSCI (correct abbreviation) with CS (common abbreviation) and the like """
        return DEPT_ABBRS.get(abbr.upper(), (abbr.upper(),))[0]


    @staticmethod
    def get_proper_abbr(abbr):
        """ replaces CS (common abbreviation) with COMPSCI (correct abbreviation) and the like """    
        if abbr:
            return DEPT_ABBRS_INV.get(abbr.upper(), abbr.upper())
        return None

    def __cmp__(self, other):
        return cmp(self.name, other.name)

    class QuerySet(NoDeleteQuerySet):
        def ft_query(self, abbr):
            return self.filter(abbr = Department.get_proper_abbr(abbr))
        
        def ft_query_name(self, name):
            return self.filter(name__iexact = name)

        def ft_query_name_fuzzy(self, name):
            return self.filter(name__icontains = name)

        def ft_query_all(self, q):
            return self.filter(Q(name__icontains = q) | Q(abbr = Department.get_proper_abbr(q)))

        def annotate_exam_count(self, publishable = True):
            return self.filter(exam__publishable=publishable).annotate(exam_count=Count('exam'))

        def get_top_departments_by_published_exams(self,n=10):
            departments = list(self.annotate_exam_count(True).order_by("-exam_count", "name")[:n])
            departments = filter(lambda x: x.exam_count > 0, departments)
            return departments


    
class Course(models.Model):
    """ Models a course (not to be confused with a klass, which is the teaching of a course in a particular semester"""
    objects = courses = CourseManager()
    
    
    id = models.AutoField(primary_key = True)
    
    department = models.ForeignKey(Department)
    """ The department in charge of the course """
    
    department_abbr = models.CharField(max_length = 10)
    """ cached so we can get the course name (which relies on department abbr) without joining """
    
    prefix = models.CharField(max_length=2)
    """ course prefix e.g. R or C or H """

    number = models.CharField(max_length = 10)
    """ The course number without prefixes or suffixes. Note that this isn't really a number, can contain letters e.g. 61A"""
    
    integer_number = models.IntegerField()
    """ the course number as an integer. used for sorting """
    
    suffix = models.CharField(max_length=4)
    """ course suffix e.g. AC; does not include suffixes like "BL" in CS61BL """
    
    coursenumber = models.CharField(max_length=10)
    """ The course number, including prefix and suffix e.g. C281A """
    
    name = models.CharField(max_length = 150)
    """ The course name, e.g. "Structure and Interpretation of Computer Programs" """
    
    description = models.TextField()
    """ A description of the course """
    
    @staticmethod
    def split_coursenumber(coursenumber):
        prefix = suffix = ""
        number = coursenumber.upper()
        for pref in PREFIX.values():
            if number.startswith(pref):
                prefix = pref
                number = number[len(pref):]
                break
        for suff in SUFFIX.values():
            if number.endswith(suff):
                suffix = suff
                number = number[:len(suff)]
        return prefix, number, suffix
    
    def __unicode__(self):
        return self.short_name(space=True)    

    def canonical_name(self):
        return "%s %s" % (self.department_abbr, self.coursenumber)

    def long_name(self):
        return u'%s%s %s' % (Department.get_nice_abbr(self.department_abbr), self.coursenumber, self.name)

    def short_name(self, space = False):
        if space:
            return "%s %s" % (Department.get_nice_abbr(self.department_abbr), self.coursenumber)
        else:
            return "%s%s" % (Department.get_nice_abbr(self.department_abbr), self.coursenumber)

    def short_name_space(self):
        return self.short_name(True)
    
    def __cmp__(self, other):
        return cmp(self.department_abbr, other.department_abbr) or cmp(self.integer_number, other.integer_number)  \
                   or cmp(self.number, other.number)

    class QuerySet(NoDeleteQuerySet):
        course_patterns = (
                         re.compile(r'(?P<dept>[-,A-Za-z_\.& ]+)[\s_]+(?P<course>\w?\d+\w*)'),  # matches "CS 61A"
                         re.compile(r'(?P<dept>[-,A-Za-z_\.& ]+)(?P<course>\d\w*)'),  # matches "CS61A"
                         re.compile(r'(?P<dept>[-,A-Za-z_\.& ]+)'),  # matches "CS"
                         )    
        def parse_query(self, query):
            for course_pattern in Course.QuerySet.course_patterns:
                m = course_pattern.match(query)
                if m:
                    dept = m.groupdict().get("dept").upper().replace(".", "").replace('&', 'and')
                    coursenumber = m.groupdict().get("course")
                    if coursenumber:
                        coursenumber = coursenumber.upper().lstrip("0")
                    if not (dept in DEPT_ABBRS_SET) and dept[:-1] in DEPT_ABBRS_SET:
                        return (Department.get_proper_abbr(dept[:-1]), "%s%s" % (dept[-1], coursenumber))
                    return (Department.get_proper_abbr(dept), coursenumber)
            return (None, None)

        CANONICAL_PATTERN = re.compile(r'(?P<dept>[-,A-Za-z_\.& ]+)\s+(?P<course>\w?\d+\w*)')  # matches "CS 61A"
        def parse_canonical(self, query):
            m = Course.QuerySet.CANONICAL_PATTERN.match(query)
            if not m:
                return None, None
            return m.groupdict().get('dept'), m.groupdict().get('course')
            
        def get_canonical(self, query):
            print query
            abbr, coursenumber = self.parse_canonical(query)
            return self.get(department_abbr__iexact=abbr, coursenumber__iexact=coursenumber)

        def query_coursenumber(self, coursenumber):
            prefix, number, suffix = Course.split_coursenumber(coursenumber)
            self = self.filter(number__istartswith = number)
            if len(prefix) > 0:
                self = self.filter(prefix=prefix.upper())
            if len(suffix) > 0:
                self = self.filter(suffix=suffix.upper())                    
            return self
        
        def ft_query(self, query):
            (dept_abbr, coursenumber) = self.parse_query(query)
        
            self = self.filter(department_abbr__iexact = dept_abbr)        
            if coursenumber:
                self = self.query_coursenumber(coursenumber)
            return self
        
        def query_exact(self, dept_abbr, coursenumber, number=False):
            dept_abbr = Department.get_proper_abbr(dept_abbr)
            if not number:
                return self.filter(department_abbr__iexact = dept_abbr, coursenumber__iexact = coursenumber)
            else:
                return self.filter(department_abbr__iexact = dept_abbr, number__iexact = coursenumber)      
            
        def annotate_exam_count(self, publishable = True):
            return self.filter(exam__publishable=publishable).annotate(exam_count=Count('exam'))

        def get_top_courses_by_published_exams(self,n=10):
            courses = list(self.annotate_exam_count(True).order_by("-exam_count", "name")[:n])
            courses = filter(lambda x: x.exam_count > 0, courses)
            # this sort will get e..g 61A 61B 61C in order
            courses.sort(key=lambda x: x.number)
            # hopefully this is a stable sort... this will sort the rest
            courses.sort(key=lambda x: x.integer_number)
            return courses

    INTEGER_PATTERN = re.compile("(?P<integer>\d+)")
    def save(self, *args, **kwargs):
        if not self.department_abbr:
            self.department_abbr = self.department.abbr
        self.coursenumber = self.coursenumber.upper()
        if self.coursenumber:
            self.prefix, self.number, self.suffix = Course.split_coursenumber(self.coursenumber)
            m = Course.INTEGER_PATTERN.search(self.coursenumber)
            self.integer_number = 0
            if m:
                self.integer_number = int(m.group("integer"))                
        super(Course, self).save(*args, **kwargs)
    def delete(self, *args, **kwargs):
        force = kwargs.pop('force_delete', False)
        if not force:
            raise DeletionException("Attempt to delete '%s'; pass force_delete=True to force" % repr(self))
        super(Course, self).delete(*args, **kwargs)
        
    
    class Meta:
        unique_together = (("department", "coursenumber"),)
        ordering = ("department_abbr", "integer_number", "coursenumber")
        
class KlassManager(QuerySetManager):
    def ft_query(self, *args, **kwargs):
        return self.get_query_set().ft_query(*args, **kwargs)

class Klass(models.Model):
    objects = KlassManager()
    
    id = models.AutoField(primary_key = True)
    
    course = models.ForeignKey(Course)
    """ The course that this klass is a particular instance of """
    
    semester = SemesterField()
    """ The semester this klass was taught """
    
    section = models.CharField(max_length = 10)
    """ 
    The section number of this klass. 
    
    Differentiates multiple teachings of the same course in the same semester
    (i.e. two physics 7A lectures in the same semester, or lots of 194 sections, etc.)
    """
    
    section_type = models.CharField(max_length = 10)
    """
    The section type (LEC, DIS, etc.)
    """
    
    section_note = models.TextField()
    """
    A note for the particular section/klass, used for 194 and 294 series classes to store 
    the title.
    """
    
    website = models.CharField(max_length = 100)
    """ The URL for the klass website """
    
    newsgroup = models.CharField(max_length = 100)
    """ The klass newsgroup """

    cached_instructor_names = models.CharField(max_length = 200, null=True)
    """ cached instructor names """
    
    def pretty_semester(self):
        return self.semester.verbose_description()
    
    def _instructor_names(self):
        if self.cached_instructor_names is None:
            self.cached_instructor_names = "; ".join([inst.last for inst in self.instructors.all()])
            # maybe we shouldn't auto save...
            self.save()
        return self.cached_instructor_names
    instructor_names = property(_instructor_names)

    def __str__(self):
        return "%s %s" % (str(self.course.short_name()), self.semester)

    def delete(self, *args, **kwargs):
        force = kwargs.pop('force_delete', False)
        if not force:
            raise DeletionException("Attempt to delete '%s'; pass force_delete=True to force" % repr(self))
        super(Klass, self).delete(*args, **kwargs)

    class QuerySet(NoDeleteQuerySet):
        def ft_query(self, course, semester):
            season = semester[:2]
            year = int(semester[2:])
            if year < 10:
                year += 2000
            else:
                year += 1900
            year = datetime.date(year=year, month=1, day=1)
            return self.filter(course__in = Course.objects.ft_query(course), semester=semester)
            
    
class InstructorManager(QuerySetManager):
    def parse_query(self, *args, **kwargs):
        return self.get_query_set().parse_query(*args, **kwargs)

    def ft_query(self, *args, **kwargs):
        return self.get_query_set().ft_query(*args, **kwargs)

    def ft_query_inexact(self, *args, **kwargs):
        return self.get_query_set().ft_query_inexact(*args, **kwargs)

    def hinted_query(self, *args, **kwargs):
        return self.get_query_set().hinted_query(*args, **kwargs)
        
    def query_exact(self, *args, **kwargs):
        return self.get_query_set().query_exact(*args, **kwargs)    


    
class Instructor(models.Model):
    """ Models an instructor. """
    
    objects = InstructorManager()
    
    id = models.AutoField(primary_key = True)
    
    home_department = models.ForeignKey(Department, related_name="home_instructors")
    """ This instructor's 'home' department """

    home_department_abbr = models.CharField(max_length = 10)
    """ cached so we can get the course name (which relies on department abbr) without joining """

    departments = models.ManyToManyField(Department, related_name="instructors")
    """ Departments with which this instructor is affiliated """
    
    first = models.CharField(max_length = 30)
    """ Instructor's first name """
    
    middle = models.CharField(max_length = 30)
    """ Instructor's middle name """
    
    last = models.CharField(max_length = 30)
    """ Instructor's last name """
    
    email = models.EmailField()
    """ Instructor's email address """
    
    klasses = models.ManyToManyField(Klass, related_name="instructors")
    """
    A many-to-many relationship of the klasses taught by the instructor.
    """
    
    distinguished_teacher = models.BooleanField()
    """ If this instructor has won the Distinguished Teacher award. """
    
    def __str__(self):
        return self.short_name()
    
    def short_name(self, first = False, dept = False):
        if first or len(self.first) == 0:
            first = self.first
        else:
            first = self.first[0]
            
            
        if dept:
            return "%s, %s [%s]" % (self.last, first, self.home_department_abbr)
        else:
            return "%s, %s" % (self.last, first)

    def save(self, *args, **kwargs):
        if not self.home_department_abbr:
            self.home_department_abbr = self.home_department.nice_abbr
        super(Instructor, self).save(*args, **kwargs)
        if not self.home_department in self.departments.all():
            self.departments.add(self.home_department)        
        assert(self.departments.count() > 0)

    def delete(self, *args, **kwargs):
        force = kwargs.pop('force_delete', False)
        if not force:
            raise DeletionException("Attempt to delete '%s'; pass force_delete=True to force" % repr(self))
        super(Instructor, self).delete(*args, **kwargs)

    class QuerySet(NoDeleteQuerySet):
        instructor_patterns = (
                         re.compile(r'(?P<last>[\w-]*),\s*(?P<first>[\w-]*)\s*\[(?P<dept>\w*)\]'),  # matches "Harvey, Brian [CS]"
                         re.compile(r'(?P<last>[\w-]*),\s*(?P<first>[\w-]*)'),                      # matches "Harvey, Brian"
                         re.compile(r'(?P<first>[\w-]*)\s+(?P<last>[\w-]*)'),                      # matches "Brian Harvey"
                         re.compile(r'(?P<last>[\w-]*)'),                      # matches "Harvey"
                         )
        def parse_query(self, query):        
            for instructor_pattern in Instructor.QuerySet.instructor_patterns:
                m = instructor_pattern.match(query)
                if m:
                    d = m.groupdict()
                    return (d.get("last"), d.get("first"), Department.get_proper_abbr(d.get("dept")))            
            return (None, None, None)
            
        def hinted_query(self, last_name=None, last_startswith=False, first_name=None, force_first=False, department_abbrs=None, force_departments=False, courses=None, exact=False):
            if last_name:
                if last_startswith:
                    self = self.filter(last__istartswith=last_name)
                else:
                    self = self.filter(last__iexact=last_name)
                
            if not force_first and not exact and self.count() <= 1:
                return self
                
            if first_name:
                old_self = self                            
                self = self.filter(first__iexact=first_name)
                if self.count() == 0:
                    self = old_self.filter(first__istartswith=first_name[0])
                if not exact:
                    if not force_first and self.count() == 0:
                       return old_self
                    elif self.count() == 1:
                       return self
                    
            if department_abbrs and len(department_abbrs) > 0:
                old_self = self            
                self = self.filter(departments__abbr__in = department_abbrs)
                
                if not exact:            
                    if self.count() == 0:
                       return old_self
                    elif self.count() == 1:
                       return self
            
            if courses:
                old_self = self
                self = self.filter(klasses__course__in = courses).distinct()

                if not exact and self.count() == 0:
                   return old_self                
                   
            return self        
            
        def ft_query_inexact(self, query, course_query=None):
            return self.ft_query(query, course_query=course_query, last_startswith=True)
            
        def ft_query(self, query, course_query=None, dept_abbr = None, course_number = None, departments=None, courses=None, exact=False, last_startswith=False):
            department_abbrs = None
            if departments and len(departments) > 0:
                department_abbrs = [Department.get_proper_abbr(dept) for dept in departments]        
        
            (last, first, dept_abbr) = self.parse_query(query)
            if department_abbrs is None and dept_abbr is not None:
                department_abbrs = (dept_abbr,)        
        
            if course_query:
                (dept_abbr, course_number) = Course.objects.parse_query(course_query)
                department_abbrs = None
            
            if dept_abbr and course_number:
                courses = Course.objects.filter(department_abbr__iexact = dept_abbr, number__icontains = course_number)
            elif dept_abbr:
                courses = Course.objects.filter(department_abbr__iexact = dept_abbr)            
            
            return self.hinted_query(last_name=last, first_name=first, department_abbrs=department_abbrs, courses=courses, exact=exact, last_startswith=last_startswith)

