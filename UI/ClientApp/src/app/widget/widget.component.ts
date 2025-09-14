

import { AfterViewInit, Component } from '@angular/core';
import { Router } from '@angular/router';

interface ChatMessage {
  text: string;
  sender: 'user' | 'bot';
  time: string;
}

@Component({
  selector: 'app-widget',
  templateUrl: './widget.component.html',
  styleUrl: './widget.component.scss'
})
export class WidgetComponent{
 
 constructor(private router: Router){
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

  sendMessage() {
    if (!this.userInput.trim()) return;

    const userMessage: ChatMessage = {
      text: this.userInput,
      sender: 'user',
      time: this.getCurrentTime()
    };

    this.messages.push(userMessage);
    this.userInput = '';

    // Simulate bot reply
    setTimeout(() => {
      const botMessage: ChatMessage = {
        text: 'Our support team is available 24/7 to help you. You can reach us through this chat, email us at support@example.com, or call our helpline.',
        sender: 'bot',
        time: this.getCurrentTime()
      };
      this.messages.push(botMessage);
    }, 1000);
  }

  getCurrentTime(): string {
    return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

}

