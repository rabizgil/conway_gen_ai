import os

import streamlit as st
from chatbot import Chatbot, SummaryState
from db.db_service import SQLiteService
from langchain_core.messages import AIMessageChunk


def set_env():
    if not os.environ.get("OPENAI_API_KEY"):
        os.environ["OPENAI_API_KEY"] = st.secrets["openai_api_key"]
    if not os.environ.get("UI_DB_URL"):
        os.environ["UI_DB_URL"] = st.secrets["ui_db_url"]


def init_sesion_state():
    if "history" not in st.session_state:
        st.session_state.history = []
    if "login_status" not in st.session_state:
        st.session_state.login_status = True
    if "reset_memory" not in st.session_state:
        st.session_state.reset_memory = True


def render_messages():
    if st.session_state.history:
        for message in st.session_state.history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])


def show_main_page(chatbot: Chatbot):

    with st.sidebar:
        st.title("Conway Game Of Life Pompt Interface")
        st.caption("Powered by gpt-4o-mini")

    with st.chat_message("assistant"):
        st.write("Welcome to the CGOL GenAI interface. Are you ready to play?")

    render_messages()

    user_prompt = st.chat_input("Ask anything")
    if user_prompt:
        st.chat_message("user").write(user_prompt)
        st.session_state.history.append({"role": "user", "content": user_prompt})

        with st.chat_message("assistant"):

            response_placeholder = st.empty()
            full_response = []
            stream = chatbot.stream(SummaryState(messages=[user_prompt]))
            for streamed in stream:
                for chunk, metadata in streamed:
                    if not isinstance(chunk, AIMessageChunk):
                        continue
                    if not metadata["langgraph_node"] == "model":
                        continue
                    full_response.append(chunk.content)
                    response_placeholder.markdown("".join(full_response))
            st.session_state.history.append({"role": "assistant", "content": "".join(full_response)})


def show_login_page(db_service: SQLiteService):
    st.title("Login")
    st.empty()
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if verify_user(username=username, password=password, db_service=db_service):
            st.session_state.login_status = True
            st.rerun()
        else:
            st.error("Invalid username or password. Please try again.")


def verify_user(username: str, password: str, db_service: SQLiteService) -> bool:
    return db_service.validate_user(username=username, password=password)


if __name__ == "__main__":

    set_env()
    init_sesion_state()

    db_service = SQLiteService(os.environ["UI_DB_URL"])

    chatbot = Chatbot(st.session_state.reset_memory)
    if st.session_state.reset_memory:
        st.session_state.reset_memory = False

    if st.session_state.login_status:
        show_main_page(chatbot)
    else:
        show_login_page(db_service=db_service)
