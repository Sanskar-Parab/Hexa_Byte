"use client";

import { useState, useRef, useEffect, Fragment } from "react";
import { Send, Bot, User, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";

interface Message {
  role: "user" | "assistant";
  content: string;
  suggestions?: string[];
}

interface ChatInterfaceProps {
  onAsk: (
    question: string,
    conversation: { role: "user" | "assistant"; content: string }[]
  ) => Promise<{
    response: string;
    suggestions: string[];
  }>;
  focusSkill?: string | null;
}

const MAX_HISTORY_MESSAGES = 10; // last ~5 turns — enough for follow-ups like "why?", bounded so the prompt stays small

function getStarterQuestions(focusSkill?: string | null) {
  return [
    "What should I learn next?",
    "Why am I not ready yet?",
    "Which project should I build?",
    focusSkill ? `How can I improve my ${focusSkill}?` : "How can I improve my core skills?",
    "Am I ready for this career?",
  ];
}

// Renders **bold** segments from plain-text coach responses without assuming any other structure.
function RichText({ text }: { text: string }) {
  const lines = text.split("\n");
  return (
    <>
      {lines.map((line, i) => {
        const parts = line.split(/(\*\*[^*]+\*\*)/g).filter(Boolean);
        return (
          <Fragment key={i}>
            {parts.map((part, j) =>
              part.startsWith("**") && part.endsWith("**") ? (
                <strong key={j} className="font-semibold text-ink">
                  {part.slice(2, -2)}
                </strong>
              ) : (
                <Fragment key={j}>{part}</Fragment>
              )
            )}
            {i < lines.length - 1 && <br />}
          </Fragment>
        );
      })}
    </>
  );
}

export function ChatInterface({ onAsk, focusSkill }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content:
        "Hi, I'm your AI Career Coach. I use your actual skill evidence, target career, and roadmap progress to give you grounded, specific guidance — not generic advice.",
      suggestions: getStarterQuestions(focusSkill),
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleSend = async (question?: string) => {
    const q = question || input.trim();
    if (!q || loading) return;

    // Build history from the messages already on screen, before appending the new question.
    const history = messages
      .filter((m) => m.role === "user" || m.role === "assistant")
      .slice(-MAX_HISTORY_MESSAGES)
      .map((m) => ({ role: m.role, content: m.content }));

    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: q }]);
    setLoading(true);

    try {
      const result = await onAsk(q, history);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: result.response,
          suggestions: result.suggestions,
        },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            err instanceof Error && err.message
              ? `Sorry, I couldn't process that: ${err.message}`
              : "Sorry, I couldn't process that. Please try again.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-[calc(100vh-320px)] min-h-[440px] flex-col rounded-xl border border-hairline bg-canvas shadow-card">
      <div className="flex-1 space-y-4 overflow-y-auto p-4 sm:p-6">
        {messages.map((msg, i) => (
          <div key={i} className={cn("flex items-start gap-2.5 sm:gap-3", msg.role === "user" && "justify-end")}>
            {msg.role === "assistant" && (
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-canvas-soft2">
                <Bot className="h-4 w-4 text-ink" />
              </div>
            )}
            <div
              className={cn(
                "max-w-[85%] sm:max-w-[75%] rounded-2xl px-4 py-3",
                msg.role === "user"
                  ? "rounded-br-md bg-ink text-white"
                  : "rounded-bl-md border border-hairline bg-canvas-soft text-ink"
              )}
            >
              <p className="whitespace-pre-wrap break-words text-sm leading-relaxed">
                <RichText text={msg.content} />
              </p>
              {msg.suggestions && msg.suggestions.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-2">
                  {msg.suggestions.map((s, j) => (
                    <button
                      key={j}
                      onClick={() => handleSend(s)}
                      className="rounded-full border border-hairline bg-canvas px-3 py-1 text-xs text-body transition-colors hover:border-ink/20 hover:bg-canvas-soft2 hover:text-ink"
                    >
                      {s}
                    </button>
                  ))}
                </div>
              )}
            </div>
            {msg.role === "user" && (
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-canvas-soft2">
                <User className="h-4 w-4 text-body" />
              </div>
            )}
          </div>
        ))}
        {loading && (
          <div className="flex items-start gap-2.5 sm:gap-3">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-canvas-soft2">
              <Bot className="h-4 w-4 text-ink" />
            </div>
            <div className="rounded-2xl rounded-bl-md border border-hairline bg-canvas-soft px-4 py-3">
              <div className="flex items-center gap-1.5">
                <Sparkles className="h-4 w-4 animate-pulse text-link" />
                <span className="text-sm text-mute">Thinking through your data...</span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="border-t border-hairline bg-canvas p-3 sm:p-4">
        <div className="flex gap-2">
          <Textarea
            placeholder="Ask your career coach..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            className="min-h-[44px] max-h-32 resize-none border-hairline"
            rows={1}
          />
          <Button onClick={() => handleSend()} disabled={!input.trim() || loading} className="shrink-0">
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
