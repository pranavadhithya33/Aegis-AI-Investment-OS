// Educational AI sidebar that explains concepts in real-time.
"use client";

import React, { useState, useEffect } from "react";

interface TutorMessage {
  role: "tutor" | "user";
  content: string;
  tip?: string;
  warning?: string;
  action?: string;
}

interface AITutorSidebarProps {
  step: number;
  goal: string | null;
  risk: number;
  monthly: number;
}

export function AITutorSidebar({ step, goal, risk, monthly }: AITutorSidebarProps) {
  const [messages, setMessages] = useState<TutorMessage[]>([]);
  const [userInput, setUserInput] = useState("");

  const stepMessages: Record<number, TutorMessage> = {
    1: {
      role: "tutor",
      content: `Hi! I'm your investing tutor. Think of me as that friend who reads too much about money and loves explaining it.\n\nInvesting isn't about being smart. It's about being consistent. The richest people didn't get rich by picking the right stock. They got rich by starting early and not stopping.`,
      tip: "Open a brokerage account this week. Even if you don't invest yet, having it ready removes friction.",
      warning: "Don't wait for the 'perfect time' to start. There is no perfect time.",
    },
    2: {
      role: "tutor",
      content: `Goals matter more than stock picks.\n\nIf you're investing for 10+ years, you can handle more volatility because you have time to recover. If you need the money in 3 years, you can't afford a crash right before you need it.`,
      tip: "Write your goal down. Put it on your phone wallpaper. When the market crashes, read it.",
      warning: "Don't change your goal every month. The people who switch goals every quarter never build anything.",
    },
    3: {
      role: "tutor",
      content: `Risk isn't about bravery. It's about sleep.\n\nIf your portfolio drops 30% and you can't sleep, you have too much risk. If it drops 30% and you think "great, I'm buying the sale," you have the right risk level.\n\nThe most aggressive investors often make the LEAST money because they panic-sell during crashes.`,
      tip: "Be honest with yourself. If you've never experienced a crash, assume you'll panic more than you think.",
      warning: "Every beginner thinks they can handle risk until they actually lose money.",
    },
    4: {
      role: "tutor",
      content: `This portfolio isn't magic. It's just math.\n\nWhen you buy a Nifty 50 ETF, you own tiny pieces of 50 companies. If Reliance does badly, TCS might do well. This is called diversification, and it's the only free lunch in finance.\n\nThe AI didn't pick "winning" stocks. It spread your money so no single company can ruin you. That's not exciting. That's the point.`,
      tip: "Set up an automatic SIP so you invest without thinking about it. Automation beats willpower.",
      warning: "Don't check your portfolio every day. Daily checking leads to emotional decisions.",
    },
    5: {
      role: "tutor",
      content: `You just made a smart decision. Most people never start. You did.\n\nNow the key is consistency. If the market drops, keep buying. If it rises, don't get greedy. The people who build wealth are the ones who show up every month, not the ones who time the market perfectly.`,
      tip: "If you get a bonus, invest it immediately. Don't try to 'drip' it in. Lump sum usually wins.",
      warning: "The #1 beginner mistake: Stopping your SIP when the market drops. That's when stocks are on sale!",
    },
  };

  useEffect(() => {
    const msg = stepMessages[step];
    if (msg) {
      setMessages([msg]);
    }
  }, [step]);

  const askQuestion = async () => {
    if (!userInput.trim()) return;

    const userMsg: TutorMessage = { role: "user", content: userInput };
    setMessages((prev) => [...prev, userMsg]);
    setUserInput("");

    // In production, call your backend:
    // const res = await fetch("/api/ai/tutor", { ... })
    // For now, show a safe fallback response
    setTimeout(() => {
      const tutorResponse: TutorMessage = {
        role: "tutor",
        content: `That's a great question! I can't predict what ${userInput} will do, but I can help you think about it.\n\nThe best investors don't try to predict prices. They ask: "Do I understand this business? Would I be okay owning it for 10 years even if the price drops 50%?" If the answer is yes, the price today matters less than you think.`,
        tip: "Read the company's annual report. Just 10 pages. That's more research than 90% of investors do.",
        warning: "Never invest in something you can't explain to a 10-year-old in one sentence.",
      };
      setMessages((prev) => [...prev, tutorResponse]);
    }, 800);
  };

  return (
    <aside className="ai-sidebar">
      <div className="ai-header">
        <div className="ai-avatar">🎓</div>
        <div>
          <div className="ai-name">Aegis Tutor</div>
          <div className="ai-status">Online — Learning with you</div>
        </div>
      </div>

      <div className="ai-chat">
        {messages.map((msg, i) => (
          <div key={i} className={`chat-bubble ${msg.role}`}>
            <div className="bubble-content">
              {msg.content.split("\n").map((line, j) => (
                <p key={j}>{line}</p>
              ))}
              {msg.tip && (
                <div className="tip-box">
                  💡 <strong>Tip:</strong> {msg.tip}
                </div>
              )}
              {msg.warning && (
                <div className="warning-box">
                  ⚠️ <strong>Watch out:</strong> {msg.warning}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      <div className="ai-input">
        <input
          type="text"
          placeholder="Ask me anything about investing..."
          value={userInput}
          onChange={(e) => setUserInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && askQuestion()}
        />
        <button onClick={askQuestion}>Ask</button>
      </div>
    </aside>
  );
}
