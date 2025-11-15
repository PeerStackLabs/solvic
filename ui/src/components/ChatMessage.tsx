import { User, Sparkles } from 'lucide-react';

interface ChatMessageProps {
  role: 'user' | 'assistant';
  content: string;
  mode?: 'thinking' | 'search';
}

export function ChatMessage({ role, content, mode }: ChatMessageProps) {
  return (
    <div
      className={`flex gap-4 px-6 py-6 ${
        role === 'user' ? 'bg-transparent' : 'bg-[#141414]/50'
      }`}
    >
      <div className="flex-shrink-0">
        {role === 'user' ? (
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center">
            <User className="w-5 h-5 text-white" />
          </div>
        ) : (
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
        )}
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-2">
          <span className="text-gray-200">
            {role === 'user' ? 'You' : 'Assistant'}
          </span>
          {role === 'assistant' && mode && (
            <span className="text-xs text-gray-500 px-2 py-0.5 bg-gray-800/50 rounded-full">
              {mode === 'thinking' ? 'Deep thinking' : 'Search'}
            </span>
          )}
        </div>
        <div className="text-gray-300 whitespace-pre-wrap break-words">
          {content}
        </div>
      </div>
    </div>
  );
}
