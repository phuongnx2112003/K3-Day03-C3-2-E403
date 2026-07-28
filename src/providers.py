"""
🔌 MULTI-PROVIDER LLM ADAPTER (OpenAI, Gemini, Anthropic, OpenRouter & Offline Mock)
Hỗ trợ chuyển đổi linh hoạt giữa các nhà cung cấp AI chỉ bằng cách đổi biến môi trường LLM_PROVIDER.
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv

DEFAULT_GEMINI_MODEL = "gemini-3.6-flash"
RETIRED_GEMINI_MODELS = {
    "gemini-2.5-flash",
    "gemini-2.5-flash-preview-09-25",
}

# Đảm bảo in ra Tiếng Việt và Emojis không bị lỗi trên Windows Console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

load_dotenv()

class BaseLLMProvider:
    """Interface cơ sở cho tất cả các LLM Provider"""
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        raise NotImplementedError


class GeminiProvider(BaseLLMProvider):
    """Google Gemini Provider"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        requested_model = model or os.getenv("LLM_MODEL") or DEFAULT_GEMINI_MODEL
        # Các key/API project mới có thể nhận 404 với Gemini 2.5 Flash. Tự
        # migrate giá trị legacy, nhưng vẫn tôn trọng một model mới do user chọn.
        self.model_name = DEFAULT_GEMINI_MODEL if requested_model in RETIRED_GEMINI_MODELS else requested_model
        
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            return "[Gemini Error]: Chưa cấu hình GEMINI_API_KEY trong file .env!"
        try:
            from google import genai
            client = genai.Client(api_key=self.api_key)
            contents = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            response = client.models.generate_content(
                model=self.model_name,
                contents=contents
            )
            return response.text
        except Exception as e:
            return f"[Gemini Exception]: {str(e)}"


class OpenAIProvider(BaseLLMProvider):
    """OpenAI Provider (GPT-4o, GPT-3.5-turbo, etc.)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gpt-4o-mini"
        
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            return "[OpenAI Error]: Chưa cấu hình OPENAI_API_KEY trong file .env!"
        try:
            import openai
            client_kwargs = {"api_key": self.api_key}
            if os.getenv("OPENAI_BASE_URL"):
                client_kwargs["base_url"] = os.getenv("OPENAI_BASE_URL")
            client = openai.OpenAI(**client_kwargs)
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = client.chat.completions.create(
                model=self.model_name,
                messages=messages
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"[OpenAI Exception]: {str(e)}"


class OllamaProvider(BaseLLMProvider):
    """Ollama local hoặc Ollama Cloud qua API chính thức /api/chat."""
    def __init__(self, api_key: str = None, model: str = None, base_url: str = None):
        self.api_key = api_key or os.getenv("OLLAMA_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gemma4:31b-cloud"
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL") or "https://ollama.com/api").rstrip("/")

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key:
            return "[Ollama Error]: Chưa cấu hình OLLAMA_API_KEY trong file .env!"
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        try:
            response = requests.post(
                f"{self.base_url}/chat",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": self.model_name, "messages": messages, "stream": False},
                timeout=20,
            )
            response.raise_for_status()
            return response.json()["message"]["content"]
        except Exception as exc:
            return f"[Ollama Exception]: {exc}"


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude Provider (Claude 3.5 Sonnet, Claude 3 Haiku)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "claude-3-haiku-20240307"
        
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_anthropic_api_key_here":
            return "[Anthropic Error]: Chưa cấu hình ANTHROPIC_API_KEY trong file .env!"
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.api_key)
            kwargs = {
                "model": self.model_name,
                "max_tokens": 1000,
                "messages": [{"role": "user", "content": prompt}]
            }
            if system_prompt:
                kwargs["system"] = system_prompt
                
            response = client.messages.create(**kwargs)
            return response.content[0].text
        except Exception as e:
            return f"[Anthropic Exception]: {str(e)}"


class OpenRouterProvider(BaseLLMProvider):
    """OpenRouter Provider (Hỗ trợ gọi mọi model qua OpenRouter API)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "google/gemini-3.6-flash"
        
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_openrouter_api_key_here":
            return "[OpenRouter Error]: Chưa cấu hình OPENROUTER_API_KEY trong file .env!"
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            payload = {
                "model": self.model_name,
                "messages": messages
            }
            res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=30)
            if res.status_code == 200:
                data = res.json()
                return data["choices"][0]["message"]["content"]
            else:
                return f"[OpenRouter API Error {res.status_code}]: {res.text}"
        except Exception as e:
            return f"[OpenRouter Exception]: {str(e)}"


class MockProvider(BaseLLMProvider):
    """Offline Mock Provider (Cho bài test không cần kết nối API)"""
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if "QUY TRÌNH SUY LUẬN BẮT BUỘC" in system_prompt:
            if "Observation:" in prompt:
                observation = prompt.rsplit("Observation:", 1)[-1].strip()
                return (
                    "Thought: Tôi đã nhận Observation và chỉ kết luận dựa trên dữ liệu của tool.\n"
                    f"Final Answer: {observation}"
                )
            lowered = prompt.lower()
            if "hãy đăng ký ngay" in lowered or ("comp3020" in lowered and "comp4890" in lowered):
                return (
                    "Thought: Cần kiểm tra prerequisite của các môn được yêu cầu trước khi lập kế hoạch.\n"
                    "Action: check_prerequisites['2A202601874', ['COMP3020', 'COMP2050', 'COMP4890']]"
                )
            if "trùng lịch" in lowered or "schedule" in lowered:
                return (
                    "Thought: Cần kiểm tra trực tiếp các mã môn được nêu trong lịch fixture.\n"
                    "Action: check_schedule_conflicts[['COMP2050', 'COMP3020']]"
                )
            if "tính tải tín chỉ" in lowered or "comp1020, math2010 và stat1010" in lowered:
                return (
                    "Thought: Cần cộng tín chỉ của danh sách môn và đối chiếu ngưỡng full-time.\n"
                    "Action: calculate_credit_load['2A202601874', ['COMP1020', 'MATH2010', 'STAT1010']]"
                )
            if "academic regulations" in lowered or "số trang" in lowered or "study load" in lowered:
                return (
                    "Thought: Cần tra cứu quy định chính thức về credit và study load.\n"
                    "Action: search_official_sources['credit study load']"
                )
            if "catalog fixture" in lowered or "môn thuộc hướng ai/ml" in lowered:
                return (
                    "Thought: Cần tra catalog theo lĩnh vực AI/ML.\n"
                    "Action: search_courses['AI/ML']"
                )
            if "comp1020" in lowered:
                return (
                    "Thought: Cần kiểm tra prerequisite của COMP1020 theo hồ sơ sinh viên.\n"
                    "Action: check_prerequisites['2A202601874', ['COMP1020']]"
                )
            if "comp2050" in lowered and "comp3020" not in lowered and "comp4890" not in lowered:
                return (
                    "Thought: Cần kiểm tra prerequisite riêng của COMP2050 theo hồ sơ sinh viên.\n"
                    "Action: check_prerequisites['2A202601874', ['COMP2050']]"
                )
            if "comp3020" in lowered or "comp4890" in lowered:
                return (
                    "Thought: Cần kiểm tra prerequisite của các môn được yêu cầu trước khi lập kế hoạch.\n"
                    "Action: check_prerequisites['2A202601874', ['COMP3020', 'COMP2050', 'COMP4890']]"
                )
            if "kế hoạch" in lowered or "15 đến 18" in lowered or "ai/ml" in lowered:
                return (
                    "Thought: Cần đề xuất kế hoạch dựa trên mục tiêu AI/ML và kiểm tra các điều kiện.\n"
                    "Action: recommend_course_plan['2A202601874', 'AI/ML']"
                )
            return (
                "Thought: Cần đọc hồ sơ học tập trước khi đưa ra tư vấn.\n"
                "Action: get_student_profile['2A202601874']"
            )
        return "🤖 [Mock Provider]: Phản hồi giả lập offline cho bài test học vụ."


def get_llm_provider(provider_name: str = None) -> BaseLLMProvider:
    """Factory function tự chọn Provider từ biến môi trường LLM_PROVIDER"""
    name = (provider_name or os.getenv("LLM_PROVIDER") or "mock").lower().strip()
    
    if name == "gemini":
        return GeminiProvider()
    elif name == "openai":
        return OpenAIProvider()
    elif name == "ollama":
        return OllamaProvider()
    elif name == "anthropic":
        return AnthropicProvider()
    elif name == "openrouter":
        return OpenRouterProvider()
    else:
        return MockProvider()


if __name__ == "__main__":
    print("=== TEST MULTI-PROVIDER LLM ADAPTER ===")
    provider = get_llm_provider()
    print(f"✅ Provider đang dùng: {provider.__class__.__name__}")
    print(f"🤖 User Query: Hello")
    print(f"💬 Response  : {provider.generate('Hello')}")
