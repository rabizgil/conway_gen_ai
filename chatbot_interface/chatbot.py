from typing import Literal, Any, TypedDict
from pathlib import Path

from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage, RemoveMessage, AnyMessage
from langgraph.graph import MessagesState, StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver
from langmem.short_term import SummarizationNode, RunningSummary, summarize_messages

from chatbot_tools import get_game_result, get_results_for_random_words


SYSTEM_PROMT = """
    You are a helpful and knowledgeable chatbot assistant.
    The chat is primarily about a specific version of Conways Game of Life.
    The version of game takes a word, converts it to a binary ASCII bitmask and uses the mask
    to populate starting condition on a 60x40 grid of cells. The bitmask is centered on the grid and
    reshaped to square-like representation.
    From the starting condition the game is played on normal rules until stable state.

    Your goal is to provide clear and accurate answers to user requests basing on information they provide.
    Look for words they mark to be passed to the game.
    Stay focused, concise and ensure your responses are relevant to the context of the conversation.
    If you don't have enough information, ask for clarification.
"""


class SummaryState(MessagesState):
    summarized_messages: list[AnyMessage]
    context: dict[str, Any]


class Chatbot:

    def __init__(self, reset_memory: bool) -> None:
        self.tools = [get_game_result, get_results_for_random_words]
        # self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, streaming=True)
        self.llm = init_chat_model(model="openai:gpt-4o-mini")

        self.summary_node = SummarizationNode(
            token_counter=self.llm.get_num_tokens_from_messages,
            model=self.llm.bind(max_tokens=128),
            max_tokens=256,
            max_tokens_before_summary=528,
            max_summary_tokens=128
        )

        self._setup_memory(reset_memory=reset_memory)

        self.config = {"configurable": {"thread_id": 1}}
        self.system_prompt = SystemMessage(content=SYSTEM_PROMT)
        self._build_graph()

    def _build_graph(self) -> StateGraph:
        graph_builder = StateGraph(SummaryState)
        graph_builder.add_node("model", self._model_call)

        tool_node = ToolNode(self.tools)
        graph_builder.add_node("tools", tool_node)
        graph_builder.add_node("summarize", self.summary_node)

        graph_builder.set_entry_point("summarize")
        graph_builder.add_edge("summarize", "model")
        graph_builder.add_conditional_edges("model", self._should_continue)
        graph_builder.add_edge("tools", "summarize")
        graph_builder.add_edge("model", END)

        return graph_builder

    def _setup_memory(self, reset_memory: bool = False):
        if Path("chatbot_memory.db").exists() and reset_memory:
            Path("chatbot_memory.db").unlink()

    def _model_call(self, state: SummaryState):
        system_prompt = SystemMessage(content=SYSTEM_PROMT)
        messages = [system_prompt] + state["summarized_messages"]
        response = self.llm.bind_tools(self.tools).invoke(messages)
        return {"messages": [response]}

    @staticmethod
    def _should_continue(state: SummaryState) -> Literal["tools", "__end__"]:
        last_message = state["messages"][-1]
        if not last_message.tool_calls:
            return "__end__"
        else:
            return "tools"

    def stream(self, user_input: SummaryState):
        with SqliteSaver.from_conn_string("chatbot_memory.db") as memory:
            graph = self._build_graph().compile(checkpointer=memory)
            yield graph.stream(user_input, config=self.config, stream_mode="messages")

    def invoke(self, user_input: SummaryState):
        with SqliteSaver.from_conn_string("chatbot_memory.db") as memory:
            graph = self._build_graph().compile(checkpointer=memory)
            return graph.invoke(user_input, config=self.config)
