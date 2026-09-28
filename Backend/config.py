"""Runtime configuration. Secrets are read only from the process environment."""

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    ai_provider: str = os.getenv("AI_PROVIDER", "cloudflare").lower()
    cloudflare_account_id: str = os.getenv("CLOUDFLARE_ACCOUNT_ID", "")
    cloudflare_api_token: str = os.getenv("CLOUDFLARE_API_TOKEN", "")
    cloudflare_text_model: str = os.getenv("CLOUDFLARE_TEXT_MODEL", "@cf/qwen/qwen3-30b-a3b-fp8")
    cloudflare_vision_model: str = os.getenv("CLOUDFLARE_VISION_MODEL", "@cf/meta/llama-3.2-11b-vision-instruct")
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "qwen2.5vl:3b")
    quota_backend: str = os.getenv("QUOTA_BACKEND", "upstash").lower()
    upstash_url: str = os.getenv("UPSTASH_REDIS_REST_URL", "")
    upstash_token: str = os.getenv("UPSTASH_REDIS_REST_TOKEN", "")
    session_secret: str = os.getenv("SESSION_SECRET", "")
    ai_disabled: bool = os.getenv("AI_DISABLED", "false").lower() in ("1", "true", "yes")
    allowed_origins: tuple[str, ...] = tuple(
        origin.strip() for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if origin.strip()
    )
    trust_proxy_headers: bool = os.getenv("TRUST_PROXY_HEADERS", "false").lower() in ("1", "true", "yes")
    session_daily_limit: int = max(1, int(os.getenv("SESSION_DAILY_LIMIT", "5")))
    ip_daily_limit: int = max(1, int(os.getenv("IP_DAILY_LIMIT", "20")))
    global_daily_limit: int = max(1, int(os.getenv("GLOBAL_DAILY_LIMIT", "100")))

    @property
    def ai_configured(self) -> bool:
        if self.ai_disabled:
            return False
        if self.ai_provider == "ollama":
            return bool(self.ollama_base_url and self.ollama_model)
        return self.ai_provider == "cloudflare" and bool(self.cloudflare_account_id and self.cloudflare_api_token)

    @property
    def quota_configured(self) -> bool:
        if self.quota_backend == "memory":
            return bool(self.session_secret)
        return self.quota_backend == "upstash" and bool(self.upstash_url and self.upstash_token and self.session_secret)


settings = Settings()
