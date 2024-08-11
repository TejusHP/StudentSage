import os
import sys
import django
from django.conf import settings
from datetime import timedelta,timezone
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'modelrev2.settings')
django.setup()
from asgiref.sync import sync_to_async


from django.utils import timezone
from google.generativeai.protos import FunctionDeclaration, Schema, Type
from django.core.exceptions import ObjectDoesNotExist
from firstapp.models import *

@sync_to_async
def get_student_tests(student_id: int):
    try:
        student = Students.objects.get(pk=student_id)
        teacher=student.teacher
        tests = Test.objects.filter(teacher=teacher)
        return [{"assigned test name":test.display_name,
                 "test total marks":test.test_total_marks} for test in tests]
    except ObjectDoesNotExist:
        return {"error": "Student not found"}

@sync_to_async
def get_student_test_attempts(student_id: int):
    try:
        student = Students.objects.get(pk=student_id)
        tests = TestAttempt.objects.filter(student=student)
        return [{
            'test': attempt.test.display_name,
            'obtained marks': attempt.test_marks,
            'total marks  of test':attempt.test.test_total_marks,
            'start time':(attempt.attempt_start+timedelta(hours=5,minutes=30)).strftime('%d-%m-%Y %H:%M'),
            'submitted time':(attempt.attempt_end+timedelta(hours=5,minutes=30)).strftime('%d-%m-%Y %H:%M'),
            'topics to focus':[topic.topic for topic in Topics.objects.filter(test=attempt.test,student=student)]
        } for attempt in tests]
    except ObjectDoesNotExist:
        return {"error": "Student not found"}
    
@sync_to_async
def make_personalized_quiz(student_id: int,topic_name:str):
    try:
        student = Students.objects.get(pk=student_id)
        topic_list={i.topic:i.id for i in Topics.objects.filter(student=student)}

        if topic_list.get(topic_name)==None:
            return "No weakness found on topic given. Upload file instead"
        else:
            return settings.BASE_URL +reverse('firstapp:improvement-test',kwargs={'topic_id':topic_list[topic_name]})
    except:
        return {"error": "Student not found"}
        

@sync_to_async
def get_student_answer_details(student_id: int):
    try:
        student = Students.objects.get(pk=student_id)
        tests = TestAttempt.objects.filter(student=student)
        return [{
            'test': i.test.display_name,
            'test result details':i.Submitted_data
        } for i in tests]
    except ObjectDoesNotExist:
        return {"error": "Student not found"}
    
@sync_to_async
def get_student_topics(student_id: int):
    try:
        student = Students.objects.get(pk=student_id)
        topics = Topics.objects.filter(student=student)
        return [topic.topic for topic in topics]
    except ObjectDoesNotExist:
        return {"error": "Student not found"}

@sync_to_async
def get_student_name(student_id: int):
    try:
        student = Students.objects.get(pk=student_id)
        return student.name.username
    except ObjectDoesNotExist:
        return {"error": "Student not found"}

@sync_to_async
def get_student_details(student_id: int):
    try:
        student = Students.objects.get(pk=student_id)
        return {
            "name": student.name.username,
            "teacher": student.teacher.name.username,
            "description": student.description,
            "added_date": (student.added_at + timedelta(hours=5,minutes=30)).strftime('%d-%m-%Y %H:%M')
        }
    except ObjectDoesNotExist:
        return {"error": "Student not found"}

@sync_to_async   
def get_upcoming_tests(student_id: int):
    try:
        student = Students.objects.get(pk=student_id)
        teacher = student.teacher
        upcoming_tests = Test.objects.filter(teacher=teacher, start_time__gte=timezone.now())
        return [{"test name": test.display_name, "scheduled time": test.start_time} for test in upcoming_tests]
    except ObjectDoesNotExist:
        return {"error": "Student not found"}

@sync_to_async
def personalized_greeting(student_id: int):
    try:
        student = Students.objects.get(pk=student_id)
        name = student.name.username
        upcoming_tests = [{"test name": test.display_name, "scheduled time": test.start_time} for test in Test.objects.filter(teacher=student.teacher, start_time__gte=timezone.now())]
        
        greeting = f"Welcome back, {name}!"
        
        if upcoming_tests:
            test_info = "You have the following upcoming test(s):\n"
            for test in upcoming_tests:
                test_info += f"- {test['test name']} on {(test['scheduled time']+timedelta(hours=5,minutes=30)).strftime('%d-%m-%Y %H:%M')}\n"
        else:
            test_info = "You have no upcoming tests scheduled."

        greeting_message = f"{greeting}\n\n{test_info}\n\nIs there anything else you need help with?"

        return greeting_message

    except ObjectDoesNotExist:
        return {"error": "Student not found"}





tools = [
    FunctionDeclaration(
        name="get_student_tests",
        description="Fetch the tests assigned to the student.",
        parameters=Schema(
            type=Type.OBJECT,
            properties={"student_id": Schema(type=Type.NUMBER)},
            required=["student_id"]
        )
    ),
    FunctionDeclaration(
        name="make_personalized_quiz",
        description="Create a personalized quiz for a student based on a specific topic. If the topic is not found in the student's weaknesses topics, it suggests uploading a file.",
        parameters=Schema(
            type=Type.OBJECT,
            properties={"student_id":Schema(type=Type.NUMBER),
                        "topic_name":Schema(type=Type.STRING)},
            required=["student_id","topic_name"]
        )
    ),
    FunctionDeclaration(
        name="get_student_test_attempts",
        description="Fetch the test attempts made by the student which includes a list of dictionaries with details such as the test name, obtained marks, total marks, and topics to focus on.",
        parameters=Schema(
            type=Type.OBJECT,
            properties={"student_id": Schema(type=Type.NUMBER)},
            required=["student_id"]
        )
    ),
    FunctionDeclaration(
        name="get_student_answer_details",
        description="Fetch the test submission details of students which is in form of a list of dictionary data. each elelement of list includes details of each question such as question, options, correct_answer, difficulty, solution, tags,total marks of question, and answer_given.",
        parameters=Schema(
            type=Type.OBJECT,
            properties={"student_id": Schema(type=Type.NUMBER)},
            required=["student_id"]
        )
    ),
    FunctionDeclaration(
        name="get_student_topics",
        description="Fetch the weakness topics related to the student.",
        parameters=Schema(
            type=Type.OBJECT,
            properties={"student_id": Schema(type=Type.NUMBER)},
            required=["student_id"]
        )
    ),
    FunctionDeclaration(
        name="get_student_name",
        description="Fetch the student's name.",
        parameters=Schema(
            type=Type.OBJECT,
            properties={"student_id": Schema(type=Type.NUMBER)},
            required=["student_id"]
        )
    ),
    FunctionDeclaration(
        name="get_student_details",
        description="Fetch the student's details (name, teacher, description, added date).",
        parameters=Schema(
            type=Type.OBJECT,
            properties={"student_id": Schema(type=Type.NUMBER)},
            required=["student_id"]
        )
    ),
    FunctionDeclaration(
        name="get_upcoming_tests",
        description="Fetch the upcoming tests for the student.",
        parameters=Schema(
            type=Type.OBJECT,
            properties={"student_id": Schema(type=Type.NUMBER)},
            required=["student_id"]
        )
    ),
    FunctionDeclaration(
        name="personalized_greeting",
        description="Generate a personalized greeting for the student, informing them of upcoming tests and offering assistance.",
        parameters=Schema(
            type=Type.OBJECT,
            properties={"student_id": Schema(type=Type.NUMBER)},
            required=["student_id"]
        )
    )
]