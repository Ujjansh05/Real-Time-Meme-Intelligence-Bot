"""Runtime configuration. Secrets are read only from the process environment."""

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    cloudflare_account_id: str = os.getenv("CLOUDFLARE_ACCOUNT_ID", "")
    cloudflare_api_token: str = os.getenv("CLOUDFLARE_API_TOKEN", "")
    cloudflare_text_model: str = os.getenv("CLOUDFLARE_TEXT_MODEL", "@cf/qwen/qwen3-30b-a3b-fp8")
    cloudflare_vision_model: str = os.getenv("CLOUDFLARE_VISION_MODEL", "@cf/meta/llama-3.2-11b-vision-instruct")
    upstash_url: str = os.getenv("UPSTASH_REDIS_REST_URL", "")
    upstash_token: str = os.getenv("UPSTASH_REDIS_REST_TOKEN", "")
    session_secret: str = os.getenv("SESSION_SECRET", "")
    ai_disabled: bool = os.getenv("AI_DISABLED", "false").lower() in ("1", "true", "yes")
    allowed_origins: tuple[str, ...] = tuple(
        origin.strip() for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if origin.strip()
    )
    trust_proxy_headers: bool = os.getenv("TRUST_PROXY_HEADERS", "false").lower() in ("1", "true", "yes")
    session_daily_limit: int = 5
    ip_daily_limit: int = 20
    global_daily_limit: int = 100

    @property
    def ai_configured(self) -> bool:
        return bool(self.cloudflare_account_id and self.cloudflare_api_token and not self.ai_disabled)

    @property
    def quota_configured(self) -> bool:
        return bool(self.upstash_url and self.upstash_token and self.session_secret)


settings = Settings()
