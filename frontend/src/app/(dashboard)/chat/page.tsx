"use client";

import { useState } from "react";
import { Send, Paperclip, Bot, User, FileText } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

// Note: Ensure @/components/ui/* are created
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Card } from "@/components/ui/card";

export default function ChatPage() {
  const [messages, setMessages] = useState([
    { id: 1, role: 'assistant', content: "Hello! I'm your Enterprise Knowledge Assistant. How can I help you today?", citations: [] },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSend = () => {
    if (!input.trim()) return;
    const userMsg = { id: Date.now(), role: 'user', content: input, citations: [] };
    setMessages(prev => [...prev, userMsg]);
    setInput("");
    setIsLoading(true);

    // Simulate response
    setTimeout(() => {
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        role: 'assistant',
        content: "Based on the documents, here is what I found. \n\n* **SSO Integration** is supported via SAML 2.0.\n* You can configure it in the `Settings > Security` tab.",
        citations: [{ id: 'c1', title: 'Admin Guide.pdf', page: 14 }]
      }]);
      setIsLoading(false);
    }, 1500);
  };

  return (
    <div className="h-full flex flex-col md:flex-row gap-6">
      {/* Sidebar - Conversation History */}
      <Card className="w-full md:w-64 flex-shrink-0 hidden md:flex flex-col h-[calc(100vh-8rem)]">
        <div className="p-4 border-b">
          <Button className="w-full">New Chat</Button>
        </div>
        <ScrollArea className="flex-1">
          <div className="p-2 space-y-1">
            <div className="px-3 py-2 text-sm bg-muted rounded-md font-medium cursor-pointer">
              SSO Integration Help
            </div>
            <div className="px-3 py-2 text-sm text-muted-foreground hover:bg-muted/50 rounded-md cursor-pointer">
              Q3 Financial Summary
            </div>
          </div>
        </ScrollArea>
      </Card>

      {/* Main Chat Area */}
      <Card className="flex-1 flex flex-col h-[calc(100vh-8rem)] overflow-hidden">
        <ScrollArea className="flex-1 p-4">
          <div className="space-y-6 max-w-3xl mx-auto">
            {messages.map((msg) => (
              <div key={msg.id} className={`flex gap-4 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                {msg.role === 'assistant' && (
                  <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center flex-shrink-0 text-primary-foreground">
                    <Bot size={18} />
                  </div>
                )}
                
                <div className={`flex flex-col gap-2 max-w-[80%] ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                  <div className={`p-4 rounded-xl ${msg.role === 'user' ? 'bg-primary text-primary-foreground' : 'bg-muted/50 border'}`}>
                    {msg.role === 'user' ? (
                      <p className="whitespace-pre-wrap">{msg.content}</p>
                    ) : (
                      <div className="prose prose-sm dark:prose-invert max-w-none">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                          {msg.content}
                        </ReactMarkdown>
                      </div>
                    )}
                  </div>
                  
                  {msg.citations && msg.citations.length > 0 && (
                    <div className="flex gap-2 flex-wrap mt-1">
                      {msg.citations.map((c: any) => (
                        <div key={c.id} className="flex items-center gap-1 text-xs bg-muted border px-2 py-1 rounded-md cursor-pointer hover:bg-muted/80">
                          <FileText size={12} />
                          <span>{c.title}</span>
                          <span className="text-muted-foreground">p.{c.page}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {msg.role === 'user' && (
                  <div className="w-8 h-8 rounded-full bg-secondary flex items-center justify-center flex-shrink-0">
                    <User size={18} />
                  </div>
                )}
              </div>
            ))}
            {isLoading && (
              <div className="flex gap-4">
                <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-primary-foreground">
                  <Bot size={18} />
                </div>
                <div className="p-4 rounded-xl bg-muted/50 border flex items-center gap-2">
                  <div className="w-2 h-2 bg-foreground/30 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                  <div className="w-2 h-2 bg-foreground/30 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                  <div className="w-2 h-2 bg-foreground/30 rounded-full animate-bounce"></div>
                </div>
              </div>
            )}
          </div>
        </ScrollArea>

        <div className="p-4 border-t bg-card">
          <div className="max-w-3xl mx-auto flex gap-2">
            <Button variant="outline" size="icon" className="flex-shrink-0">
              <Paperclip size={18} />
            </Button>
            <Input 
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask anything about your knowledge base..."
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              className="flex-1"
            />
            <Button onClick={handleSend} disabled={!input.trim() || isLoading} className="flex-shrink-0">
              <Send size={18} />
            </Button>
          </div>
          <p className="text-center text-xs text-muted-foreground mt-2">
            AI can make mistakes. Consider verifying important information.
          </p>
        </div>
      </Card>
    </div>
  );
}
