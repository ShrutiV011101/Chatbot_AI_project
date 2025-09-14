

import { AfterViewInit, Component } from '@angular/core';
import { Router } from '@angular/router';
import { HttpClient } from '@angular/common/http';

interface ChatMessage {
  text: string;
  sender: 'user' | 'bot';
  time: string;
}

interface ChatResponse {
  session_id: string;
  reply: string;
}

@Component({
  selector: 'app-widget',
  templateUrl: './widget.component.html',
  styleUrl: './widget.component.scss'
})
export class WidgetComponent{
 
 constructor(private http: HttpClient){
  console.log('Hello! WidgetComponent component has been loaded.');

 }
messages: ChatMessage[] = [
    {
      text: "Hello! I'm your AI assistant. I'm here to help you with any questions or issues you might have. How can I assist you today?",
      sender: 'bot',
      time: '12:55 PM'
    }
  ];

  userInput: string = '';
  sessionId: string | null = null;
  sendMessage() {
    if (!this.userInput.trim()) return;

    const userMessage: ChatMessage = {
      text: this.userInput,
      sender: 'user',
      time: this.getCurrentTime()
    };

    this.messages.push(userMessage);
    const payload: any = {
      user_message: userMessage.text,
      session_id: this.sessionId // send session id if available
    };

    // Call FastAPI backend
    this.http.post<ChatResponse>('http://127.0.0.1:8000/chat', payload).subscribe({
      next: (response) => {
        // Save session id (first time)
        if (!this.sessionId) {
          this.sessionId = response.session_id;
        }

        const botMessage: ChatMessage = {
          text: response.reply,
          sender: 'bot',
          time: this.getCurrentTime()
        };

        this.messages.push(botMessage);
      },
      error: (err) => {
        console.error('Chat API error:', err);
        const botMessage: ChatMessage = {
          text: "Oops! I couldn't reach the server. Please try again later.",
          sender: 'bot',
          time: this.getCurrentTime()
        };
        this.messages.push(botMessage);
      }
    });

    this.userInput = '';
  }

  getCurrentTime(): string {
    return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

}

