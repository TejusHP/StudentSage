from django import template
import datetime
from django.utils.safestring import mark_safe
import json
from firstapp.models import *
from django.utils import timezone
register = template.Library()

@register.filter
def compareTwo(value,arg):
    if value==arg:
        return True
    return False

@register.filter(is_safe=True)
def js(obj):
    return mark_safe(json.dumps(obj))

@register.filter(is_safe=True)
def toUTC(test):
    return test.isoformat()

@register.filter(is_safe=True)
def test_specific_topic(value,arg):
    return Topics.objects.filter(student=value,test=arg)

@register.filter(is_safe=True)
def student_test_start_time(value,arg):
    return TestAttempt.objects.get(student=value,test=arg).attempt_start

@register.filter(is_safe=True)
def student_test_end_time(value,arg):
    return TestAttempt.objects.get(student=value,test=arg).attempt_end

@register.filter(is_safe=True)
def student_test_attempt_marks(value,arg):
    return TestAttempt.objects.get(student=value,test=arg).test_marks

@register.filter(is_safe=True)
def student_test_attempt_status(value,arg):
    correct_attempt=Students.objects.filter(
        test_history__test=arg,
        test_history__attempt_start__lte=arg.end_time
    )
    correct_attempt_names=[i.name.username for i in correct_attempt]
    if value.name.username in correct_attempt_names:
        return "Accepted"
    return "Late"


@register.filter(is_safe=True)
def compare_timezone(value, arg=None):
    if arg is None:
        arg = timezone.now()
    if value > arg:
        return 'greater'
    return 'lesser'