import streamlit as st
import llm
import time
import random
import asyncio
import re

st.set_page_config(
    layout="wide",
)

student_id = st.query_params.get("student_id")
student_name = st.query_params.get("student_name")


def gen_respose(res:str):
    for i in res:
        time.sleep(random.randrange(0,3,1)*0.01)
        yield i

async def async_chat_with_me(prompt: str):
    response = await llm.chat_with_me(prompt)
    return response

async def async_greeting(student_id):
    response = await llm.greeting(student_id)
    return response

def find_link(text):
    pattern=re.compile(r'https?://\S+')
    link=pattern.findall(text)
    return link


st.title(f"Welcome, {student_name}")

if "messages" not in st.session_state:
    response = asyncio.run(async_greeting(student_id))
    st.session_state["messages"] = [{"role": "assistant", "content": response}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    response = asyncio.run(async_chat_with_me(prompt+f" my student id is {student_id}"))
    if find_link(response):
        st.chat_message("assistant").write_stream(gen_respose("here is your personalized quiz"))
        st.link_button("Click here",find_link(response)[0])
    else:
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.chat_message("assistant").write_stream(gen_respose(response))

    