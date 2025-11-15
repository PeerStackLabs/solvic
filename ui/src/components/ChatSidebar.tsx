import { Plus, MessageSquare, User, Menu, X } from 'lucide-react';
import { useState } from 'react';

interface ChatItem {
  id: string;
  title: string;
  timestamp: string;
  preview: string;
}

interface ChatSidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export function ChatSidebar({ isOpen, onClose }: ChatSidebarProps) {
  const [activeChat, setActiveChat] = useState<string | null>(null);

  const chatHistory: ChatItem[] = [
    {
      id: '1',
      title: 'Explain quantum computing',
      timestamp: 'Today',
      preview: 'Can you explain quantum computing in simple terms?'
    },
    {
      id: '2',
      title: 'React best practices',
      timestamp: 'Today',
      preview: 'What are the best practices for React development?'
    },
    {
      id: '3',
      title: 'API integration guide',
      timestamp: 'Yesterday',
      preview: 'How do I integrate a REST API with my frontend?'
    },
    {
      id: '4',
      title: 'TypeScript generics',
      timestamp: 'Yesterday',
      preview: 'Explain TypeScript generics with examples'
    },
    {
      id: '5',
      title: 'Database design',
      timestamp: '2 days ago',
      preview: 'Best practices for database schema design'
    },
    {
      id: '6',
      title: 'CSS Grid vs Flexbox',
      timestamp: '3 days ago',
      preview: 'When should I use CSS Grid vs Flexbox?'
    },
    {
      id: '7',
      title: 'Authentication flow',
      timestamp: '3 days ago',
      preview: 'How to implement OAuth authentication?'
    },
    {
      id: '8',
      title: 'Performance optimization',
      timestamp: 'Last week',
      preview: 'Tips for optimizing web application performance'
    }
  ];

  return (
    <>
      {/* Overlay for mobile */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed top-0 left-0 h-full w-64 bg-[#141414] border-r border-gray-800/50 flex flex-col z-50 transition-transform duration-300 lg:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Header with close button on mobile */}
        <div className="p-4 flex items-center justify-between lg:justify-center">
          <button
            onClick={onClose}
            className="lg:hidden p-2 hover:bg-gray-800/50 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-400" />
          </button>
        </div>

        {/* New Chat Button */}
        <div className="px-3 pt-2 pb-4">
          <button className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-blue-600 to-cyan-500 hover:from-blue-700 hover:to-cyan-600 text-white rounded-lg transition-all duration-200 shadow-lg shadow-blue-500/20 hover:shadow-blue-500/40">
            <Plus className="w-5 h-5" />
            <span>New Chat</span>
          </button>
        </div>

        {/* Chat History */}
        <div className="flex-1 overflow-y-auto px-3 space-y-1">
          {chatHistory.map((chat) => (
            <button
              key={chat.id}
              onClick={() => setActiveChat(chat.id)}
              className={`w-full text-left p-3 rounded-lg transition-all duration-200 group ${
                activeChat === chat.id
                  ? 'bg-gray-800/70 shadow-lg'
                  : 'hover:bg-gray-800/30'
              }`}
            >
              <div className="flex items-start gap-3">
                <MessageSquare className="w-4 h-4 text-gray-400 mt-1 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-gray-200 text-sm truncate">{chat.title}</p>
                  <p className="text-gray-500 text-xs mt-1">{chat.timestamp}</p>
                </div>
              </div>
            </button>
          ))}
        </div>

        {/* User Profile */}
        <div className="p-4 border-t border-gray-800/50">
          <button className="w-full flex items-center gap-3 px-3 py-2 hover:bg-gray-800/30 rounded-lg transition-colors">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center">
              <User className="w-5 h-5 text-white" />
            </div>
            <div className="flex-1 text-left">
              <p className="text-gray-200 text-sm">User</p>
              <p className="text-gray-500 text-xs">user@example.com</p>
            </div>
          </button>
        </div>
      </aside>
    </>
  );
}
