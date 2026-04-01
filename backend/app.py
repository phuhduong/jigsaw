"""
Jigsaw Backend — Flask server for PCB component analysis.
Uses a 3-agent LangChain pipeline with LangSmith tracing.
"""

import json
import logging
import os
import uuid
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
from dotenv import load_dotenv
from pipeline import stream_component_analysis, get_chat_response

load_dotenv()

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
CORS(app)

PORT = int(os.getenv("PORT", "3001"))

# In-memory conversation state: {queryId: {query, messages, status}}
query_state: dict[str, dict] = {}


def _detect_context_request(text: str) -> bool:
    """Detect if the model is asking for more information."""
    text_lower = text.lower()
    has_question = "?" in text
    short_response = len(text.split()) < 60
    asking_patterns = [
        "what is", "what are", "can you tell", "please provide",
        "could you", "i need", "more information", "additional",
    ]
    matches_pattern = any(p in text_lower for p in asking_patterns)
    return has_question and (matches_pattern or short_response)


@app.route("/mcp/query", methods=["POST"])
def mcp_query():
    """Handle initial chat query."""
    data = request.get_json()
    if not data or "query" not in data:
        return jsonify({"error": "Missing 'query' field"}), 400

    query = data["query"]
    query_id = f"query_{uuid.uuid4().hex[:12]}"

    try:
        response_text = get_chat_response(query)

        query_state[query_id] = {
            "query": query,
            "messages": [
                {"role": "user", "content": query},
                {"role": "assistant", "content": response_text},
            ],
            "status": "active",
        }

        if _detect_context_request(response_text):
            return jsonify({"type": "context_request", "queryId": query_id, "message": response_text}), 200
        return jsonify({"type": "response", "message": response_text}), 200

    except Exception as e:
        app.logger.error(f"Error in /mcp/query: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/mcp/continue", methods=["POST"])
def mcp_continue():
    """Continue conversation with additional context."""
    data = request.get_json()
    if not data or "context" not in data or "queryId" not in data:
        return jsonify({"error": "Missing 'context' or 'queryId' field"}), 400

    context = data["context"]
    query_id = data["queryId"]

    if query_id not in query_state:
        return jsonify({"error": "Query ID not found"}), 404

    state = query_state[query_id]

    try:
        response_text = get_chat_response(context, state["messages"])

        state["messages"].append({"role": "user", "content": context})
        state["messages"].append({"role": "assistant", "content": response_text})

        if _detect_context_request(response_text):
            return jsonify({"type": "context_request", "queryId": query_id, "message": response_text}), 200
        return jsonify({"type": "response", "message": response_text}), 200

    except Exception as e:
        app.logger.error(f"Error in /mcp/continue: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/mcp/component-analysis", methods=["POST"])
def mcp_component_analysis():
    """Stream component analysis via Server-Sent Events."""
    data = request.get_json()
    if not data or "query" not in data:
        return jsonify({"error": "Missing 'query' field"}), 400

    query = data["query"]
    context = data.get("context")

    def generate():
        try:
            for event in stream_component_analysis(query, context):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as e:
            app.logger.error(f"Streaming error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=True)
