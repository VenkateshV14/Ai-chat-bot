import requests
import json
import traceback
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.shortcuts import render
from .models import ChatSession, ChatMessage

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

@csrf_exempt
def chatbot_response(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_message = data.get("message", "").strip()
            if not user_message:
                return JsonResponse({"error": "Message cannot be empty"}, status=400)

            # Get or create a chat session (using session data)
            session_id = request.session.get("chat_session_id")
            if session_id:
                try:
                    chat_session = ChatSession.objects.get(id=session_id)
                except ChatSession.DoesNotExist:
                    chat_session = ChatSession.objects.create()
                    request.session["chat_session_id"] = chat_session.id
            else:
                chat_session = ChatSession.objects.create()
                request.session["chat_session_id"] = chat_session.id

            # Store the user's message in the DB
            ChatMessage.objects.create(session=chat_session, role="user", content=user_message)

            # Build conversation history from the DB
            conversation = []
            messages = ChatMessage.objects.filter(session=chat_session).order_by("timestamp")
            for m in messages:
                conversation.append({"role": m.role, "content": m.content})

            headers = {
                "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": "gpt-3.5-turbo",  # Change model as needed
                "messages": conversation
            }

            response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload)

            try:
                response_data = response.json()
            except json.JSONDecodeError:
                print("❌ OpenRouter returned invalid JSON:", response.text)
                return JsonResponse({"error": "Invalid response from AI API"}, status=500)

            print("🔍 API Response:", json.dumps(response_data, indent=2))

            if response.status_code == 200 and "choices" in response_data:
                bot_reply = response_data["choices"][0]["message"]["content"]
                # Store bot's reply in the DB
                ChatMessage.objects.create(session=chat_session, role="assistant", content=bot_reply)
                return JsonResponse({"reply": bot_reply})

            return JsonResponse({"error": f"API error: {response.status_code}, {response.text}"}, status=500)

        except Exception as e:
            print("⚠️ Error:", traceback.format_exc())
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=400)


@csrf_exempt
def clear_conversation(request):
    """
    Clears the current conversation. Before clearing, it saves the current session ID in a list of previous sessions.
    """
    if request.method == "POST":
        current_session_id = request.session.get("chat_session_id")
        if current_session_id:
            previous_sessions = request.session.get("previous_chat_sessions", [])
            if current_session_id not in previous_sessions:
                previous_sessions.append(current_session_id)
            request.session["previous_chat_sessions"] = previous_sessions
        # Create a new chat session for a fresh conversation
        new_session = ChatSession.objects.create()
        request.session["chat_session_id"] = new_session.id
        return JsonResponse({"status": "Conversation cleared", "new_session_id": new_session.id})
    return JsonResponse({"error": "Invalid request method"}, status=400)


def get_chat_history(request):
    """
    Returns previous chat history sessions stored for this browser session.
    """
    if request.method == "GET":
        previous_sessions = request.session.get("previous_chat_sessions", [])
        history = []
        for session_id in previous_sessions:
            try:
                chat_session = ChatSession.objects.get(id=session_id)
                messages = ChatMessage.objects.filter(session=chat_session).order_by("timestamp")
                message_list = [
                    {
                        "role": m.role,
                        "content": m.content,
                        "timestamp": m.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                    }
                    for m in messages
                ]
                history.append({
                    "session_id": session_id,
                    "created_at": chat_session.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "messages": message_list
                })
            except ChatSession.DoesNotExist:
                continue
        return JsonResponse({"history": history})
    return JsonResponse({"error": "Invalid request method"}, status=400)


def chat_page(request):
    return render(request, "chatbot/chat.html")

from django.urls import path
from django.shortcuts import render

# Simple view to render the WebSocket chat template
def chat_ws_page(request):
    return render(request, "chatbot/chat_ws.html")

# chatbot/views.py
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from .models import ChatSession, ChatMessage


def export_chat_history(request, session_id):
    try:
        # Ensure that the session belongs to the authenticated user.
        chat_session = ChatSession.objects.get(id=session_id, user=request.user)
    except ChatSession.DoesNotExist:
        return HttpResponse("Session not found", status=404)

    # Retrieve all messages for the session, ordered by time.
    messages = ChatMessage.objects.filter(session=chat_session).order_by("timestamp")
    export_text = f"Chat Session {session_id} (Started: {chat_session.created_at.strftime('%Y-%m-%d %H:%M:%S')})\n\n"
    
    for msg in messages:
        export_text += f"{msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')} - {msg.role.capitalize()}: {msg.content}\n"
    
    # Create the HTTP response with plain text content.
    response = HttpResponse(export_text, content_type="text/plain")
    response["Content-Disposition"] = f"attachment; filename=chat_session_{session_id}.txt"
    return response
