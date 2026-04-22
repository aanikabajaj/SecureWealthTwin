import React, { useState, useRef, useEffect } from 'react';
import { chatAPI } from '../services/api';

const AIChatAdvisor = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [message, setMessage] = useState('');
  const [chatHistory, setChatHistory] = useState([
    { role: 'ai', text: "Hello! I'm your SecureWealth AI Twin. How can I help you today?" }
  ]);
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [chatHistory]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!message.trim() || loading) return;

    const userMsg = message.trim();
    setChatHistory(prev => [...prev, { role: 'user', text: userMsg }]);
    setMessage('');
    setLoading(true);

    try {
      const response = await chatAPI.ask(userMsg);
      setChatHistory(prev => [...prev, { role: 'ai', text: response.data.answer }]);
    } catch (err) {
      setChatHistory(prev => [...prev, { role: 'ai', text: "Sorry, I'm having trouble connecting. Please try again later." }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed bottom-8 right-8 z-[1000] flex flex-col items-end">
      {/* Chat Window */}
      {isOpen && (
        <div className="w-[380px] h-[520px] bg-white rounded-3xl shadow-2xl border border-[#eeeeee] flex flex-col overflow-hidden mb-4 animate-in slide-in-from-bottom-10 fade-in duration-300">
          {/* Header */}
          <div className="bg-[#c8102e] p-5 text-white flex justify-between items-center">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                </svg>
              </div>
              <div>
                <div className="text-[15px] font-bold">SecureWealth AI</div>
                <div className="text-[10px] text-white/70 uppercase tracking-widest font-bold">Digital Twin Active</div>
              </div>
            </div>
            <button onClick={() => setIsOpen(false)} className="hover:bg-white/10 p-2 rounded-full transition-colors">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M18 6L6 18M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Messages */}
          <div ref={scrollRef} className="flex-1 overflow-y-auto p-5 space-y-4 bg-[#fcfcfc]">
            {chatHistory.map((msg, i) => (
              <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[80%] p-4 rounded-2xl text-[13px] leading-relaxed ${
                  msg.role === 'user' 
                    ? 'bg-[#c8102e] text-white rounded-tr-none shadow-md shadow-red-100' 
                    : 'bg-white border border-[#eeeeee] text-[#1a1a1a] rounded-tl-none shadow-sm'
                }`}>
                  {msg.text}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-white border border-[#eeeeee] p-4 rounded-2xl rounded-tl-none flex gap-1.5">
                  <div className="w-1.5 h-1.5 bg-[#c8102e] rounded-full animate-bounce"></div>
                  <div className="w-1.5 h-1.5 bg-[#c8102e] rounded-full animate-bounce delay-100"></div>
                  <div className="w-1.5 h-1.5 bg-[#c8102e] rounded-full animate-bounce delay-200"></div>
                </div>
              </div>
            )}
          </div>

          {/* Input */}
          <form onSubmit={handleSend} className="p-4 bg-white border-t border-[#eeeeee]">
            <div className="relative">
              <input 
                type="text" 
                placeholder="Ask your advisor..." 
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                className="w-full bg-[#f8f9fa] border border-[#eeeeee] rounded-xl py-3 pl-4 pr-12 text-[13px] focus:outline-none focus:border-[#c8102e] transition-colors"
              />
              <button 
                type="submit" 
                disabled={loading}
                className="absolute right-2 top-1.5 p-1.5 bg-[#c8102e] text-white rounded-lg hover:bg-[#a80d26] transition-colors disabled:opacity-50"
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" />
                </svg>
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Toggle Button */}
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className={`w-16 h-16 rounded-full flex items-center justify-center shadow-2xl transition-all duration-300 hover:scale-110 active:scale-95 ${
          isOpen ? 'bg-white text-[#c8102e] border border-[#eeeeee]' : 'bg-[#c8102e] text-white'
        }`}
      >
        {isOpen ? (
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M18 6L6 18M6 6l12 12" />
          </svg>
        ) : (
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
          </svg>
        )}
      </button>
    </div>
  );
};

export default AIChatAdvisor;
