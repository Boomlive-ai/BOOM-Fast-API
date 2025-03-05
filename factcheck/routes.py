# from flask import Blueprint, request, jsonify
# from factcheck.tools import FactCheck, ProvideQuestionsForArticle, ProvideAnswerForArticle

# factcheck_bp = Blueprint('factcheck', __name__)

# # Define a root endpoint that provides documentation
# @factcheck_bp.route('/', methods=['GET'])
# def documentation():
#     doc = {
#         "API Documentation": {
#             "factcheck": {
#                 "description": "Perform fact-checking on a given query",
#                 "method": "GET",
#                 "endpoint": "/factcheck",
#                 "parameters": {
#                     "query": "The query to be fact-checked"
#                 },
#                 "example": {
#                     "url": "/factcheck?query=Is+the+earth+flat"
#                 },
#                 "response": {
#                     "result": "The fact-checked result"
#                 }
#             },
#             "fetch_questions": {
#                 "description": "Fetch questions based on the provided article URL",
#                 "method": "GET",
#                 "endpoint": "/fetch_questions",
#                 "parameters": {
#                     "url": "The URL of the article for which questions are to be fetched"
#                 },
#                 "example": {
#                     "url": "/fetch_questions?url=https://example.com/article"
#                 },
#                 "response": {
#                     "result": "List of questions generated for the article",
#                     "document": "Serialized document content and metadata"
#                 }
#             },
#             "answer_questions": {
#                 "description": "Provide answers to questions based on a given article URL and input query",
#                 "method": "GET",
#                 "endpoint": "/answer_questions",
#                 "parameters": {
#                     "url": "The URL of the article",
#                     "query": "The specific question to be answered"
#                 },
#                 "example": {
#                     "url": "/answer_questions?url=https://example.com/article&query=What+is+the+main+topic"
#                 },
#                 "response": {
#                     "result": "Answer to the input question"
#                 }
#             }
#         }
#     }
#     return jsonify(doc)

# # Define an endpoint to use the function
# @factcheck_bp.route('/factcheck', methods=['GET'])
# def factcheck():
#     query = request.args.get('query')
#     if not query:
#         return jsonify({'error': 'Query parameter is required'}), 400
    
#     result = FactCheck(query)
#     return jsonify({'result': result})

# # Fetch questions
# @factcheck_bp.route('/fetch_questions', methods=['GET'])
# def fetch_questions():
#     url = request.args.get('url')
#     if not url:
#         return jsonify({'error': 'No URL provided'}), 400
    
#     result, document = ProvideQuestionsForArticle(url)
#     if not result:
#         return jsonify({'error': 'Failed to generate questions'}), 500

#     # Serialize the Document object
#     serialized_document = {
#         "page_content": document.page_content,
#         "metadata": document.metadata
#     }

#     return jsonify({'result': result, 'document': serialized_document})

# # Answer questions
# @factcheck_bp.route('/answer_questions', methods=['GET'])
# def answer_questions():
#     # Extract URL and input query from the request parameters
#     url = request.args.get('url')
#     input_query = request.args.get('query')

#     if not url or not input_query:
#         return jsonify({'error': 'Both URL and query parameters are required'}), 400

#     # Call the function to generate answers
#     result = ProvideAnswerForArticle(url, input_query)
#     if not result:
#         return jsonify({'error': 'Failed to generate an answer'}), 500

#     return jsonify({'result': result})



from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict, Any
from pydantic import BaseModel
from factcheck.tools import FactCheck, ProvideQuestionsForArticle, ProvideAnswerForArticle

# Initialize router
factcheck_router = APIRouter()

class DocumentResponse(BaseModel):
    page_content: str
    metadata: Dict[str, Any]

@factcheck_router.get("/")
async def documentation():
    """API Documentation"""
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
                }
            },
            "fetch_questions": {
                "description": "Fetch questions based on the provided article URL",
                "method": "GET",
                "endpoint": "/fetch_questions",
                "parameters": {
                    "url": "The URL of the article for which questions are to be fetched"
                }
            },
            "answer_questions": {
                "description": "Provide answers to questions based on a given article URL and input query",
                "method": "GET",
                "endpoint": "/answer_questions",
                "parameters": {
                    "url": "The URL of the article",
                    "query": "The specific question to be answered"
                }
            }
        }
    }

@factcheck_router.get("/factcheck")
async def factcheck(
    query: str = Query(..., description="The query to fact-check")
):
    try:
        result = FactCheck(query)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@factcheck_router.get("/fetch_questions")
async def fetch_questions(
    url: str = Query(..., description="The URL of the article")
):
    try:
        result, document = ProvideQuestionsForArticle(url)
        if not result:
            raise HTTPException(status_code=500, detail="Failed to generate questions")
        
        serialized_document = {
            "page_content": document.page_content,
            "metadata": document.metadata
        }
        
        return {"result": result, "document": serialized_document}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@factcheck_router.get("/answer_questions")
async def answer_questions(
    url: str = Query(..., description="The URL of the article"),
    query: str = Query(..., description="The question to answer")
):
    try:
        result = ProvideAnswerForArticle(url, query)
        if not result:
            raise HTTPException(status_code=500, detail="Failed to generate an answer")
        
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))