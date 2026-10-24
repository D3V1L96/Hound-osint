import json
import requests
from typing import Dict, Any

class AIAgent:
    """Local AI Analyst for HOUND OSINT Framework"""
    
    def __init__(self, model: str = "llama3.2", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        
    def is_available(self) -> bool:
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
            
    def analyze_evidence(self, target: str, evidence: Dict[str, Any]) -> str:
        system_prompt = '''You are HOUND's AI Intelligence Analyst. 
Your ONLY job is to summarize OSINT findings into actionable intelligence.

STRICT RULES:
1. NEVER invent facts, URLs, IPs, or relationships not in the evidence
2. If evidence is missing, state "No data available"
3. Always cite which collector produced each finding [DNS], [WHOIS], [SHODAN]
4. Flag conflicting information explicitly
5. Output MUST be concise, professional, and structured
6. Never claim 100% certainty
7. Do NOT execute commands or suggest actions beyond analysis
8. Suggested Next Steps MUST be derived from gaps in current evidence'''

        user_prompt = f'''Analyze this OSINT evidence for target: {target}

EVIDENCE DATA:
{json.dumps(evidence, indent=2, default=str)}

Produce a structured intelligence brief with EXACTLY these sections:
## EXECUTIVE SUMMARY
(2-3 sentences max)

## KEY VERIFIED FINDINGS
(Bullet points with source attribution)

## SECURITY POSTURE ASSESSMENT
(Risk level + specific observations)

## UNRESOLVED QUESTIONS / GAPS
(What critical data is missing?)

## SUGGESTED NEXT STEPS
(Numbered list of 3-5 specific follow-up tasks addressing gaps)

## CONFIDENCE LEVEL
(High/Medium/Low + rationale)

FORMAT: Use markdown headers (##). Keep terminal-readable.'''

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": False,
            "options": {"temperature": 0.1, "num_ctx": 4096}
        }
        
        try:
            # Try modern chat endpoint first
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=120
            )
            
            # Fallback to legacy generate endpoint for older Ollama versions
            if response.status_code == 404:
                legacy_payload = {
                    "model": self.model,
                    "prompt": f"{system_prompt}\n\n{user_prompt}",
                    "stream": False,
                    "options": {"temperature": 0.1, "num_ctx": 4096}
                }
                response = requests.post(
                    f"{self.base_url}/api/generate",
                    json=legacy_payload,
                    timeout=120
                )
                result = response.json()["response"]
            else:
                response.raise_for_status()
                result = response.json()["message"]["content"]
                
            return result
            
        except requests.exceptions.ConnectionError:
            return "[AI OFFLINE] Cannot connect to Ollama at localhost:11434"
        except Exception as e:
            return f"[AI ERROR] {str(e)}\nTip: Run 'ollama list' to verify model exists"
