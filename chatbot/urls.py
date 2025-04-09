from django.urls import path
from .views import chatbot_response, chat_page, clear_conversation, get_chat_history, chat_ws_page
from .views import export_chat_history

urlpatterns = [
    path("", chat_page, name="chat_page"),  # Redirect root URL to chat page
    path("api/chat/", chatbot_response, name="chatbot_response"),        # Chat API
    path("api/clear_conversation/", clear_conversation, name="clear_conversation"),  # Clear conversation (New Chat)
    path("api/chat_history/", get_chat_history, name="get_chat_history"),    # Retrieve previous chat history
    path("chat_ws/", chat_ws_page, name="chat_ws_page"),
    path("api/export_chat/<int:session_id>/", export_chat_history, name="export_chat_history"),
]