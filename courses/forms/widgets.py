from django import forms
from django.db import models
from django.forms.widgets import flatatt
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe
from ajaxwidgets.widgets import ModelAutocomplete
from courses.models import Course, Department

import re

AUTOCOMPLETE_URLS = {
'department' : '/courses/department_autocomplete/',
'coursenumber' : '/courses/coursenumber_autocomplete/',
'instructor' : '/courses/instructor_autocomplete/',
'subject' : '/courses/subject_autocomplete/',
}

class DepartmentAutocomplete(ModelAutocomplete):
    def __init__(self, list_series=1, abbreviations=False, *args, **kwargs):
        kwargs['attrs'] = kwargs.get('attrs', {})
        kwargs['attrs'].update({'department_autocomplete' : list_series})
        self.list_series = list_series
        super(DepartmentAutocomplete, self).__init__(
            AUTOCOMPLETE_URLS['department'],
            *args, **kwargs)

class SubjectAutocomplete(ModelAutocomplete):
    def __init__(self, list_series=1, abbreviations=False, *args, **kwargs):
        kwargs['attrs'] = kwargs.get('attrs', {})
        kwargs['attrs'].update({'subject_autocomplete' : list_series})
        self.list_series = list_series
        super(SubjectAutocomplete, self).__init__(
            AUTOCOMPLETE_URLS['subject'],
            *args, **kwargs)

    def render_additional_result_javascript(self, name):
        return u'''
        elementlist.add_element_to_list('%(list_series)s', data[1], data[0]);
        $(this).attr('value', '');
''' % (self.__dict__)


class CourseNumberAutocomplete(ModelAutocomplete):
    def __init__(self, list_series=1, abbreviations=False, *args, **kwargs):
        kwargs['attrs'] = kwargs.get('attrs', {})
        kwargs['attrs'].update({'coursenumber_autocomplete' : list_series})
        if abbreviations:
            abbreviations = ', abbrs : true'
        else:
            abbreviations = ''
        self.list_series = list_series
        self.abbrs = abbreviations
        kwargs['options'] = """{ extraParams : {department_query : function () { return $('[department_autocomplete=%(list_series)s]').attr("value") } %(abbrs)s }, matchContains : true, delay : 100, cacheLength : 10 }""" % self.__dict__

            
        super(CourseNumberAutocomplete, self).__init__(
            AUTOCOMPLETE_URLS['coursenumber'],
            *args, **kwargs)

    def render(self, name, value=None, attrs={}):
        html = super(CourseNumberAutocomplete, self).render(name, value, attrs)
        return mark_safe(html + u"""
<p>&nbsp;</p>
<script language="javascript">
    $('[department_autocomplete=%(list_series)s]').focus( function() {
        $('[coursenumber_autocomplete=%(list_series)s]').flushCache();
    }).blur( function () {
        $('[coursenumber_autocomplete=%(list_series)s]').flushCache();
    });
    
    $('[coursenumber_autocomplete=%(list_series)s]').result( function(event, data, formatted) {
        courselist_result(data, %(list_series)s);
        $(this).attr('value', '');
    });
</script>
""" % (self.__dict__) )

ELEMENTLIST_KEY_RE = re.compile("elementlist_(?P<list_series>\d+)_(?P<counter>\d+)")
class ElementList(forms.Widget):
    def __init__(self, list_series=1, attrs={}):
        self.list_series = list_series
        self.attrs = attrs

    def value_from_datadict(self, datadict, files, name):
        if datadict.has_key(name):
            return datadict[name]
        values = []
        for key, value in datadict.items():
            m = ELEMENTLIST_KEY_RE.match(key)
            if m and int(m.group('list_series')) == self.list_series:
                values.append((value, int(m.group('counter'))))
        values.sort(key=lambda x: x[1])
        values = [value[0].split(',', 1) for value in values]
        return values

    def render_javascript(self, name, value=None):
        d = {'name': name}
        d.update(self.__dict__)
        items = []
        if value:
            for item in value:
                if isinstance(item, models.Model):
                   item  = (item.pk, unicode(item))
                items.append("""elementlist.add_element_to_list("%s", "%s", "%s", "%s");""" % (self.list_series, item[0], item[1], name))
        d['items'] = "\n".join(items)
        return u"""
    <script type='text/javascript'>
        $(document).ready( function() {
            %(items)s
        });
    </script>
""" % d

    def render(self, name, value=None, attrs={}):
            d = {'name' : name}
            d.update(self.__dict__)
            d['js'] = self.render_javascript(name, value)
            return mark_safe(u""" 
<ul class="elementlist" list_series="%(list_series)s" id="id_%(name)s">
    <li element_id="-1">Nothing selected yet</li>
</ul>
%(js)s""" % d)

    class Media:
        js = ( settings.STATIC_URL + "courses/course.js", settings.STATIC_URL + "courses/jquery.color.js", )

class CourseAutocomplete(forms.MultiWidget):
    def __init__(self, attrs=None, list_series=1):
        widgets = (
            DepartmentAutocomplete(list_series=list_series, attrs={"style" : "width: 10em"}),
            CourseNumberAutocomplete(list_series=list_series, attrs={"style" : "width: 4em"}),
        )
        super(CourseAutocomplete, self).__init__(widgets, attrs)

    def decompress(self, value):
        if value and instanceof(value, Course):
            return [value.department, value.coursenumber]
        return [None, None]
            
            
class InstructorAutocomplete(ModelAutocomplete):
    def __init__(self, list_series=1, *args, **kwargs):
        kwargs['attrs'] = kwargs.get('attrs', {})
        kwargs['attrs'].update({'instructor_autocomplete' : list_series})
        kwargs['options'] = """{ extraParams : {department_query : function () { return $('[department_autocomplete=%s]').attr("value") }, coursenumber_query : function () { return $('[coursenumber_autocomplete=%s]').attr("value") } } }""" % (list_series, list_series)
        super(InstructorAutocomplete, self).__init__(
            AUTOCOMPLETE_URLS['instructor'],
            *args, **kwargs)


