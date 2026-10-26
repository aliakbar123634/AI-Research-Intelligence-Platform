import os
from dotenv import load_dotenv
from typing import TypedDict
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END

load_dotenv()


class ResearchState(TypedDict):
    question: str
    answer: str


# LLM model
llm = ChatGroq(
    model="openai/gpt-oss-120b",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.2
)


def generate_answer(state: ResearchState):
    response = llm.invoke(
        f"Answer this question clearly and accurately:\n{state['question']}"
    )
    return {"answer": response.content}


# Build workflow
builder = StateGraph(ResearchState)
builder.add_node("generate_answer", generate_answer)
builder.add_edge(START, "generate_answer")
builder.add_edge("generate_answer", END)

research_graph = builder.compile()


def run_llm_workflow(question: str) -> dict:
    return research_graph.invoke({
        "question": question,
        "answer": ""
    })
