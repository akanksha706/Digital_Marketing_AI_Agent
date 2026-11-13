import React, { useState, useRef, useEffect } from 'react';
import gsap from 'gsap';
import { apiClient } from '../api/client';
import {
  X,
  Send,
  ArrowRight,
  RotateCcw,
} from 'lucide-react';

interface ChatMessage {
  id: string;
  sender: 'bot' | 'user';
  text: string;
  quickReplies?: string[];
}

const LAYMAN_KNOWLEDGE: {
  keywords: string[];
  answer: string;
}[] = [
  {
    keywords: ['what is this', 'about', 'purpose', 'what does this do', 'what is studio', 'website'],
    answer:
      '42 WORKS Studio is an AI tool that turns your creative ideas into high-quality marketing posters and captions ready for social media in seconds!',
  },
  {
    keywords: ['how to make', 'how do i create', 'generate', 'create', 'prompt', 'make a poster', 'how to use'],
    answer:
      'Just type what you want in the prompt box (like "Diwali celebration" or "Product launch"), pick a format like Square or Story, and click "Generate Poster"!',
  },
  {
    keywords: ['edit', 'change text', 'headline', 'quote', 'modify', 'tweak'],
    answer:
      'Yes! When your poster is created, you can edit the headline, quote, and caption anytime with one click without having to redraw the image.',
  },
  {
    keywords: ['publish', 'share', 'post', 'linkedin', 'instagram', 'social media', 'schedule'],
    answer:
      'You can share your poster directly to LinkedIn or Instagram with a single click, or schedule it to post automatically on a specific date and time.',
  },
  {
    keywords: ['save', 'saved', 'library', 'where are my', 'find my', 'history'],
    answer:
      'All your created posters are safely saved in your "Library" tab at the top of the page so you can view, download, or reuse them anytime.',
  },
  {
    keywords: ['size', 'aspect ratio', 'format', 'story', 'square', 'dimension'],
    answer:
      'You can create posters in Square (1:1 for feeds), Portrait (4:5 for tall posts), Landscape (16:9 for banners), or Story format (9:16 for Reels and Stories).',
  },
  {
    keywords: ['download', 'save image', 'export'],
    answer:
      'Yes, you can download the full high-resolution poster image directly to your computer or phone whenever you open it in the review window.',
  },
  {
    keywords: ['delete', 'remove', 'trash'],
    answer:
      'You can delete drafts anytime. Posts that have already been shared can be moved to your Archive so your workspace stays clean and organized.',
  },
];

const INITIAL_WELCOME: ChatMessage = {
  id: 'welcome',
  sender: 'bot',
  text: 'Hi there! I am your 42 WORKS Studio helper. How can I help you create or share your posters today?',
  quickReplies: [
    'What does this website do?',
    'How do I make a poster?',
    'Can I edit the text on my poster?',
    'How do I post to LinkedIn or Instagram?',
    'Where are my saved posters?',
  ],
};

// Reusable Pikachu / Sparky Vector Face Component
const PikachuAvatar: React.FC<{ className?: string }> = ({ className = 'h-8 w-8' }) => (
  <svg viewBox="0 0 100 100" className={className}>
    {/* Left Ear */}
    <path
      d="M 32 38 L 18 10 L 28 20 L 26 4 L 42 30 Z"
      fill="#FFC20E"
      stroke="#0F172A"
      strokeWidth="2.5"
      strokeLinejoin="round"
    />
    <path d="M 18 10 L 26 4 L 24 16 Z" fill="#0F172A" />

    {/* Right Ear */}
    <path
      d="M 68 38 L 82 10 L 72 20 L 74 4 L 58 30 Z"
      fill="#FFC20E"
      stroke="#0F172A"
      strokeWidth="2.5"
      strokeLinejoin="round"
    />
    <path d="M 82 10 L 74 4 L 76 16 Z" fill="#0F172A" />

    {/* Chubby Round Head */}
    <circle cx="50" cy="58" r="32" fill="#FFFFFF" stroke="#0F172A" strokeWidth="3" />

    {/* Cute Cheeks */}
    <circle cx="28" cy="62" r="6" fill="#F59E0B" />
    <circle cx="72" cy="62" r="6" fill="#F59E0B" />

    {/* Eyes */}
    <circle cx="38" cy="54" r="6" fill="#0F172A" />
    <circle cx="36" cy="52" r="2.2" fill="#FFFFFF" />

    <circle cx="62" cy="54" r="6" fill="#0F172A" />
    <circle cx="60" cy="52" r="2.2" fill="#FFFFFF" />

    {/* Smile */}
    <path
      d="M 44 64 Q 50 68 56 64"
      fill="none"
      stroke="#0F172A"
      strokeWidth="2.4"
      strokeLinecap="round"
    />

    {/* 42 Logo Badge */}
    <rect x="42" y="74" width="16" height="10" rx="5" fill="#FFC20E" stroke="#0F172A" strokeWidth="1.5" />
    <text x="50" y="81.5" textAnchor="middle" fontSize="6.5" fontWeight="900" fill="#0F172A" fontFamily="Inter, sans-serif">
      42
    </text>
  </svg>
);

export const SparkyMascot: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([INITIAL_WELCOME]);
  const [inputQuery, setInputQuery] = useState('');
  const [isTyping, setIsTyping] = useState(false);

  const modalRef = useRef<HTMLDivElement>(null);
  const chatBottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to latest message
  useEffect(() => {
    if (isOpen) {
      chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isOpen, isTyping]);

  // Smooth pop animation on open
  useEffect(() => {
    if (isOpen && modalRef.current) {
      gsap.fromTo(
        modalRef.current,
        { scale: 0.94, opacity: 0, y: 10 },
        { scale: 1, opacity: 1, y: 0, duration: 0.25, ease: 'power2.out' }
      );
    }
  }, [isOpen]);

  const handleSendQuery = async (textToSend?: string) => {
    const query = (textToSend || inputQuery).trim();
    if (!query) return;

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      sender: 'user',
      text: query,
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputQuery('');
    setIsTyping(true);

    try {
      const res = await apiClient.post<{ reply: string }>('/assistant/chat', { message: query });
      const botMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        sender: 'bot',
        text: res.data.reply,
        quickReplies: [
          'How do I make a poster?',
          'Can I edit the text on my poster?',
          'How do I post to LinkedIn or Instagram?',
        ],
      };
      setMessages((prev) => [...prev, botMsg]);
    } catch {
      // Offline fallback
      const lower = query.toLowerCase();
      const matched = LAYMAN_KNOWLEDGE.find((item) =>
        item.keywords.some((kw) => lower.includes(kw))
      );
      const botMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        sender: 'bot',
        text: matched
          ? matched.answer
          : 'You can create posters in the Studio tab, move and edit text on the canvas, and share to LinkedIn or Instagram!',
        quickReplies: [
          'How do I make a poster?',
          'Can I edit the text on my poster?',
          'How do I post to LinkedIn or Instagram?',
        ],
      };
      setMessages((prev) => [...prev, botMsg]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <>
      {/* ========================================================================= */}
      {/* STATIC ASSISTANT AVATAR ANCHORED IN BOTTOM-RIGHT CORNER                   */}
      {/* ========================================================================= */}
      <aside aria-label="Studio Assistant" className="fixed bottom-4 right-4 sm:bottom-6 sm:right-6 z-50 select-none">
        <button
          type="button"
          onClick={() => setIsOpen(!isOpen)}
          title="Need help? Click to chat with 42 WORKS Assistant"
          className="group relative flex h-14 w-14 items-center justify-center rounded-2xl bg-white border-2 border-amber-300 shadow-xl shadow-slate-300/40 hover:border-[#FFC20E] hover:shadow-2xl hover:shadow-[#FFC20E]/30 transition-all hover:scale-105 active:scale-95 cursor-pointer"
        >
          <PikachuAvatar className="h-10 w-10" />

          {/* Online green indicator dot */}
          <span className="absolute -top-1 -right-1 flex h-3 w-3">
            <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500 border-2 border-white" />
          </span>
        </button>
      </aside>

      {/* ========================================================================= */}
      {/* CLEAN, CRISP LAYMAN CHAT WINDOW                                           */}
      {/* ========================================================================= */}
      {isOpen && (
        <div className="fixed bottom-20 right-4 sm:bottom-24 sm:right-6 z-50 w-[calc(100vw-2rem)] max-w-sm rounded-3xl border border-slate-200 bg-white shadow-2xl flex flex-col max-h-[75vh] overflow-hidden">
          <div ref={modalRef} className="flex flex-col h-full">
            {/* Header (Now features the EXACT SAME mascot icon!) */}
            <div className="flex items-center justify-between border-b border-slate-100 bg-slate-50 px-4 py-3">
              <div className="flex items-center gap-2.5">
                <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-white border border-amber-200 shadow-xs">
                  <PikachuAvatar className="h-7 w-7" />
                </div>
                <div>
                  <h3 className="text-xs font-bold text-slate-900">42 WORKS Assistant</h3>
                  <p className="text-[10px] text-slate-500">Ask any question in simple terms</p>
                </div>
              </div>

              <div className="flex items-center gap-1">
                <button
                  type="button"
                  onClick={() => setMessages([INITIAL_WELCOME])}
                  title="Restart chat"
                  className="rounded-lg p-1 text-slate-400 hover:bg-slate-200 hover:text-slate-700 cursor-pointer"
                >
                  <RotateCcw className="h-3.5 w-3.5" />
                </button>
                <button
                  type="button"
                  onClick={() => setIsOpen(false)}
                  className="rounded-lg p-1 text-slate-400 hover:bg-slate-200 hover:text-slate-700 cursor-pointer"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            </div>

            {/* Message Area */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-white text-xs max-h-[46vh]">
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start items-start gap-2'}`}
                >
                  {/* Mascot Face Beside Bot Messages */}
                  {msg.sender === 'bot' && (
                    <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-lg bg-amber-50 border border-amber-200 mt-0.5">
                      <PikachuAvatar className="h-5 w-5" />
                    </div>
                  )}

                  <div className={`flex flex-col ${msg.sender === 'user' ? 'items-end' : 'items-start'} max-w-[85%]`}>
                    <div
                      className={`rounded-2xl px-3.5 py-2.5 leading-relaxed ${
                        msg.sender === 'user'
                          ? 'bg-slate-900 text-white font-medium rounded-tr-xs'
                          : 'bg-slate-100 text-slate-800 rounded-tl-xs border border-slate-200/50'
                      }`}
                    >
                      {msg.text}
                    </div>

                    {/* Simple Clean Quick Reply Pills */}
                    {msg.quickReplies && msg.quickReplies.length > 0 && (
                      <div className="mt-2 flex flex-col gap-1.5 w-full">
                        {msg.quickReplies.map((qr, idx) => (
                          <button
                            key={idx}
                            type="button"
                            onClick={() => handleSendQuery(qr)}
                            className="flex items-center justify-between rounded-xl bg-amber-50 hover:bg-amber-100/80 border border-amber-200/70 px-3 py-1.5 text-[11px] font-semibold text-amber-950 text-left transition-colors cursor-pointer"
                          >
                            <span>{qr}</span>
                            <ArrowRight className="h-3 w-3 text-amber-700 shrink-0 ml-1" />
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {isTyping && (
                <div className="flex items-center gap-2">
                  <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-lg bg-amber-50 border border-amber-200">
                    <PikachuAvatar className="h-5 w-5" />
                  </div>
                  <div className="flex items-center gap-1 bg-slate-100 rounded-xl px-2.5 py-1.5 w-14">
                    <span className="h-1.5 w-1.5 rounded-full bg-slate-400 animate-bounce" />
                    <span className="h-1.5 w-1.5 rounded-full bg-slate-400 animate-bounce [animation-delay:0.15s]" />
                    <span className="h-1.5 w-1.5 rounded-full bg-slate-400 animate-bounce [animation-delay:0.3s]" />
                  </div>
                </div>
              )}

              <div ref={chatBottomRef} />
            </div>

            {/* Input Bar */}
            <div className="border-t border-slate-100 bg-slate-50 p-2.5">
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  handleSendQuery();
                }}
                className="flex items-center gap-1.5"
              >
                <input
                  type="text"
                  value={inputQuery}
                  onChange={(e) => setInputQuery(e.target.value)}
                  placeholder="Ask a question..."
                  className="flex-1 rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs text-slate-900 placeholder-slate-400 focus:border-[#FFC20E] focus:outline-none"
                />
                <button
                  type="submit"
                  disabled={!inputQuery.trim() || isTyping}
                  className="flex h-8 w-8 items-center justify-center rounded-xl bg-[#FFC20E] hover:bg-[#e6ad0a] text-slate-950 transition-all disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
                >
                  <Send className="h-3.5 w-3.5" />
                </button>
              </form>
            </div>
          </div>
        </div>
      )}
    </>
  );
};
