import os
from dotenv import load_dotenv
from langsmith import traceable
# from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langchain_google_genai import ChatGoogleGenerativeAI
load_dotenv()


model = ChatGoogleGenerativeAI(model="gemini-2.5-flash",temperature=0.7)
@traceable(name="LLM_Query_for_Assistant")
def query_llm(prompt: str) -> str:
    response = model.invoke(prompt)
    if hasattr(response, "content"):
        return response.content
    if isinstance(response, dict) and "content" in response:
        return response["content"]
    return str(response)