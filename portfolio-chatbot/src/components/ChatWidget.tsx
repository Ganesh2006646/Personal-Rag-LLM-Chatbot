import { useState, useRef, useEffect } from 'react';
import { MessageSquare, X, Send, Terminal, Compass, Sparkles, BookOpen } from 'lucide-react';

interface Message {
  id: string;
  sender: 'user' | 'bot';
  text: string;
  citations?: Array<{
    chunk_id: string;
    source: string;
    category: string;
    context_header: string;
  }>;
}

const SUGGESTED_PROMPTS = [
  "What is RiceAgent Pro?",
  "What are your core skills?",
  "Tell me about a time you failed",
  "What is your 5-year career vision?"
];

export default function ChatWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      sender: 'bot',
      text: "Hi, I'm Ganesh's Digital Twin — an AI representation of his knowledge base. Ask me about his projects, skills, background, or engineering philosophy!"
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom of messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSend = async (textToSend: string) => {
    if (!textToSend.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      sender: 'user',
      text: textToSend
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: textToSend }),
      });

      const data = await response.json();
      
      if (response.ok) {
        setMessages(prev => [...prev, {
          id: (Date.now() + 1).toString(),
          sender: 'bot',
          text: data.reply,
          citations: data.citations
        }]);
      } else {
        throw new Error(data.error || 'Failed to communicate with API');
      }
    } catch (err: any) {
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        sender: 'bot',
        text: `Error: ${err.message || 'The server function failed to respond. Make sure you set up your API keys.'}`
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed bottom-6 right-6 z-50 font-sans">
      {/* 1. Floating Orb Trigger */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="group relative flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-tr from-blue-600 to-cyan-500 text-white shadow-[0_0_15px_rgba(6,182,212,0.4)] transition-all hover:scale-110 active:scale-95 duration-300"
        >
          <div className="absolute inset-0 rounded-full bg-cyan-400 opacity-20 blur-md group-hover:opacity-40 transition-opacity"></div>
          <MessageSquare className="h-6 w-6 relative z-10 transition-transform group-hover:rotate-12" />
          <span className="absolute -top-1 -right-1 flex h-3 w-3">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-cyan-500"></span>
          </span>
        </button>
      )}

      {/* 2. Glassmorphic Chat Panel */}
      {isOpen && (
        <div className="flex h-[600px] w-[380px] sm:w-[420px] flex-col rounded-2xl border border-gray-700/50 bg-gray-950/80 backdrop-blur-xl shadow-[0_0_30px_rgba(0,0,0,0.5)] overflow-hidden transition-all duration-300 animate-in fade-in slide-in-from-bottom-6">
          
          {/* Header */}
          <div className="flex items-center justify-between border-b border-gray-800/80 bg-gray-900/50 px-4 py-3">
            <div className="flex items-center gap-3">
              <div className="relative flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-tr from-blue-900 to-cyan-800 border border-cyan-500/30">
                <Terminal className="h-5 w-5 text-cyan-400" />
                <div className="absolute bottom-0 right-0 h-3 w-3 rounded-full bg-green-500 border-2 border-gray-950"></div>
              </div>
              <div>
                <h3 className="text-sm font-semibold text-white tracking-wide">Ganesh's Digital Twin</h3>
                <p className="text-xs text-cyan-400 font-mono flex items-center gap-1">
                  <Sparkles className="h-3 w-3 animate-pulse" /> RAG System v2.0
                </p>
              </div>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="rounded-full p-1.5 text-gray-400 hover:bg-gray-800/60 hover:text-white transition-colors"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4 scrollbar-thin scrollbar-thumb-gray-800">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex flex-col ${msg.sender === 'user' ? 'items-end' : 'items-start'}`}
              >
                <div
                  className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed shadow-sm ${
                    msg.sender === 'user'
                      ? 'bg-blue-600 text-white rounded-br-none'
                      : 'bg-gray-800/60 text-gray-100 border border-gray-700/30 rounded-bl-none'
                  }`}
                >
                  <p className="whitespace-pre-line">{msg.text}</p>
                </div>

                {/* Render Citations if available */}
                {msg.citations && msg.citations.length > 0 && (
                  <div className="mt-1.5 flex flex-wrap gap-1.5 pl-2">
                    {msg.citations.map((cit, idx) => (
                      <span
                        key={idx}
                        className="inline-flex items-center gap-1 text-[10px] font-mono text-cyan-400 bg-cyan-950/40 border border-cyan-800/30 px-2 py-0.5 rounded"
                        title={cit.context_header}
                      >
                        <BookOpen className="h-2.5 w-2.5" />
                        {cit.source.split('/').pop()}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
            
            {/* Loading Indicator */}
            {isLoading && (
              <div className="flex items-start">
                <div className="flex items-center gap-1 bg-gray-800/40 border border-gray-700/20 rounded-2xl px-4 py-3 rounded-bl-none">
                  <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-cyan-400" style={{ animationDelay: '0ms' }}></span>
                  <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-cyan-400" style={{ animationDelay: '150ms' }}></span>
                  <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-cyan-400" style={{ animationDelay: '300ms' }}></span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Quick Prompts */}
          {messages.length === 1 && !isLoading && (
            <div className="px-4 py-2 border-t border-gray-800/40 bg-gray-900/10">
              <p className="text-[11px] text-gray-400 mb-1.5 font-mono flex items-center gap-1">
                <Compass className="h-3 w-3 text-cyan-500" /> SUGGESTED TOPICS:
              </p>
              <div className="grid grid-cols-2 gap-1.5">
                {SUGGESTED_PROMPTS.map((prompt) => (
                  <button
                    key={prompt}
                    onClick={() => handleSend(prompt)}
                    className="text-left text-xs bg-gray-950/60 hover:bg-gray-800/80 border border-gray-800 hover:border-cyan-500/30 rounded-lg p-2 text-gray-300 hover:text-white transition-all duration-200"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Input Box */}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend(input);
            }}
            className="border-t border-gray-800/80 bg-gray-900/30 p-3"
          >
            <div className="flex items-center gap-2 bg-gray-950/80 border border-gray-800 rounded-xl px-3 py-1.5 focus-within:border-cyan-500/50 transition-colors">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask me anything about Ganesh..."
                disabled={isLoading}
                className="flex-1 bg-transparent text-sm text-gray-200 placeholder-gray-500 focus:outline-none disabled:opacity-50"
              />
              <button
                type="submit"
                disabled={!input.trim() || isLoading}
                className="rounded-lg p-1.5 text-cyan-400 hover:bg-cyan-500/10 disabled:opacity-30 transition-all hover:scale-105 active:scale-95"
              >
                <Send className="h-4 w-4" />
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
