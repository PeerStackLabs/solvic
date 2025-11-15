import { useState } from 'react';
import { Menu } from 'lucide-react';
import { ChatSidebar } from './components/ChatSidebar';
import { ChatInput } from './components/ChatInput';
import { ChatMessage } from './components/ChatMessage';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  mode?: 'thinking' | 'search';
}

export default function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);

  const handleSendMessage = (content: string, mode: 'thinking' | 'search') => {
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content
    };

    const assistantMessage: Message = {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: 'This is a demo response. In a real application, this would connect to an AI backend to generate responses.',
      mode
    };

    setMessages((prev) => [...prev, userMessage, assistantMessage]);
  };

  return (
    <div className="flex h-screen bg-[#0a0a0a] text-white overflow-hidden">
      {/* Sidebar */}
      <ChatSidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      {/* Main Content */}
      <main className="flex-1 flex flex-col lg:ml-64">
        {/* Header */}
        <header className="flex items-center justify-between px-4 py-4 border-b border-gray-800/50 lg:hidden">
          <button
            onClick={() => setSidebarOpen(true)}
            className="p-2 hover:bg-gray-800/30 rounded-lg transition-colors"
          >
            <Menu className="w-6 h-6 text-gray-400" />
          </button>
          <h1 className="text-transparent bg-clip-text bg-gradient-to-r from-blue-500 to-cyan-400">
            DeepSeek
          </h1>
          <div className="w-10" /> {/* Spacer for centering */}
        </header>

        {/* Chat Area */}
        <div className="flex-1 overflow-y-auto">
          {messages.length === 0 ? (
            /* Empty State */
            <div className="h-full flex flex-col items-center justify-center px-4">
              <div className="text-center space-y-8 max-w-2xl mb-12">
                {/* Logo/Icon */}
                <div className="flex justify-center mb-6">
                  <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-600 to-cyan-500 flex items-center justify-center shadow-2xl shadow-blue-500/20">
                    <svg
                      className="w-10 h-10 text-white"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={1.5}
                        d="M13 10V3L4 14h7v7l9-11h-7z"
                      />
                    </svg>
                  </div>
                </div>

                {/* Main Heading */}
                <h1 className="text-4xl md:text-5xl lg:text-6xl text-transparent bg-clip-text bg-gradient-to-r from-gray-100 to-gray-300 tracking-tight">
                  How can I help you?
                </h1>

                {/* Suggested Prompts */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-8">
                  {[
                    {
                      icon: (
                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                        </svg>
                      ),
                      text: 'Explain a complex concept'
                    },
                    {
                      icon: (
                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
                        </svg>
                      ),
                      text: 'Write some code'
                    },
                    {
                      icon: (
                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                      ),
                      text: 'Analyze some text'
                    },
                    {
                      icon: (
                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                        </svg>
                      ),
                      text: 'Research a topic'
                    }
                  ].map((prompt, index) => (
                    <button
                      key={index}
                      className="flex items-center gap-3 p-4 bg-[#1a1a1a] hover:bg-[#222] border border-gray-800/50 hover:border-gray-700/50 rounded-xl transition-all duration-200 text-left group"
                    >
                      <div className="text-gray-400 group-hover:text-blue-400 transition-colors">
                        {prompt.icon}
                      </div>
                      <span className="text-gray-300 text-sm">{prompt.text}</span>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            /* Messages */
            <div className="max-w-4xl mx-auto w-full">
              {messages.map((message) => (
                <ChatMessage
                  key={message.id}
                  role={message.role}
                  content={message.content}
                  mode={message.mode}
                />
              ))}
            </div>
          )}
        </div>

        {/* Input Area */}
        <div className="border-t border-gray-800/50 py-6 px-4">
          <ChatInput onSendMessage={handleSendMessage} />
        </div>
      </main>
    </div>
  );
}
