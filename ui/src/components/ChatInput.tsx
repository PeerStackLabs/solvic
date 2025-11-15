import { Send, Paperclip } from 'lucide-react';
import { useState } from 'react';

interface ChatInputProps {
  onSendMessage: (message: string, mode: 'thinking' | 'search') => void;
}

export function ChatInput({ onSendMessage }: ChatInputProps) {
  const [message, setMessage] = useState('');
  const [mode, setMode] = useState<'thinking' | 'search'>('thinking');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim()) {
      onSendMessage(message, mode);
      setMessage('');
    }
  };

  return (
    <div className="w-full max-w-3xl mx-auto px-4">
      <form onSubmit={handleSubmit} className="relative">
        {/* Input Container */}
        <div className="relative bg-[#1a1a1a] rounded-2xl border border-gray-800/50 shadow-2xl hover:border-gray-700/50 transition-all duration-200">
          {/* Mode Toggle Buttons */}
          <div className="flex gap-2 p-3 pb-2">
            <button
              type="button"
              onClick={() => setMode('thinking')}
              className={`flex-1 px-4 py-2 rounded-lg text-sm transition-all duration-200 ${
                mode === 'thinking'
                  ? 'bg-gradient-to-r from-blue-600 to-cyan-500 text-white shadow-lg shadow-blue-500/20'
                  : 'bg-gray-800/30 text-gray-400 hover:bg-gray-800/50 hover:text-gray-300'
              }`}
            >
              <span className="flex items-center justify-center gap-2">
                <svg
                  className="w-4 h-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                  />
                </svg>
                Deep thinking
              </span>
            </button>
            <button
              type="button"
              onClick={() => setMode('search')}
              className={`flex-1 px-4 py-2 rounded-lg text-sm transition-all duration-200 ${
                mode === 'search'
                  ? 'bg-gradient-to-r from-blue-600 to-cyan-500 text-white shadow-lg shadow-blue-500/20'
                  : 'bg-gray-800/30 text-gray-400 hover:bg-gray-800/50 hover:text-gray-300'
              }`}
            >
              <span className="flex items-center justify-center gap-2">
                <svg
                  className="w-4 h-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                  />
                </svg>
                Search
              </span>
            </button>
          </div>

          {/* Text Input Area */}
          <div className="flex items-end gap-3 p-3 pt-2">
            <button
              type="button"
              className="flex-shrink-0 p-2 text-gray-400 hover:text-gray-300 hover:bg-gray-800/30 rounded-lg transition-all duration-200"
            >
              <Paperclip className="w-5 h-5" />
            </button>

            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSubmit(e);
                }
              }}
              placeholder="Message..."
              rows={1}
              className="flex-1 bg-transparent text-gray-100 placeholder-gray-500 outline-none resize-none max-h-32 py-2"
              style={{
                minHeight: '40px',
                height: 'auto',
                overflowY: message.split('\n').length > 3 ? 'auto' : 'hidden'
              }}
            />

            <button
              type="submit"
              disabled={!message.trim()}
              className={`flex-shrink-0 p-3 rounded-xl transition-all duration-200 ${
                message.trim()
                  ? 'bg-gradient-to-r from-blue-600 to-cyan-500 hover:from-blue-700 hover:to-cyan-600 text-white shadow-lg shadow-blue-500/20 hover:shadow-blue-500/40'
                  : 'bg-gray-800/30 text-gray-600 cursor-not-allowed'
              }`}
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Helper Text */}
        <p className="text-center text-gray-600 text-xs mt-3">
          Press Enter to send, Shift + Enter for new line
        </p>
      </form>
    </div>
  );
}
