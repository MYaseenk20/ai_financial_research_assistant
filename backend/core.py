from datetime import datetime

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langgraph.constants import START, END
from langgraph.graph import StateGraph

load_dotenv()
import os
from typing import TypedDict

from langchain_tavily import TavilySearch
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI

from langchain_google_genai import GoogleGenerativeAIEmbeddings

FAISS_INDEX_PATH = r"..\docs\faiss_index"

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    project=os.getenv("GOOGLE_PROJECT_ID"),
    location=os.getenv("GOOGLE_LOCATION")
)

embeddings = GoogleGenerativeAIEmbeddings(
    model="text-embedding-005",
    project=os.getenv("GOOGLE_PROJECT_ID"),
    location=os.getenv("GOOGLE_LOCATION")
)

search_tool    = TavilySearch(max_results=3)

class AgentState(TypedDict):
    query: str
    company:str
    research_result: str
    rag_result: str
    risk_result: str
    final_result: str
    next:str          # supervisor routing decision


def supervisor_node(state: AgentState) -> AgentState:
    """Decides which agent to run next based on what's missing."""

    if not state.get("research_result"):
        print("  → routing to: research")
        return {**state,"next":"research"}

    if not state.get("rag_result"):
        print("  → routing to: Rag")
        return {**state,"next":"rag"}

    if not state.get("risk_result"):
        print("  → routing to: risk")
        return {**state,"next":"risk"}

    print("  → routing to: writer")
    return{**state,"next":"writer"}

def research_node(state: AgentState) -> AgentState:
    """Searches the web for latest news & financials."""
    print("\n🔍 [Research Agent] Searching the web...")

    company = state["company"]
    results = search_tool.invoke(f"{company} stock financial analysis")

    prompt = ChatPromptTemplate.from_template("""
    You are a financial research analyst.
    Summarise the following web search results about {company} for an investment analysis.
    Focus on: recent performance, revenue, growth trends, and market position.

    Search Results:
    {results}

    Provide a concise 3-4 paragraph summary.
    """)

    chain = prompt | llm

    summary = chain.invoke({"company":company,"results": str(results)})

    print("  ✅ Research complete.")

    return {**state,"research_result":summary.content}

def rag_node(state: AgentState) -> AgentState:
    """Load existing FAISS index if it exists, otherwise create it"""
    company = state["company"]
    query = f"{company} revenue earnings financial performance risks"

    if os.path.exists(FAISS_INDEX_PATH):
        print("*** Loading existing FAISS index ***")
        vector_store = FAISS.load_local(FAISS_INDEX_PATH,embeddings,allow_dangerous_deserialization=True)
        retriever  = vector_store.as_retriever(
                    search_type="similarity", search_kwargs={"k": 4}
                )

        docs = retriever.invoke(query)

        if docs:
            context = "\n\n".join(d.page_content for d in docs)
        else:
            context = f"No documents found. Using LLM knowledge for {company}."
    else:
        # ← THIS was missing — context was undefined if index didn't exist
        print("*** No FAISS index found, using LLM knowledge only ***")
        context = f"No financial documents available. Using general knowledge for {company}."

    prompt = ChatPromptTemplate.from_template("""
    You are a financial document analyst.
    Based on the following context from official financial documents about {company},
    provide key insights on: revenue, profit margins, debt levels, and future guidance.
    
    Context:
    {context}
    
    Provide a structured 3-4 paragraph analysis.
    """)

    chain = prompt | llm

    summary = chain.invoke({"company":company,"context": context})
    print("  ✅ RAG retrieval complete.")
    return {**state,"rag_result":summary.content}

def risk_node(state: AgentState) -> AgentState:
    """Evaluates investment risks based on collected data."""
    print("\n⚠️  [Risk Agent] Evaluating risks...")

    prompt = ChatPromptTemplate.from_template("""
    You are a risk analyst for investment research.
    Based on the research and document data below, identify the TOP 5 investment risks
    for {company}. Consider: market risks, competitive risks, regulatory risks,
    macroeconomic risks, and company-specific risks.

    Research Data:
    {research}

    Document Data:
    {rag}

    Format your response as a numbered list with brief explanations for each risk.
    """)

    chain = prompt | llm

    risks   = chain.invoke({
        "company":  state["company"],
        "research": state["research_result"],
        "rag":      state["rag_result"],
    })

    print("  ✅ Risk assessment complete.")
    return {**state, "risk_result": risks.content}

def writer_node(state: AgentState) -> AgentState:
    """Synthesises all agent outputs into a final investment brief."""
    print("\n📝 [Writer Agent] Generating final report...")
    current_date = datetime.now().strftime("%B %d, %Y")
    prompt = ChatPromptTemplate.from_template("""
You are a senior investment analyst. Write a professional investment brief.

Date: {date}
Company: {company}

Use the following research, document analysis, and risk assessment.

## Web Research:
{research}

## Document Analysis (10-K / Annual Report):
{rag}

## Risk Assessment:
{risks}

---
Write a structured investment brief with these sections:
1. Executive Summary
2. Company Overview & Recent Performance
3. Financial Highlights
4. Key Risks
5. Investment Verdict (Buy / Hold / Sell with reasoning)

Keep the tone professional and concise.
Noted:
Today's date is {date}. Use this exact date in the report header
""")
    chain  = prompt | llm
    report = chain.invoke({
        "company":  state["company"],
        "research": state["research_result"],
        "rag":      state["rag_result"],
        "risks":    state["risk_result"],
        "date": current_date
    })

    print("  ✅ Report complete.")
    return {**state, "final_result": report.content}

def route_supervisor(state: AgentState) -> str:
    return state["next"]


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("supervisor", supervisor_node)
    graph.add_node("research", research_node)
    graph.add_node("rag", rag_node)
    graph.add_node("risk", risk_node)
    graph.add_node("writer", writer_node)

    graph.add_edge(START,"supervisor")
    graph.add_conditional_edges("supervisor",route_supervisor,{
        "research": "research",
        "rag": "rag",
        "risk": "risk",
        "writer": "writer",
    })
    graph.add_edge("research", "supervisor")
    graph.add_edge("rag", "supervisor")
    graph.add_edge("risk", "supervisor")
    graph.add_edge("writer", END)

    print(graph.compile().get_graph().draw_mermaid())

    return graph.compile()

if __name__ == '__main__':
    app = build_graph()

    # Initial state
    initial_state: AgentState = {
        "query": "Analyze Apple for investment",
        "company": "Apple",
        "research_result": "",
        "rag_result": "",
        "risk_result": "",
        "final_result": "",
        "next": "",
    }

    print("=" * 60)
    print("  💼 AI Financial Research Assistant")
    print("=" * 60)

    final_state = app.invoke(initial_state)

    print("\n" + "=" * 60)
    print("  📊 FINAL INVESTMENT BRIEF")
    print("=" * 60)
    print(final_state["final_result"])