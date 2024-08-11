from langchain_community.document_loaders import PyPDFLoader
from langchain_community.document_loaders import DirectoryLoader
from langchain_community.vectorstores import FAISS
from django.http import request

from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
import json
import re



genai.configure(api_key="AIzaSyDiPRVwLa41RMWxOQZJ0FpjKG8zaUZx2sk")
os.environ["GOOGLE_API_KEY"]="AIzaSyDiPRVwLa41RMWxOQZJ0FpjKG8zaUZx2sk"


# def load_documents():
#     try:
#         loader= DirectoryLoader('./quizapp/Documents', glob="*.pdf", loader_cls=PyPDFLoader)
#         documents=loader.load()
#         return documents
#     except Exception as e:
#         print(f"failed to load document due to exception {e}")

def load_documents(file_path):
    try:
        loader = PyPDFLoader(file_path)
        document = loader.load()
        return document
    except Exception as e:
        print(f"Failed to load document due to exception: {e}")


def get_pdf_text(pdf_docs):
    cleaned_data=""
    try:
        for i in pdf_docs:
            cleaned_data+=re.sub(r'\s+',' ', i.page_content).strip()
            cleaned_data+='\n'
        return cleaned_data
    except Exception as e:
        print(f"failed to clean data due to exception {e}")
        return ""
    
def get_text_chunks(text):
  text_splitter=RecursiveCharacterTextSplitter(
      chunk_size=1000,
      chunk_overlap=200
  )
  chunks=text_splitter.split_text(text)

  return chunks




def get_vector_store(text_chunks):
  embeddings=GoogleGenerativeAIEmbeddings(model="models/embedding-001")
  vector_store=FAISS.from_texts(text_chunks,embedding=embeddings)
  vector_store.save_local("faiss_index")


def user_input(user_question):
    embeddings = GoogleGenerativeAIEmbeddings(model = "models/embedding-001")

    new_db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
    docs = new_db.similarity_search(user_question)

    return (docs,user_question)



def config_model():
    # Create the model
    # See https://ai.google.dev/api/python/google/generativeai/GenerativeModel
    generation_config = {
      "temperature": 1,
      "top_p": 0.95,
      "top_k": 64,
      "max_output_tokens": 8192,
      "response_mime_type": "application/json",
    }
    safety_settings = [
      {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_NONE",
      },
      {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_NONE",
      },
      {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_NONE",
      },
      {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_NONE",
      },
    ]

    

    model1 = genai.GenerativeModel(
      model_name="gemini-1.5-flash",
      safety_settings=safety_settings,
      generation_config=generation_config,
      system_instruction="""You are an AI assistant tasked with generating multiple-choice questions (MCQs with only 4 options) from the provided context. Follow these steps:

    1. Read the provided context carefully.
    2. Generate the specified number of questions based on the context.
    3. Categorize the questions into three difficulty levels: Easy, Medium, and Hard.
    4. Assign marks according to the difficulty levels: 5 marks for Easy, 10 marks for Medium, and 20 marks for Hard.
    5. Format each question in JSON format with the following fields:
        - id: A unique identifier for the question.
        - question: The text of the question.
        - options: A list of ONLY FOUR possible answers.
        - correct_answer: The correct answer from the options.
        - difficulty: The difficulty level (Easy, Medium, or Hard).
        - solution: A detailed explanation of the correct answer.
        - tags: Relevant tags related to the question.
        - marks: The marks assigned based on the difficulty level.
        - status: Initial status (e.g., "initial").

    ### Example:

    Given the following context:
    "Quantum mechanics is a fundamental theory in physics that describes the physical properties of nature at the scale of atoms and subatomic particles. A key principle is the superposition principle, which states that particles can exist in multiple states simultaneously. The Schrödinger Equation is the fundamental equation that describes how the quantum state of a physical system changes with time."

    Generate questions in the following format:

    {
        "questions": [
            {
                "id": 1,
                "question": "In quantum mechanics, what is the principle that states particles can exist in multiple states simultaneously?",
                "options": ["Heisenberg Uncertainty Principle", "Superposition Principle", "Pauli Exclusion Principle", "Schrödinger Equation"],
                "correct_answer": "Superposition Principle",
                "difficulty": "Easy",
                "solution": "The Superposition Principle states that particles can exist in multiple states simultaneously.",
                "tags": ["quantum mechanics"],
                "marks": "5",
                "status": "initial"
            },
            {
                "id": 2,
                "question": "What equation governs the wave function of a quantum mechanical system?",
                "options": ["Newton's Second Law", "Schrödinger Equation", "Maxwell's Equations", "Einstein's Field Equations"],
                "correct_answer": "Schrödinger Equation",
                "difficulty": "Medium",
                "solution": "The Schrödinger Equation governs the wave function of a quantum mechanical system, describing how the quantum state of a physical system changes with time.",
                "tags": ["Schrödinger Equation"],
                "marks": "10",
                "status": "initial"
            },
            {
                "id": 3,
                "question": "What is the degeneracy of the ground state in a three-dimensional harmonic oscillator potential?",
                "options": ["1", "2", "3", "4"],
                "correct_answer": "1",
                "difficulty": "Hard",
                "solution": "In a three-dimensional harmonic oscillator potential, the ground state is non-degenerate, hence its degeneracy is 1.",
                "tags": ["harmonic oscillator"],
                "marks": "20",
                "status": "initial"
            }
        ]
    }"""
    )

    chat_session1 = model1.start_chat(
      history=[
      ]
    )

    return chat_session1



def start_embedding(file_path):
    raw_text=get_pdf_text(load_documents(file_path))
    raw_chunks=get_text_chunks(raw_text)
    get_vector_store(raw_chunks)

def generate_quiz(question):
    R_input=user_input(question)
    content=""
    for i in R_input[0]:
      content+=i.page_content

    model=config_model()
    response1 = model.send_message(content+" for the context provided "+R_input[1])
    return json.loads(response1.text)


def calculate_total_marks(data):
    total_marks = 0
    for question in data["questions"]:
        total_marks += int(question["marks"])
    return total_marks

def count_result_status(data):
    result=[0,0,0]
    for question in data["questions"]:
        if question["answer_given"]=='correct':
            result[0]+=1
        elif question["answer_given"]=='incorrect':
            result[1]+=1
        elif question["answer_given"]=='unattempted':
            result[2]+=1
    return result
