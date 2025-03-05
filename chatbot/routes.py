# from flask import Blueprint, request, jsonify
# from chatbot.bot import Chatbot
# from chatbot.utils import extract_sources_and_result, prioritize_sources
# from langchain_core.messages import HumanMessage
# from chatbot.tools import fetch_questions_on_latest_articles_in_Boomlive, fetch_articles_based_on_articletype
# from chatbot.vectorstore import StoreCustomRangeArticles, StoreDailyArticles
# chatbot_bp = Blueprint('chatbot', __name__)
# mybot = Chatbot()
# workflow = mybot()




# @chatbot_bp.route('/')
# def api_overview():
#     """
#     This route provides a basic overview of available API routes.
#     """
#     routes = {
#         "GET /query": "Query the chatbot with a question (requires 'question' and 'thread_id' parameters).",
#         "POST /store_articles": "Store articles for a custom date range (requires 'from_date' and 'to_date' in the body).",
#         "POST /store_daily_articles": "Store articles for the current day.",
#         "GET /generate_questions": "Fetch latest articles and generate questions from Boomlive.",
#         "GET /fetch_articles": "Fetch articles of specific article type (requires 'articleType' parameter)."
#     }
#     return jsonify(routes), 200




# @chatbot_bp.route('/query', methods=['GET'])
# def query_bot():
#     question = request.args.get('question')
#     thread_id = request.args.get('thread_id')
#     sources = []
#     if not question or not thread_id:
#         return jsonify({"error": "Missing required parameters"}), 400

#     input_data = {"messages": [HumanMessage(content=question)]}
#     try:
#         response = workflow.invoke(input_data, config={"configurable": {"thread_id": thread_id}})
#         result = response['messages'][-1].content
#         print("response['messages'][-1]",result)
#         result,raw_sources  = extract_sources_and_result(result)

#         sources = prioritize_sources(question, raw_sources)
#         if not result:
#             result = "No response generated. Please try again."
#         return jsonify({"response": result, "sources": sources})
#     except Exception as e:
#         print(f"Error in query_bot: {str(e)}")
#         return jsonify({"error": str(e)}), 500




# # Route for Storing Articles with Custom Date Range
# @chatbot_bp.route('/store_articles', methods=['POST'])
# async def store_articles():
#     """
#     Store articles for a custom date range.
#     Query Parameters:
#         - from_date (str): Start date in 'YYYY-MM-DD' format.
#         - to_date (str): End date in 'YYYY-MM-DD' format.
#     """
#     # Extract dates from JSON payload
#     data = request.get_json()
#     from_date = data.get('from_date')
#     to_date = data.get('to_date')

#     # Validate input
#     if not from_date or not to_date:
#         return jsonify({"error": "Missing 'from_date' or 'to_date' in request body"}), 400

#     # Instantiate and invoke the StoreCustomRangeArticles class
#     try:
#         store_articles_handler = StoreCustomRangeArticles()
#         result = await store_articles_handler.invoke(from_date=from_date, to_date=to_date)
#         return jsonify(result)
#     except Exception as e:
#         print(f"Error in store_articles: {str(e)}")
#         return jsonify({"error": str(e)}), 500

# @chatbot_bp.route('/store_daily_articles', methods=['POST'])
# async def store_daily_articles_route():
#     """
#     Async route to fetch and store daily articles.
#     """
#     try:
#         # Instantiate the handler class
#         store_articles_handler = StoreDailyArticles()
        
#         # Invoke the class method
#         result = await store_articles_handler.invoke()
        
#         # Return JSON response
#         return jsonify(result)
#     except Exception as e:
#         print(f"Error in /store_daily_articles: {str(e)}")
#         return jsonify({"status": "error", "message": str(e)}), 500
    


# @chatbot_bp.route('/generate_questions', methods=['GET'])
# def generate_questions_route():
#     """
#     Route to fetch articles and generate questions using imported functions.
#     """
#     try:
#         # Call the imported function to fetch and generate questions
#         results = fetch_questions_on_latest_articles_in_Boomlive()
#         return jsonify(results), 200
#     except Exception as e:
#         return jsonify({"error": f"An error occurred: {str(e)}"}), 500
    



# @chatbot_bp.route('/fetch_articles', methods=['GET'])
# def fetch_articles():
#     """
#     Route to fetch articles of specific article type.
#     """
#     articleType = request.args.get('articleType')
#     try:
#         # Call the imported function to fetch and generate questions
#         results = fetch_articles_based_on_articletype(articleType)
#         return jsonify(results), 200
#     except Exception as e:
#         return jsonify({"error": f"An error occurred: {str(e)}"}), 500

import os, json, re
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict, Any
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessageChunk, AIMessage
from chatbot.bot import Chatbot
from chatbot.utils import extract_sources_and_result, prioritize_sources
from chatbot.tools import fetch_questions_on_latest_articles_in_Boomlive, fetch_articles_based_on_articletype
from chatbot.vectorstore import StoreCustomRangeArticles, StoreDailyArticles
from fastapi.responses import StreamingResponse

# Initialize router
chatbot_router = APIRouter()

# Initialize chatbot
mybot = Chatbot()
workflow = mybot()

# Pydantic models for request validation
class DateRangeRequest(BaseModel):
    from_date: str
    to_date: str

@chatbot_router.get("/")
async def api_overview():
    """API route overview"""
    return {
        "routes": {
            "GET /query": "Query the chatbot with a question (requires 'question' and 'thread_id' parameters).",
            "POST /store_articles": "Store articles for a custom date range (requires 'from_date' and 'to_date' in the body).",
            "POST /store_daily_articles": "Store articles for the current day.",
            "GET /generate_questions": "Fetch latest articles and generate questions from Boomlive.",
            "GET /fetch_articles": "Fetch articles of specific article type (requires 'articleType' parameter)."
        }
    }



 
    
@chatbot_router.get("/stream_query")
async def stream_query_bot(question: str, thread_id: str):
    if not question or not thread_id:
        raise HTTPException(status_code=400, detail="Missing required parameters.")
    
    input_data = {"messages": [HumanMessage(content=question)]}

    async def stream_chunks():
        sources = []
        cnt = 0
        response_collected = ""  # Store full response to check if "Not Found" is in it
        found_not_found = False  # Track if "Not Found" was ever present
        use_cnt_3_res = True
        use_cnt_4_res = True
        use_cnt_5_res = True
        try:
            async for event in workflow.astream_events(input_data, config={"configurable": {"thread_id": thread_id}}, version="v2"):
                kind = event["event"]

                print(f"{kind}: {event["name"]}")
                if event["event"] == "on_chat_model_start":
                    cnt = cnt + 1
                    print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
                    print(f"COUNT: {cnt}")
                    print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")

                if event["event"]=="on_chat_model_end":
                    # print(event["data"])
                    pass

                if event["event"]=="on_retriever_end":
                    print("*************************************************************************")
                    # print(event["data"])  # Debug print to check the data structure

                    # Extract sources from the "output" field
                    output = event["data"].get("output", [])
                    if isinstance(output, list):  # Ensure the output is a list
                        sources.extend(
                            [doc.metadata.get("source") for doc in output if doc.metadata.get("source")]
                        )  # Print the extracted sources
                       
           
                if event["event"] == "on_chat_model_stream" and cnt==3 and use_cnt_3_res:
                    chunk = event["data"]["chunk"]
                    # print(chunk.content, end="|", flush=True)
                    # print(chunk)
                    if isinstance(chunk, AIMessageChunk):
                        # print(chunk)
                        match = re.search(r"content='([^']+)'", str(chunk))
                        if match:
                            content = match.group(1)
                            response_collected += content  # Collect the full response
                            print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
                            print("response_collected",event["name"])
                            print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
                            if response_collected=="1":
                                use_cnt_3_res = False
                                response_collected=""
                                content=""
                            if response_collected=="Not":
                                found_not_found = True
                                break
                            
                            if "Not Found" in response_collected:
                                found_not_found = True
                                break
                            content = content.replace('\n', '<br>')
                            content = content.replace('.\n\n', '.<br><br>')
                            if content is not "":
                                yield f"data: {content}\n\n"  # Format for SSE

                    else:
                        yield "data: Invalid chunk type\n\n"

                print("found_not_found",found_not_found)
                if event["event"] == "on_chat_model_stream" and cnt==4 and found_not_found==False and use_cnt_4_res:
                    chunk = event["data"]["chunk"]
                    print(chunk.content, end="|", flush=True)
                  
                    if isinstance(chunk, AIMessageChunk):
                        # print(chunk)
                        match = re.search(r"content='([^']+)'", str(chunk))
                        if match:
                            content = match.group(1)
                            response_collected += content  # Collect the full response
                            print("#############################response_collected in count 4################################")
                            print(response_collected)
                            print("##############################response_collected################################")
                            if response_collected=="1from" or response_collected=="from":
                                use_cnt_4_res = False
                                content=""
                            if response_collected=="Not" or response_collected=="1Not":
                                found_not_found = True
                                content=""
                                break
                            
                            if "Not Found" in response_collected:
                                found_not_found = True
                                content=""
                                break
                            # use_cnt_5_res = False
                            # content = content.replace('\n', '<br>')
                            # content = content.replace('.\n\n', '.<br><br>')
                            yield f"data: {content}\n\n"  # Format for SSE

                    else:
                        yield "data: Invalid chunk type\n\n"
                print("for count 5",cnt,found_not_found, use_cnt_5_res ,event["event"] == "on_chat_model_stream" and cnt==5 and found_not_found==False and use_cnt_5_res)
                if event["event"] == "on_chat_model_stream" and cnt==5 and found_not_found==False and use_cnt_5_res:

                    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!1")
                    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!1")
                    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!1")
                    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!1")
                    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!1")
                    print("Hyachya AAT Yetay")
                    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!1")
                    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!1")
                    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!1")
                    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!1")
                    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!1")
                    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!1")

                    chunk = event["data"]["chunk"]
                    print(chunk.content, end="|", flush=True)
                  
                    if isinstance(chunk, AIMessageChunk):
                        # print(chunk)
                        match = re.search(r"content='([^']+)'", str(chunk))
                        if match:
                            content = match.group(1)
                            response_collected += content  # Collect the full response
                            print("#############################response_collected in count 5################################")
                            print(content)
                            print("##############################response_collected################################")
                            if response_collected=="Not":
                                found_not_found = True
                                break
                            
                            if "Not Found" in response_collected:
                                found_not_found = True
                                break
                            
                            if content!="Verified":
                                yield f"data: {content}\n\n"  # Format for SSE

                            # content = content.replace('\n', '<br>')
                            # content = content.replace('.\n\n', '.<br><br>')

                    else:
                        yield "data: Invalid chunk type\n\n"

                if event["event"] == "on_chain_end" and cnt == 3:
                    # Ensure event["data"] is a dictionary
                    data = event["data"]
                    if isinstance(data, str):  # If it's a string, parse it
                        data = json.loads(data)

                    print(data)  # Debugging output

                    output = data.get("output", {})
                    messages = output.get("messages", [])

                    print("Messages:", messages)  # Debugging output

                    # Extract AIMessage
                    ai_messages = [msg for msg in messages if isinstance(msg, AIMessage)]
                    print("AI Messages:", ai_messages)  # Debugging output

                    # Extract content and sources
                    for msg in ai_messages:
                        content = msg.content
                        sources = msg.sources  # Extract sources safely

                        print("Content:", content)
                        print("Sources:", sources)
                    yield f"data: {content}\n\n"  # Format for SSE

                    
        except Exception as e:
            # yield f"data: Error in query_bot: {str(e)}\n\n"
            pass
        finally:
        # Send the end marker when the stream finishes

            if found_not_found:
                    yield "data: Not Found\n\n"
                    # pass

            
            elif sources:
                unique_sources = list(set(sources))  

                prioritized_sources  = prioritize_sources(question,unique_sources,response_collected)
                print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
                print("QUESTION", question)
                print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
                print("SOURCES", prioritized_sources)
                print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")

                yield f"data: {json.dumps({'sources': prioritized_sources})}\n\n"
            print("(((((((((((((((((((((((((((((((())))))))))))))))))))))))))))))))")
            print(response_collected, len(response_collected))
            print("(((((((((((((((((((((((((((((((((((())))))))))))))))))))))))))))))))))))")
            # if response_collected=="1" and len(response_collected)==1:
            #     yield "data: Not Found\n\n"

            yield "data: [end]\n\n"

    return StreamingResponse(
        stream_chunks(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )



@chatbot_router.get("/query")
async def query_bot(
    question: str = Query(..., description="The question to ask the chatbot"),
    thread_id: str = Query(..., description="Thread ID for conversation context")
):
    sources = []
    input_data = {"messages": [HumanMessage(content=question)]}
    
    try:
        async for event in workflow.astream_events(input_data, config={"configurable": {"thread_id": thread_id}}, version="v2"):
                print(event["event"])
        response = workflow.invoke(input_data, config={"configurable": {"thread_id": thread_id}})
        result = response['messages'][-1].content
        result, raw_sources = extract_sources_and_result(result)
        sources = prioritize_sources(question, raw_sources, result)
        
        if not result:
            result = "No response generated. Please try again."
        
        return {"response": result, "sources": sources}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@chatbot_router.post("/store_articles")
async def store_articles(request: DateRangeRequest):
    try:
        store_articles_handler = StoreCustomRangeArticles()
        result = await store_articles_handler.invoke(
            from_date=request.from_date,
            to_date=request.to_date
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@chatbot_router.post("/store_daily_articles")
async def store_daily_articles():
    try:
        store_articles_handler = StoreDailyArticles()
        result = await store_articles_handler.invoke()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@chatbot_router.get("/generate_questions")
async def generate_questions():
    try:
        results = fetch_questions_on_latest_articles_in_Boomlive()
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@chatbot_router.get("/fetch_articles")
async def fetch_articles(
    articleType: str = Query(..., description="Type of articles to fetch")
):
    try:
        results = fetch_articles_based_on_articletype(articleType)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))