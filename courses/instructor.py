from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext

from courses.models import *

from string import atoi

    
def instructor_autocomplete(request):
    def iter_results(instructors):
        if instructors:
            for instructor in instructors:
                yield '%s|%s\n' % (instructor.short_name(first = True, dept = True), instructor.id)
    
    if not request.GET.get('q'):
        return HttpResponse(mimetype='text/plain')
    
    q = request.GET.get('q')
    limit = request.GET.get('limit', 15)
    try:
        limit = int(limit)
    except ValueError:
        return HttpResponseBadRequest() 
    
    course_query = request.GET.get("course_query")

    instructors = Instructor.objects.ft_query_inexact(q, course_query=course_query)
    if len(instructors) == 0:
        instructors = Instructor.objects.ft_query_inexact(q)
    instructors = instructors[:limit]    
    
    
    return HttpResponse(iter_results(instructors), mimetype='text/plain')
