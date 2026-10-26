# `llm_workflow.py` — Code Flow & Connection Notes

## 1. Project ka purpose

Ye file AI Research Workflow handle karti hai.

Iska main kaam:

1. User ka question receive karna.
2. `search_web()` ko call karke web sources lena.
3. Sources ko readable text mein convert karna.
4. Groq LLM ko question aur sources dena.
5. AI-generated answer aur sources return karna.

**Important:** Is file mein web search aur LLM answer generation hai. Database mein save karna is function ka direct kaam nahi hai.

---

## 2. Functions aur components ka connection

### A. `search_web(question)`

**Defined in:** `app.services.web_search_service`

**Called by:** `run_llm_workflow()`

**Input:**
- `question` — user ka research question (`str`).

**Returns:**
- `sources` — web search results ki list, jismein har source ek dictionary hota hai.

Example:

```python
[
    {
        "title": "What is RAG?",
        "url": "https://example.com/rag",
        "content": "RAG retrieves relevant information..."
    }
]
```

**Connection:** `search_web()` ke returned results `run_llm_workflow()` mein `sources` variable ko milte hain.

### B. `run_llm_workflow(question)`

**Purpose:** Poore workflow ko start aur coordinate karta hai.

**Input:**
- `question: str`

**Execution flow:**

1. `search_web(question)` call karta hai.
2. Search results ko `sources` variable mein rakhta hai.
3. `research_graph.invoke(...)` call karta hai.
4. Graph ko `question`, `sources` aur initial empty `answer` deta hai.
5. Graph se generated answer receive karta hai.
6. Final dictionary return karta hai.

**Graph ko di jaane wali state:**

```python
{
    "question": question,
    "sources": sources,
    "answer": ""
}
```

**Final return:**

```python
{
    "question": question,
    "answer": result["answer"],
    "sources": sources
}
```

Yahan `result["answer"]` LangGraph node se generated answer hai.

### C. `ResearchState`

**Purpose:** LangGraph state ka expected structure define karta hai.

```python
class ResearchState(TypedDict):
    question: str
    sources: list[dict]
    answer: str
```

- `question`: user ka question.
- `sources`: web results ki list.
- `answer`: generated answer.

`TypedDict` expected keys aur unki types describe karta hai; ye khud data fetch ya generate nahi karta.

### D. `generate_answer(state)`

**Purpose:** Web sources ko use karke AI answer generate karta hai.

**Called by:** LangGraph node, jab `research_graph.invoke(...)` execute hota hai.

**Input:** Current workflow state.

```python
{
    "question": "...",
    "sources": [...],
    "answer": ""
}
```

**Execution flow:**

1. `source_context = ""` se empty string banata hai.
2. `enumerate(state["sources"], start=1)` har source ko number deta hai.
3. `source.get(...)` se source ka title, URL aur content nikaalta hai.
4. `source_text` mein ek source ka formatted text banata hai.
5. `source_context += source_text + "\n\n"` se sab sources ko ek string mein jorta hai.
6. `prompt` mein user ka question, sources aur AI instructions add karta hai.
7. `llm.invoke(prompt)` se Groq model ko call karta hai.
8. `response.content` se generated text nikaalta hai.

**Return:**

```python
{
    "answer": response.content
}
```

Ye state ka answer field update karta hai. LangGraph is returned update ko existing state ke saath merge karta hai.

### E. `llm = ChatGroq(...)`

**Purpose:** Groq chat model ka object initialize karta hai.

```python
llm = ChatGroq(
    model="openai/gpt-oss-120b",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.2
)
```

- `model`: selected Groq model.
- `api_key`: `.env` se API key.
- `temperature`: response generation setting.

**Called at:** `generate_answer()` ke andar `llm.invoke(prompt)` par.

**Input:** Prompt text.

**Output:** Model response object, jiske `.content` mein generated answer hota hai.

### F. `research_graph`

Graph in components ko connect karta hai:

```python
builder = StateGraph(ResearchState)

builder.add_node("generate_answer", generate_answer)

builder.add_edge(START, "generate_answer")
builder.add_edge("generate_answer", END)

research_graph = builder.compile()
```

- `StateGraph(ResearchState)`: state structure ke saath graph banata hai.
- `add_node(...)`: function ko graph ka node banata hai.
- `START → generate_answer`: workflow ka starting connection.
- `generate_answer → END`: node complete hone ke baad workflow end.
- `compile()`: graph ko executable banata hai.
- `research_graph.invoke(...)`: graph ko state dekar execute karta hai.

**Note:** `search_web()` graph ke bahar call hota hai. Graph ke andar abhi sirf `generate_answer` node hai.

---

## 3. Complete execution flow

```text
User / API
    |
    v
run_llm_workflow(question)
    |
    v
search_web(question)
    |
    v
sources (list of dictionaries)
    |
    v
research_graph.invoke(state)
    |
    v
START
    |
    v
generate_answer(state)
    |
    +--> Format sources into source_context
    |
    +--> Build prompt
    |
    v
llm.invoke(prompt)
    |
    v
response.content
    |
    v
Return {"answer": response.content}
    |
    v
LangGraph final state: result
    |
    v
run_llm_workflow returns:
{
    "question": question,
    "answer": result["answer"],
    "sources": sources
}
```

---

## 4. Variables ka data kahan se aata hai?

| Variable | Value kahan se aati hai? |
|---|---|
| `question` | Function ko caller se milta hai |
| `sources` | `search_web(question)` se |
| `state` | LangGraph ko di gayi input state |
| `i` | `enumerate()` se source number |
| `source` | `state["sources"]` ki current dictionary |
| `source_text` | Current source ko format karke |
| `source_context` | Saare formatted sources ko jor kar |
| `prompt` | Instructions + question + source context |
| `response` | `llm.invoke(prompt)` se |
| `response.content` | AI-generated answer text |
| `result` | `research_graph.invoke(...)` ki final state |

---

## 5. Important concepts

- **Call:** Jab ek function doosre function ko execute karne ke liye use karta hai.
- **Argument:** Function call ke waqt pass ki gayi value, jaise `search_web(question)`.
- **Return:** Function ka caller ko result wapas dena.
- **State:** Workflow mein share hone wala structured data.
- **Node:** LangGraph mein registered function.
- **Edge:** Graph mein execution ka connection.
- **Invoke:** Graph ya model ko input dekar execute karna.
- **Prompt:** Instructions aur data jo LLM ko bheja jata hai.

## 6. Current limitations

1. Search results empty hon to model ke paas source context nahi hoga.
2. Prompt mein `[1]`, `[2]` citations maangi gayi hain, lekin unki correctness automatically verify nahi hoti.
3. `print(source_context)` development debugging ke liye hai; production mein logging use karna behtar hai.
4. Is workflow mein abhi source validation, evaluation, retries aur database persistence implement nahi hain.

**One-line summary:** `run_llm_workflow()` poore process ko coordinate karta hai, `search_web()` sources laata hai, LangGraph `generate_answer()` chalata hai, aur `llm.invoke()` AI answer generate karta hai.
