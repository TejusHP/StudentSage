import os
import sys
import django
import google.generativeai as genai
from gemini_tools import *
from firstapp.models import *

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'modelrev2.settings')
django.setup()
from gemini_tools import *

genai.configure(api_key="AIzaSyDM0bMWBOV-mmmG0lgdgiq022YFQa9CtbI")
os.environ["GOOGLE_API_KEY"] = "AIzaSyDM0bMWBOV-mmmG0lgdgiq022YFQa9CtbI"



safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]



model2 = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    tools=tools,
    safety_settings=safety_settings,
    generation_config={
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 64,
        "max_output_tokens": 8192,
        "response_mime_type": "text/plain",
    },
    system_instruction=(
        "You are a helpful assistant who uses ONLY the tools given to you to answer specific questions. "
        "For questions related to a student's academic details, you have the following tools:\n"
        "- 'get_student_tests(student_id)': to fetch the tests assigned to the student.\n"
        "- 'get_student_test_attempts(student_id)': Fetch the test attempts made by the student which includes a list of dictionaries with details such as the test name, obtained marks, total marks, and topics to focus on.\n"
        "- 'get_student_topics(student_id)': to fetch the Weackness topics related to the student.\n"
        "- 'get_student_name(student_id)': to fetch the student's name.\n"
        "- 'get_student_details(student_id)': to fetch the student's details (name, teacher, description, added date).\n"
        "- 'get_upcoming_tests(student_id)': to fetch the upcoming tests for the student.\n"
        "- 'personalized_greeting(student_id)': to generate a personalized greeting for the student, informing them of upcoming tests and offering assistance.\n"
        " -'get_student_answer_details': to Fetch the test submission details of students which is in form of a list of dictionary data. each elelement of list includes details of each question such as question, options, correct_answer, difficulty, solution, tags,total marks of question, and answer_given.\n"
        "- 'make_personalized_quiz(student_id, topic_name)': to create a personalized quiz for the student based on a specific topic. If the topic is not found in the student's weaknesses, it suggests uploading a file instead.\n"
        "REMEMBER THAT YOU ARE CHATTING WITH THE STUDENT"
    ),
)

chat = model2.start_chat(enable_automatic_function_calling=True)



# greeting_message = personalized_greeting(student_id)
def greeting(student_id):
    greeting_message = personalized_greeting(student_id)
    return greeting_message


async def chat_with_me(question):
    user_input = question
    response = chat.send_message(user_input)

    for part in response.parts:
        if fn := part.function_call:
            function_name = fn.name
            args = fn.args

            if function_name == "get_student_tests":
                result = await get_student_tests(args["student_id"])
            elif function_name == "get_student_test_attempts":
                result = await get_student_test_attempts(args["student_id"])
            elif function_name == "get_student_answer_details":
                result = await get_student_answer_details(args["student_id"])
            elif function_name == "get_student_topics":
                result = await get_student_topics(args["student_id"])
            elif function_name == "get_student_name":
                result = await get_student_name(args["student_id"])
            elif function_name == "get_student_details":
                result = await get_student_details(args["student_id"])
            elif function_name == "make_personalized_quiz":
                result = await make_personalized_quiz(args["student_id"],args["topic_name"])
            else:
                result = {"error": f"Unknown function: {function_name}"}

            response_parts = [
                genai.protos.Part(
                    function_response=genai.protos.FunctionResponse(
                        name=function_name,
                        response={"result": result}
                    )
                )
            ]
            response = chat.send_message(response_parts)
    if not response.parts[0].function_call:
        return response.text
