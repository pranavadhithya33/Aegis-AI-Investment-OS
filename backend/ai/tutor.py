"""
backend/ai/tutor.py
Aegis Tutor — Educational AI for Beginners
NEVER predicts prices. NEVER says buy/sell/hold.
"""
import os
from typing import Optional, List
from pydantic import BaseModel

class TutorMessage(BaseModel):
    role: str  # "tutor" or "user"
    content: str
    context: Optional[str] = None

class TutorContext(BaseModel):
    step: str  # "welcome", "goals", "risk", "portfolio", "valuation", "monthly"
    user_goal: Optional[str] = None
    risk_tolerance: Optional[int] = None
    monthly_investment: Optional[int] = None
    portfolio_template: Optional[str] = None

class TutorResponse(BaseModel):
    message: str
    tip: Optional[str] = None
    warning: Optional[str] = None
    action_suggestion: Optional[str] = None

class AegisTutor:
    """
    The AI Tutor is a patient educator, not an oracle.
    It explains concepts, warns about behavioral traps, and encourages consistency.
    """

    def __init__(self, llm_client=None):
        self.llm = llm_client
        self.fallback_mode = llm_client is None

    def generate_message(self, context: TutorContext, user_question: Optional[str] = None) -> TutorResponse:
        """Generate a contextual educational message."""

        if self.fallback_mode:
            return self._fallback_message(context)

        # Build the safe prompt
        prompt = self._build_safe_prompt(context, user_question)

        try:
            response = self.llm.generate(prompt)
            return self._parse_response(response)
        except Exception:
            return self._fallback_message(context)

    def _build_safe_prompt(self, ctx: TutorContext, question: Optional[str]) -> str:
        """Build a prompt that is physically incapable of generating harmful advice."""

        base = """You are Aegis Tutor, a patient financial educator for Indian beginners aged 18-30.

ABSOLUTE RULES (violating any of these is a critical failure):
1. NEVER predict future stock prices, market direction, or asset performance
2. NEVER say "buy", "sell", "hold", "undervalued", "overvalued", or "good time to invest"
3. NEVER recommend specific stocks, ETFs, or mutual funds by name as a recommendation
4. NEVER claim the AI has special insight, edge, or predictive ability
5. ALWAYS frame investing as probabilistic, not deterministic
6. ALWAYS emphasize that past performance ≠ future results
7. ALWAYS encourage users to do their own research beyond metrics
8. ALWAYS use plain English — explain jargon immediately

Your tone: Friendly, encouraging, slightly humorous, never condescending.
You are a smart friend who happens to know finance, not a guru.

Current context:
"""

        context_str = f"- User is on step: {ctx.step}\n"
        if ctx.user_goal:
            context_str += f"- Investment goal: {ctx.user_goal}\n"
        if ctx.risk_tolerance:
            context_str += f"- Risk tolerance: {ctx.risk_tolerance}/10\n"
        if ctx.monthly_investment:
            context_str += f"- Monthly investment: ₹{ctx.monthly_investment}\n"
        if ctx.portfolio_template:
            context_str += f"- Portfolio type: {ctx.portfolio_template}\n"

        user_q = f"\nUser question: {question}\n" if question else "\n"

        instruction = """\nGenerate a response (3-5 short paragraphs) that:
- Educates the user about the current step's concept
- Uses a relatable analogy (food, sports, school, etc.)
- Includes ONE practical tip they can act on today
- Includes ONE warning about a common beginner mistake
- Ends with an encouraging sentence

Format your response as:
MESSAGE: [your main educational text]
TIP: [one actionable tip]
WARNING: [one common mistake to avoid]
ACTION: [one small next step]
"""

        return base + context_str + user_q + instruction

    def _fallback_message(self, ctx: TutorContext) -> TutorResponse:
        """Pre-written safe messages when LLM is unavailable."""

        messages = {
            "welcome": TutorResponse(
                message="""Hi! I'm your investing tutor. Think of me as that friend who reads too much about money and loves explaining it.

Here's the truth: investing isn't about being smart. It's about being consistent. The richest people you know didn't get rich by picking the right stock. They got rich by starting early and not stopping.

At 18, you have a superpower that Warren Buffett doesn't: time. ₹5,000/month starting now beats ₹50,000/month starting at 35. That's not motivation — that's math.""",
                tip="Open a brokerage account this week. Even if you don't invest yet, having it ready removes friction.",
                warning="Don't wait for the 'perfect time' to start. There is no perfect time. The best day to start was yesterday. The second best day is today.",
                action_suggestion="Go to the next step and tell me what you're investing for."
            ),
            "goals": TutorResponse(
                message="""Goals matter more than stock picks. Here's why:

Imagine two people. One says "I want to get rich." The other says "I need ₹20 lakh for a house down payment in 7 years." The second person will make better decisions because they know exactly what they're optimizing for.

If you're investing for 10+ years, you can handle more volatility because you have time to recover. If you need the money in 3 years, you can't afford a crash right before you need it.""",
                tip="Write your goal down. Put it on your phone wallpaper. When the market crashes, read it. It will stop you from panic-selling.",
                warning="Don't change your goal every month. The people who switch from 'wealth' to 'house' to 'income' every quarter never build anything.",
                action_suggestion="Pick one goal and commit to it for at least 2 years."
            ),
            "risk": TutorResponse(
                message="""Risk isn't about bravery. It's about sleep.

If your portfolio drops 30% and you can't sleep, you have too much risk. If it drops 30% and you think "great, I'm buying the sale," you have the right risk level.

Here's the paradox: the most aggressive investors often make the LEAST money because they panic-sell during crashes. A moderate portfolio you stick with beats an aggressive portfolio you abandon.""",
                tip="Be honest with yourself. If you've never experienced a market crash, assume you'll panic more than you think.",
                warning="Every beginner thinks they can handle risk until they actually lose money. The market has a way of humbling overconfidence.",
                action_suggestion="Choose a risk level 1-2 points LOWER than your ego wants. You'll thank yourself later."
            ),
            "portfolio": TutorResponse(
                message="""This portfolio isn't magic. It's just math.

When you buy a Nifty 50 ETF, you own tiny pieces of 50 companies. If Reliance does badly, TCS might do well. If both do badly, your gold might rise. This is called diversification, and it's the only free lunch in finance.

The AI didn't pick "winning" stocks. It spread your money so no single company can ruin you. That's not exciting. That's the point. Excitement in investing usually means you're gambling.""",
                tip="Set up an automatic SIP so you invest without thinking about it. Automation beats willpower.",
                warning="Don't check your portfolio every day. Daily checking leads to emotional decisions. Monthly is enough.",
                action_suggestion="Set up your first SIP this month. Start with whatever amount you can afford — even ₹1,000. The habit matters more than the amount."
            ),
            "valuation": TutorResponse(
                message="""Valuation metrics are like a health checkup. They tell you what the market currently thinks, not what will happen.

A low P/E might mean a bargain. Or it might mean the company is dying and everyone knows it except you. A high P/E might mean overvaluation. Or it might mean the company is growing so fast that today's price looks cheap in hindsight.

The metrics don't make decisions. YOU make decisions. The metrics just give you data to think with.""",
                tip="Always look at 5-year trends, not just today's number. A company with improving ROE is very different from one with declining ROE.",
                warning="Never buy a stock just because the P/E is low. The market is usually right about why something is cheap. Do the work to understand the business.",
                action_suggestion="Pick one company you admire. Read its last annual report. Just 10 pages. That's more research than 90% of investors do."
            ),
            "monthly": TutorResponse(
                message="""It's the 1st of the month. Time for your monthly investment.

Remember: you're not trying to time the market. You're trying to time IN the market. The people who get rich are the ones who keep buying through crashes, not the ones who wait for the "perfect" entry.

If the market went down last month, congratulations — you're buying at a discount. If it went up, congratulations — your existing investments gained value. Either way, invest this month.""",
                tip="If you get a bonus or windfall, invest it immediately. Don't try to "drip" it in. Lump sum investing usually wins.",
                warning="Don't skip your SIP because you 'want to wait for a better price.' That thinking has cost beginners more money than any crash.",
                action_suggestion="Transfer your monthly amount now. Then close the app and live your life."
            ),
        }

        return messages.get(ctx.step, TutorResponse(
            message="I'm here to help you learn about investing. What would you like to understand better?",
            tip="Start with the basics. Understanding risk and diversification is more valuable than any stock tip.",
            warning="Be wary of anyone promising easy returns. If it sounds too good to be true, it is.",
            action_suggestion="Explore the portfolio builder or the valuation lab."
        ))

    def _parse_response(self, raw: str) -> TutorResponse:
        """Parse LLM output into structured response."""
        message = ""
        tip = None
        warning = None
        action = None

        lines = raw.split("\n")
        current = "message"

        for line in lines:
            line = line.strip()
            if line.startswith("TIP:"):
                current = "tip"
                tip = line.replace("TIP:", "").strip()
            elif line.startswith("WARNING:"):
                current = "warning"
                warning = line.replace("WARNING:", "").strip()
            elif line.startswith("ACTION:"):
                current = "action"
                action = line.replace("ACTION:", "").strip()
            elif line.startswith("MESSAGE:"):
                current = "message"
                message = line.replace("MESSAGE:", "").strip()
            else:
                if current == "message":
                    message += " " + line
                elif current == "tip":
                    tip += " " + line
                elif current == "warning":
                    warning += " " + line
                elif current == "action":
                    action += " " + line

        # Safety filter — redact any forbidden words
        forbidden = ["buy", "sell", "hold", "undervalued", "overvalued", "will go up", "will go down", "guaranteed"]
        full_text = (message + " " + (tip or "") + " " + (warning or "") + " " + (action or "")).lower()

        for word in forbidden:
            if word in full_text:
                # If LLM violated rules, return fallback
                return self._fallback_message(TutorContext(step="unknown"))

        return TutorResponse(
            message=message.strip(),
            tip=tip,
            warning=warning,
            action_suggestion=action
        )

    def generate_monthly_reminder(self, portfolio_summary: dict) -> str:
        """Generate a monthly educational reminder."""

        prompt = """You are Aegis Tutor. Write a friendly monthly investment reminder (max 120 words).

Rules:
- Encourage the user to invest their monthly SIP
- If the market dropped recently, frame it as "buying on sale"
- If the market rose, remind them not to get greedy
- Include one educational fact
- NEVER predict future prices
- NEVER say buy/sell/hold
- Sign off as "Aegis Tutor"

Portfolio context: {summary}
""".format(summary=str(portfolio_summary))

        if self.fallback_mode or not self.llm:
            return """Hey! It's time for your monthly investment.

Remember: consistency beats timing. The people who build wealth aren't the ones who pick the perfect moment — they're the ones who never stop.

This month, whether the market is up or down, invest your SIP amount and move on. The best investment decision you can make is to ignore the noise.

— Aegis Tutor"""

        try:
            return self.llm.generate(prompt)
        except Exception:
            return self.generate_monthly_reminder(portfolio_summary)  # fallback

# Singleton instance
tutor = AegisTutor(llm_client=None)  # Set to your LLM client when available
