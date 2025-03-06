from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any
from factcheck.tools import FactCheck, ProvideQuestionsForArticle, ProvideAnswerForArticle

factcheck_router = APIRouter()

@factcheck_router.get("/")
async def documentation():
    """API documentation"""
    return {
        "API Documentation": {
            "factcheck": {
                "description": "Perform fact-checking on a given query",
                "method": "GET",
                "endpoint": "/factcheck",
                "parameters": {
                    "query": "The query to be fact-checked"
                },
                "example": {
                    "url": "/factcheck?query=Is+the+earth+flat"
                },
                "response": {
                    "result": "The fact-checked result"
                }
            },
            "fetch_questions": {
                "description": "Fetch questions based on the provided article URL",
                "method": "GET",
                "endpoint": "/fetch_questions",
                "parameters": {
                    "url": "The URL of the article for which questions are to be fetched"
                },
                "example": {
                    "url": "/fetch_questions?url=https://example.com/article"
                },
                "response": {
                    "result": "List of questions generated for the article",
                    "document": "Serialized document content and metadata"
                }
            },
            "answer_questions": {
                "description": "Provide answers to questions based on a given article URL and input query",
                "method": "GET",
                "endpoint": "/answer_questions",
                "parameters": {
                    "url": "The URL of the article",
                    "query": "The specific question to be answered"
                },
                "example": {
                    "url": "/answer_questions?url=https://example.com/article&query=What+is+the+main+topic"
                },
                "response": {
                    "result": "Answer to the input question"
                }
            }
        }
    }

@factcheck_router.get("/factcheck")
async def factcheck(query: str = Query(..., description="The query to be fact-checked")) -> Dict[str, Any]:
    if not query:
        raise HTTPException(status_code=400, detail="Query parameter is required")
    result = FactCheck(query)
    return {"result": result}

@factcheck_router.get("/fetch_questions")
async def fetch_questions(url: str = Query(..., description="The URL of the article for which questions are to be fetched")) -> Dict[str, Any]:
    if not url:
        raise HTTPException(status_code=400, detail="No URL provided")
    result, document = ProvideQuestionsForArticle(url)
    if not result:
        raise HTTPException(status_code=500, detail="Failed to generate questions")
    return {"result": result, "document": {"page_content": document.page_content, "metadata": document.metadata}}

@factcheck_router.get("/answer_questions")
async def answer_questions(
    url: str = Query(..., description="The URL of the article"),
    query: str = Query(..., description="The specific question to be answered")
) -> Dict[str, Any]:
    if not url or not query:
        raise HTTPException(status_code=400, detail="Both URL and query parameters are required")
    result = ProvideAnswerForArticle(url, query)
    if not result:
        raise HTTPException(status_code=500, detail="Failed to generate an answer")
    return {"result": result}
