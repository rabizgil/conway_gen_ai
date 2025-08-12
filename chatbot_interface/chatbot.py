from typing import Literal
from pathlib import Path

from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage, RemoveMessage
from langgraph.graph import MessagesState, StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver


SYSTEM_PROMT = """
    You are a helpful and knowledgeable chatbot assistant.
    The chat is primarily about a specific version of Conways Game of Life.
    The version of game takes a word, converts it to a binary ASCII bitmask and uses the mask
    to populate starting condition on a 60x40 grid of cells.
    From the starting condition the game is played on normal rules until stable state.

    Your goal is to provide clear and accurate answers to user requests basing on information they provide.
    Look for words they mark to be passed to the game.
    Stay focused, concise and ensure your responses are relevant to the context of the conversation.
    If you don't have enough information, ask for clarification.
"""

class SummaryState(MessagesState):
    question: str
    answer: str
    summary: str

class Chatbot:

    def __init__(self, reset_memory: bool) -> None:
        self.llm = init_chat_model("openai:gpt-4o-mini")

        self._setup_memory(reset_memory=reset_memory)

        self.config = {"configurable": {"thread_id": 1}}
        self.system_prompt = SystemMessage(content=SYSTEM_PROMT)
        self._build_graph()

    def _build_graph(self) -> StateGraph:
        graph_builder = StateGraph(SummaryState)
        graph_builder.add_node("model", self._model_call)
        graph_builder.add_node("summarize", self._summarize)

        graph_builder.add_edge(START, "model")
        graph_builder.add_conditional_edges("model", self._should_summarize, {"summarize": "summarize", "end": END})
        graph_builder.add_edge("summarize", END)

        return graph_builder

    def _setup_memory(self, reset_memory: bool = False):
        if Path("chatbot_memory.db").exists() and reset_memory:
            Path("chatbot_memory.db").unlink()

    def _model_call(self, state: SummaryState) -> SummaryState:
        summary = state.get("summary", "")

        if summary:
            summary_prompt = SystemMessage(content=f"""
                Summary of conversation:

                {summary}
            """)

            messages = [summary_prompt] + state["messages"]
        else:
            messages = state["messages"]

        question = HumanMessage(content=state.get("question", ""))
        response = self.llm.invoke([self.system_prompt] + messages + [question])

        return SummaryState(
            messages=[question, response],
            question=state.get("question", None),
            answer=response.content,
            summary=state.get("summary", None)
        )

    def _summarize(self, state: SummaryState) -> SummaryState:
        summary = state.get("summary", "")

        if summary:
            summary_prompt = SystemMessage(content=f"""
                Expand the summary below by incorporating the above conversation while preserving context,
                key points and user intent. Rework the summary if needed. Ensure that no critical information
                is lost and the conversation can continue naturally without gaps.
                Keep the summary concise yet informative, removing unnecessary repetition while maintaining clarity.

                Only return the updated summary. Do not add explanations, section headers or extra commentary.

                Existing summary:
                {summary}
            """)
        else:
            summary_prompt = SystemMessage(content=f"""
                Summarize the above conversation while preserving full context, key points and user intent.
                Your response should be concise yet detailed enough to ensure seamless continuation of discussion.
                Avoid redundancy, maintain clarity and retain all necessary details for future exchanges.

                Only return the summarized content. Do not add explanations, section headers or extra commentary.
            """)

        messages = state["messages"] + [summary_prompt]
        response = self.llm.invoke(messages)

        delete_messages = [RemoveMessage(id=msg.id) for msg in state["messages"][:-2]]

        return SummaryState(
            messages=delete_messages,
            question=state.get("question", None),
            answer=state.get("answer", None),
            summary=response.content
        )

    @staticmethod
    def _should_summarize(state: SummaryState) -> Literal["summarize", "end"]:
        messages = state["messages"]
        if len(messages) > 2:
            return "summarize"
        else:
            return "end"

    def stream(self, user_input: SummaryState):
        with SqliteSaver.from_conn_string("chatbot_memory.db") as memory:
            graph = self._build_graph().compile(checkpointer=memory)
            yield graph.stream(user_input, config=self.config, stream_mode="messages")

    def invoke(self, user_input: SummaryState, callables: list):
        config = self.config | {"callbacks": callables}
        with SqliteSaver.from_conn_string("chatbot_memory.db") as memory:
            graph = self._build_graph().compile(checkpointer=memory)
            return graph.invoke(user_input, config=config)
