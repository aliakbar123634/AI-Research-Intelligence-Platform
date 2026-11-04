from app.tools.web_search_tool import web_search


result = web_search.invoke({
    "query": "Latest developments in AI agents"
})

print(result)