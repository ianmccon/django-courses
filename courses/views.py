from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.db.models.query import Q

from courses.models import *

from ajaxlist import get_list_context, filter_objects

from string import atoi

def find_course(request):
    list_context = get_list_context(request, default_sort = "department_abbr", default_max = "20")
    query_function = lambda objects, query: objects.ft_query(query)
    courses = filter_objects(Course, list_context, query_objects = query_function)
    return render_to_response("course/ajax/find_course.html", {"courses" : courses}, context_instance = RequestContext(request))
    
def course_autocomplete(request):
    def iter_results(courses):
        if courses:
            for r in courses:
                yield '%s|%s\n' % (r.short_name(space = True), r.id)
    
    if not request.GET.get('q'):
        return HttpResponse(mimetype='text/plain')
    
    q = request.GET.get('q')
    limit = request.GET.get('limit', 15)
    try:
        limit = int(limit)
    except ValueError:
        return HttpResponseBadRequest() 

    courses = Course.objects.ft_query(q)[:limit]
    return HttpResponse(iter_results(courses), mimetype='text/plain')

def department_autocomplete(request):
    def iter_results(departments):
        if departments:
            for r in departments:
                yield '%s|%s\n' % (r.name, r.pk)
    
    if not request.GET.get('q'):
        return HttpResponse(mimetype='text/plain')
    
    q = request.GET.get('q').strip()
    limit = request.GET.get('limit', 15)
    try:
        limit = int(limit)
    except ValueError:
        return HttpResponseBadRequest() 

    depts = Department.objects.ft_query(q)
    if depts.count() == 0:
        depts = Department.objects.ft_query_name_fuzzy(q)
    return HttpResponse(iter_results(depts), mimetype='text/plain')

def subject_autocomplete(request, major=None):
    def iter_results(subjects):
        if subjects:
            if major is None:
                for r in subjects:
                    yield '%s|%s\n' % (unicode(r), r.pk)
            else:
                for r in subjects:
                    yield '%s|%s\n' % (r.name, r.pk)
    
    if not request.GET.get('q'):
        return HttpResponse(mimetype='text/plain')
    
    q = request.GET.get('q').strip()
    limit = request.GET.get('limit', 15)
    try:
        limit = int(limit)
    except ValueError:
        return HttpResponseBadRequest() 

    if major is None:
        subjects = Subject.objects.filter(name__icontains=q)[:limit]
    else:
        subjects = Subject.objects.filter(major=major).filter(name__icontains=q)[:limit]
    return HttpResponse(iter_results(subjects), mimetype='text/plain')

def coursenumber_autocomplete(request):
    dept_abbrs = request.GET.get('abbrs', False)
    def iter_results(courses):
        if courses:
            if dept_abbrs:
                for r in courses:
                    yield '%s: %s|%s,,%s\n' % (r.coursenumber, r.name, r.short_name(space=True), r.id)
            else:
                for r in courses:
                    yield '%s|%s\n' % (r.coursenumber, r.id)
    
    if not (request.GET.has_key('q') and request.GET.has_key("department_query")) :
        return HttpResponse(mimetype='text/plain')
    
    q = request.GET.get('q')
    limit = request.GET.get('limit', 15)
    try:
        limit = int(limit)
    except ValueError:
        return HttpResponseBadRequest() 

    dq = request.GET.get("department_query")
    depts = Department.objects.ft_query_name(dq)
    if depts.count() == 0:
        depts = Department.objects.ft_query(dq)
    courses = Course.objects.filter(department__in = depts).query_coursenumber(q)

    return HttpResponse(iter_results(courses), mimetype='text/plain')

def department_abbreviations(request):
    departments = Department.objects.order_by('name')
    return render_to_response("course/department_abbreviations.html", {"departments" : departments}, context_instance=RequestContext(request))

