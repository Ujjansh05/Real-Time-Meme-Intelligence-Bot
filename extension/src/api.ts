export type Language = 'en' | 'hi' | 'hinglish';
export type Quota = { remaining: number; reset_at: string };
export type TrendItem = { title: string; url: string; score: number; score_label?: string; observed_at?: string; source?: string };
export type TrendSource = { source: string; label: string; observed_at?: string; stale: boolean; status: 'ok' | 'insufficient_data' | 'unavailable' | 'stale'; items: TrendItem[] };
export type Trends = { sources: TrendSource[]; generated_at?: string };
export type Status = { status: string; ai_provider?: 'cloudflare' | 'ollama'; ai_available: boolean; quota_available: boolean };

const defaultBase = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';
let token: string | undefined;

export async function getBase(): Promise<string> {
  const settings = await chrome.storage.local.get('apiBase');
  return (settings.apiBase as string | undefined) || defaultBase;
}

export function configuredBase(): string { return defaultBase; }

export async function setBase(value: string): Promise<void> {
  const parsed = new URL(value.trim());
  if (parsed.protocol !== 'https:' && !(['localhost', '127.0.0.1'].includes(parsed.hostname) && parsed.protocol === 'http:')) {
    throw new Error('Use an HTTPS URL, or HTTP for localhost development.');
  }
  const base = parsed.origin + parsed.pathname.replace(/\/$/, '');
  if (base !== defaultBase) {
    const granted = await chrome.permissions.request({ origins: [`${parsed.protocol}//${parsed.hostname}/*`] });
    if (!granted) throw new Error('Connection permission was declined.');
  }
  await chrome.storage.local.set({ apiBase: base });
  token = undefined;
  await chrome.storage.local.remove('sessionToken');
}

async function request(path: string, init: RequestInit = {}, authenticated = false, retry = true): Promise<any> {
  const base = await getBase();
  const headers = new Headers(init.headers);
  if (authenticated) {
    if (!token) {
      const saved = await chrome.storage.local.get('sessionToken');
      token = saved.sessionToken as string | undefined;
    }
    if (!token) await session();
    headers.set('Authorization', `Bearer ${token}`);
  }
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), authenticated ? 150000 : 25000);
  try {
    const response = await fetch(`${base}${path}`, { ...init, headers, signal: controller.signal });
    const data = await response.json().catch(() => null);
    if (!response.ok) {
      if (response.status === 401 && authenticated) {
        token = undefined;
        await chrome.storage.local.remove('sessionToken');
        if (retry) { await session(); return request(path, init, true, false); }
      }
      throw new Error(data?.error?.message || `Service returned ${response.status}.`);
    }
    return data;
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') throw new Error('The service timed out. Try again.');
    if (error instanceof TypeError) throw new Error('Cannot reach the service. Check your connection and service URL.');
    throw error;
  } finally { clearTimeout(timeout); }
}

export async function session(): Promise<Quota> {
  const data = await request('/api/v1/session', { method: 'POST' });
  token = data.token;
  if (typeof token !== 'string' || !token) throw new Error('Service did not issue a session.');
  await chrome.storage.local.set({ sessionToken: token });
  return data.quota;
}

export async function status(): Promise<Status> { return request('/api/v1/status'); }
export async function trends(): Promise<Trends> { return request('/api/v1/trends'); }

export type MemeInput = { text?: string; file?: File; language: Language; topic?: string; tone?: string };
async function ai(path: string, input: MemeInput): Promise<any> {
  if (input.file && input.file.size > 5 * 1024 * 1024) throw new Error('Image must be 5 MB or smaller.');
  if ((input.text || '').length > 4000) throw new Error('Text must be 4,000 characters or fewer.');
  if (!input.file && !input.text?.trim()) throw new Error('Add text or an image first.');
  if (input.file) {
    const form = new FormData();
    form.set('file', input.file);
    if (input.text) form.set('text', input.text);
    form.set('language', input.language);
    if (input.topic) form.set('topic', input.topic);
    if (input.tone) form.set('tone', input.tone);
    return request(path, { method: 'POST', body: form }, true);
  }
  return request(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text: input.text, language: input.language, topic: input.topic, tone: input.tone }),
  }, true);
}

export async function explain(input: MemeInput): Promise<{ explanation: string; quota?: Quota }> {
  return ai('/api/v1/explain', input);
}
export async function remix(input: MemeInput): Promise<{ variations: string[]; quota?: Quota }> {
  return ai('/api/v1/remix', input);
}
