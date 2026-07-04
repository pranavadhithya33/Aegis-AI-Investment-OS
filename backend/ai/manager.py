import httpx
import logging
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from datetime import datetime

from backend.config.settings import settings
from backend.database.models import AgentLog

logger = logging.getLogger("ai.manager")

class AIManager:
    """
    Manages connections to various LLM providers (Gemini, Groq, OpenRouter, Ollama).
    Implements key-based routing and automated fallback policies.
    """

    @classmethod
    def generate(
        cls,
        db: Session,
        prompt: str,
        system_instruction: Optional[str] = None,
        provider: Optional[str] = None,
        agent_name: str = "AegisAgent",
        mock_response: Optional[str] = None
    ) -> str:
        """
        Executes a completion request across LLM providers.
        If provider is None, routes to Gemini -> Groq -> OpenRouter -> Ollama -> Mock.
        Logs inputs/outputs to the 'agent_logs' DB table.
        """
        # If in test mode or keys are missing, and a mock is provided/requested, use mock
        if settings.ENV == "test" or mock_response is not None:
            return cls._log_and_return_mock(db, prompt, agent_name, mock_response)

        # Build fallback list
        providers = [provider] if provider else ["gemini", "groq", "openrouter", "ollama"]
        
        for prov in providers:
            try:
                if prov == "gemini" and settings.GEMINI_API_KEY:
                    return cls._call_gemini(db, prompt, system_instruction, agent_name)
                elif prov == "groq" and settings.GROQ_API_KEY:
                    return cls._call_groq(db, prompt, system_instruction, agent_name)
                elif prov == "openrouter" and settings.OPENROUTER_API_KEY:
                    return cls._call_openrouter(db, prompt, system_instruction, agent_name)
                elif prov == "ollama":
                    # We only call Ollama if OLLAMA_HOST is up (or we try it)
                    return cls._call_ollama(db, prompt, system_instruction, agent_name)
            except Exception as e:
                logger.warning(f"AI provider '{prov}' failed with error: {e}. Trying next fallback...")
                continue

        # If all fail, return a fallback mock response to keep the pipeline alive
        logger.error("All configured LLM providers failed or no API keys were provided. Returning mock response.")
        return cls._log_and_return_mock(db, prompt, agent_name, mock_response)

    @classmethod
    def _call_gemini(cls, db: Session, prompt: str, system: Optional[str], agent: str) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
        
        # Combine system instruction into prompt if needed
        full_prompt = f"System: {system}\nUser: {prompt}" if system else prompt
        
        payload = {
            "contents": [{
                "parts": [{"text": full_prompt}]
            }]
        }
        
        with httpx.Client() as client:
            resp = client.post(url, json=payload, timeout=20.0)
            resp.raise_for_status()
            res_json = resp.json()
            
            completion = res_json["candidates"][0]["content"]["parts"][0]["text"]
            # Simple token estimation
            prompt_tokens = len(full_prompt) // 4
            comp_tokens = len(completion) // 4
            
            cls._save_log(db, agent, full_prompt, completion, prompt_tokens, comp_tokens)
            return completion

    @classmethod
    def _call_groq(cls, db: Session, prompt: str, system: Optional[str], agent: str) -> str:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {settings.GROQ_API_KEY}"}
        
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": "llama3-8b-8192",
            "messages": messages
        }
        
        with httpx.Client() as client:
            resp = client.post(url, headers=headers, json=payload, timeout=20.0)
            resp.raise_for_status()
            res_json = resp.json()
            
            completion = res_json["choices"][0]["message"]["content"]
            usage = res_json.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", len(prompt) // 4)
            comp_tokens = usage.get("completion_tokens", len(completion) // 4)
            
            cls._save_log(db, agent, prompt, completion, prompt_tokens, comp_tokens)
            return completion

    @classmethod
    def _call_openrouter(cls, db: Session, prompt: str, system: Optional[str], agent: str) -> str:
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {"Authorization": f"Bearer {settings.OPENROUTER_API_KEY}"}
        
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": "meta-llama/llama-3-8b-instruct:free",
            "messages": messages
        }
        
        with httpx.Client() as client:
            resp = client.post(url, headers=headers, json=payload, timeout=20.0)
            resp.raise_for_status()
            res_json = resp.json()
            
            completion = res_json["choices"][0]["message"]["content"]
            cls._save_log(db, agent, prompt, completion, len(prompt)//4, len(completion)//4)
            return completion

    @classmethod
    def _call_ollama(cls, db: Session, prompt: str, system: Optional[str], agent: str) -> str:
        url = f"{settings.OLLAMA_HOST}/api/generate"
        payload = {
            "model": "llama3",
            "prompt": prompt,
            "stream": False
        }
        if system:
            payload["system"] = system
            
        with httpx.Client() as client:
            resp = client.post(url, json=payload, timeout=30.0)
            resp.raise_for_status()
            res_json = resp.json()
            
            completion = res_json["response"]
            cls._save_log(db, agent, prompt, completion, len(prompt)//4, len(completion)//4)
            return completion

    @classmethod
    def _log_and_return_mock(
        cls,
        db: Session,
        prompt: str,
        agent: str,
        mock_response: Optional[str]
    ) -> str:
        # Default mock response if none provided
        res = mock_response or "MOCK_AI_RESPONSE: Processed request successfully."
        cls._save_log(db, agent, prompt, res, len(prompt)//4, len(res)//4)
        return res

    @staticmethod
    def _save_log(
        db: Session,
        agent_name: str,
        prompt: str,
        completion: str,
        p_tokens: int,
        c_tokens: int
    ):
        """Save AI tokens and prompts transaction log to database."""
        try:
            log = AgentLog(
                agent_name=agent_name,
                prompt_content=prompt,
                completion_content=completion,
                prompt_tokens=p_tokens,
                completion_tokens=c_tokens,
                timestamp=datetime.utcnow()
            )
            db.add(log)
            db.commit()
        except Exception as e:
            logger.error(f"Failed to save AgentLog to database: {e}")
            db.rollback()
