from django.db import models

class ChatSession(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    # Optionally add a user field if using authentication:
    # user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"ChatSession {self.id} at {self.created_at}"

class ChatMessage(models.Model):
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=20)  # 'user' or 'assistant'
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.role.capitalize()} at {self.timestamp}"