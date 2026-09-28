import { configuredBase, explain, getBase, remix, session, setBase, status, trends, type Language, type Quota, type TrendSource } from './api';
import { all, clear, exportLibrary, get, importLibrary, newEntry, remove, save, type LibraryEntry, type TextLayer } from './store';

function el<T extends HTMLElement>(id: string): T { return document.getElementById(id) as T; }
function message(error: unknown): string { return error instanceof Error ? error.message : 'Something went wrong.'; }
function download(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a'); anchor.href = url; anchor.download = filename; anchor.click();
  setTimeout(() => URL.revokeObjectURL(url), 30000);
}
function dateLabel(value?: string | number): string {
  if (!value) return 'Time unavailable';
  const date = new Date(value); return Number.isNaN(date.valueOf()) ? 'Time unavailable' : date.toLocaleString();
}
function quotaLabel(quota?: Quota) {
  if (quota) el('appQuota').textContent = `${quota.remaining} AI actions remaining · resets ${dateLabel(quota.reset_at)}`;
}
function switchView(view: string) {
  const name = ['explain', 'editor', 'library', 'trends'].includes(view) ? view : 'explain';
  for (const part of ['explain', 'editor', 'library', 'trends']) {
    el(`${part}View`).classList.toggle('hidden', part !== name);
    document.querySelector(`[data-view="${part}"]`)?.classList.toggle('active', part === name);
  }
  location.hash = name;
  if (name === 'library') void renderLibrary();
  if (name === 'trends') void renderTrends();
}
document.querySelectorAll<HTMLButtonElement>('[data-view]').forEach(button => button.addEventListener('click', () => switchView(button.dataset.view || 'explain')));
switchView(location.hash.slice(1));

// Explain and remix
let selectedFile: File | undefined;
let previewUrl: string | undefined;
let lastResult = '';
const result = el<HTMLDivElement>('appResult');
const favorite = el<HTMLButtonElement>('appFavorite');
const initialView = location.hash.slice(1);
function chooseImage(file: File) {
  if (!['image/png', 'image/jpeg', 'image/webp'].includes(file.type) || file.size > 5 * 1024 * 1024) {
    result.textContent = 'Choose a PNG, JPEG, or WebP image up to 5 MB.'; return;
  }
  selectedFile = file;
  if (previewUrl) URL.revokeObjectURL(previewUrl);
  previewUrl = URL.createObjectURL(file);
  const preview = el<HTMLImageElement>('appPreview'); preview.src = previewUrl; preview.classList.remove('hidden');
}
el<HTMLInputElement>('appFile').addEventListener('change', event => {
  const file = (event.target as HTMLInputElement).files?.[0]; if (file) chooseImage(file);
});
document.addEventListener('paste', event => {
  const file = Array.from(event.clipboardData?.files || []).find(x => x.type.startsWith('image/'));
  if (!file) return;
  event.preventDefault();
  if (location.hash === '#editor') void setEditorImage(file);
  else { switchView('explain'); chooseImage(file); }
});

async function runAi(kind: 'explain' | 'remix') {
  if (!el<HTMLInputElement>('appAiConsent').checked) {
    result.textContent = 'Agree to send your selected content for AI processing first.';
    return;
  }
  const controls = [el<HTMLButtonElement>('appExplain'), el<HTMLButtonElement>('appRemix')];
  controls.forEach(x => x.disabled = true);
  favorite.disabled = false; favorite.textContent = 'Save result to favorites';
  favorite.classList.add('hidden'); result.textContent = 'Working…';
  try {
    const text = el<HTMLTextAreaElement>('appText').value.trim();
    const input = { text, file: selectedFile, language: el<HTMLSelectElement>('appLanguage').value as Language, topic: el<HTMLInputElement>('appTopic').value.trim(), tone: el<HTMLSelectElement>('appTone').value };
    const data = kind === 'explain' ? await explain(input) : await remix(input);
    lastResult = kind === 'explain' ? (data as { explanation: string }).explanation : (data as { variations: string[] }).variations.map((v, i) => `${i + 1}. ${v}`).join('\n\n');
    result.textContent = lastResult;
    favorite.classList.remove('hidden');
    quotaLabel(data.quota);
    await save(newEntry('history', text.slice(0, 80) || selectedFile?.name || 'Image meme', { input: text, result: lastResult }));
  } catch (error) { result.textContent = message(error); }
  finally { controls.forEach(x => x.disabled = false); }
}
el('appExplain').addEventListener('click', () => void runAi('explain'));
el('appRemix').addEventListener('click', () => void runAi('remix'));
favorite.addEventListener('click', async () => {
  if (!lastResult) return;
  try {
    const text = el<HTMLTextAreaElement>('appText').value.trim();
    await save(newEntry('favorite', text.slice(0, 80) || selectedFile?.name || 'Favorite meme', { input: text, result: lastResult }));
    favorite.textContent = 'Saved ✓'; favorite.disabled = true;
  } catch (error) { result.textContent = message(error); }
});

// Local image editor
const canvas = el<HTMLCanvasElement>('editorCanvas');
const ctx = canvas.getContext('2d')!;
let editorImage: HTMLImageElement | undefined;
let editorBlob: Blob | undefined;
let layers: TextLayer[] = [];
let selectedLayer = '';
let draftId: string | undefined;
let undoStack: TextLayer[][] = [];
let redoStack: TextLayer[][] = [];
let saveTimer: ReturnType<typeof setTimeout> | undefined;
function snapshot() { undoStack.push(structuredClone(layers)); if (undoStack.length > 40) undoStack.shift(); redoStack = []; }
function currentLayer(): TextLayer | undefined { return layers.find(x => x.id === selectedLayer); }
function drawEditor() {
  const w = canvas.width, h = canvas.height;
  ctx.fillStyle = '#ffffff'; ctx.fillRect(0, 0, w, h);
  if (editorImage) ctx.drawImage(editorImage, 0, 0, w, h);
  ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.lineJoin = 'round';
  for (const layer of layers) {
    ctx.font = `800 ${layer.size}px Impact, Arial Black, sans-serif`;
    ctx.fillStyle = layer.color; ctx.strokeStyle = layer.outline; ctx.lineWidth = Math.max(3, layer.size / 10);
    const words = layer.text.split(/\s+/); const lines: string[] = []; let line = '';
    for (const word of words) {
      const next = line ? `${line} ${word}` : word;
      if (line && ctx.measureText(next).width > w * .9) { lines.push(line); line = word; } else line = next;
    }
    if (line) lines.push(line);
    if (!lines.length) continue;
    const lineHeight = layer.size * 1.08; const y0 = layer.y * h - (lines.length - 1) * lineHeight / 2;
    lines.forEach((text, index) => {
      const y = y0 + index * lineHeight;
      ctx.strokeText(text, layer.x * w, y, w * .95);
      ctx.fillText(text, layer.x * w, y, w * .95);
    });
  }
}
function syncLayerControls() {
  const select = el<HTMLSelectElement>('layerSelect'); select.replaceChildren();
  layers.forEach((layer, i) => { const option = new Option(layer.text.slice(0, 30) || `Text ${i + 1}`, layer.id); select.add(option); });
  if (!currentLayer() && layers[0]) selectedLayer = layers[0].id;
  select.value = selectedLayer;
  const layer = currentLayer();
  el<HTMLTextAreaElement>('layerText').value = layer?.text || '';
  el<HTMLInputElement>('fontSize').value = String(layer?.size || 54);
  el<HTMLInputElement>('fontColor').value = layer?.color || '#ffffff';
  el<HTMLInputElement>('outlineColor').value = layer?.outline || '#000000';
}
function queueDraft() { if (saveTimer) clearTimeout(saveTimer); saveTimer = setTimeout(() => void saveEditorDraft(), 500); }
async function saveEditorDraft() {
  try {
    draftId ||= crypto.randomUUID();
    await save({ id: draftId, type: 'draft', title: layers[0]?.text.slice(0, 80) || 'Untitled meme', created: Date.now(), image: editorBlob, layers: structuredClone(layers) });
    await chrome.storage.local.set({ editorDraftId: draftId });
    el('editorMessage').textContent = 'Draft saved on this device.';
  } catch (error) { el('editorMessage').textContent = message(error); }
}
async function setEditorImage(file: File | Blob) {
  if (!['image/png', 'image/jpeg', 'image/webp'].includes(file.type) || file.size > 5 * 1024 * 1024) {
    el('editorMessage').textContent = 'Choose a PNG, JPEG, or WebP image up to 5 MB.'; return;
  }
  const url = URL.createObjectURL(file);
  const image = new Image();
  try {
    await new Promise<void>((resolve, reject) => { image.onload = () => resolve(); image.onerror = () => reject(new Error('Cannot read image.')); image.src = url; });
    if (image.naturalWidth * image.naturalHeight > 20_000_000) throw new Error('Image has too many pixels.');
    editorImage = image; editorBlob = file;
    const scale = Math.min(900 / image.naturalWidth, 900 / image.naturalHeight);
    canvas.width = Math.max(1, Math.round(image.naturalWidth * scale));
    canvas.height = Math.max(1, Math.round(image.naturalHeight * scale));
    drawEditor(); queueDraft();
  } catch (error) { el('editorMessage').textContent = message(error); }
  finally { URL.revokeObjectURL(url); }
}
el<HTMLInputElement>('editorFile').addEventListener('change', event => {
  const file = (event.target as HTMLInputElement).files?.[0]; if (file) void setEditorImage(file);
});
el('useTemplate').addEventListener('click', async () => {
  const template = el<HTMLSelectElement>('templateSelect').value;
  const surface = document.createElement('canvas'); surface.width = 900; surface.height = 900;
  const brush = surface.getContext('2d')!;
  if (template === 'split') {
    brush.fillStyle = '#f4a394'; brush.fillRect(0, 0, 450, 900);
    brush.fillStyle = '#647ddc'; brush.fillRect(450, 0, 450, 900);
    brush.fillStyle = '#f9e5c8'; brush.beginPath(); brush.arc(235, 475, 145, 0, Math.PI * 2); brush.fill();
    brush.fillStyle = '#b7daf0'; brush.beginPath(); brush.arc(665, 475, 145, 0, Math.PI * 2); brush.fill();
    brush.fillStyle = '#483d52';
    for (const cx of [190, 280, 620, 710]) { brush.beginPath(); brush.arc(cx, 440, 10, 0, Math.PI * 2); brush.fill(); }
    brush.lineWidth = 12; brush.strokeStyle = '#483d52';
    brush.beginPath(); brush.arc(235, 495, 50, .1, Math.PI - .1); brush.stroke();
    brush.beginPath(); brush.moveTo(620, 540); brush.lineTo(710, 540); brush.stroke();
  } else if (template === 'spotlight') {
    const gradient = brush.createRadialGradient(450, 450, 70, 450, 450, 650);
    gradient.addColorStop(0, '#faac65'); gradient.addColorStop(.55, '#ac509a'); gradient.addColorStop(1, '#282654');
    brush.fillStyle = gradient; brush.fillRect(0, 0, 900, 900);
    brush.fillStyle = '#ffe7ba'; brush.beginPath(); brush.arc(450, 475, 175, 0, Math.PI * 2); brush.fill();
    brush.fillStyle = '#281e45'; brush.beginPath(); brush.arc(450, 475, 120, 0, Math.PI * 2); brush.fill();
    brush.strokeStyle = '#fff2cc'; brush.lineWidth = 8;
    for (const [x, y] of [[115, 160], [775, 195], [150, 735], [750, 700]]) {
      brush.beginPath(); brush.moveTo(x - 18, y); brush.lineTo(x + 18, y); brush.moveTo(x, y - 18); brush.lineTo(x, y + 18); brush.stroke();
    }
  } else {
    brush.fillStyle = '#20283c'; brush.fillRect(0, 0, 900, 900);
    const colors = ['#84c6d4', '#f4a487', '#dac37b', '#a7a2d9'];
    colors.forEach((color, index) => {
      const x = 28 + (index % 2) * 430, y = 28 + Math.floor(index / 2) * 430;
      brush.fillStyle = color; brush.fillRect(x, y, 412, 412);
      brush.fillStyle = '#fff8e9'; brush.beginPath(); brush.ellipse(x + 208, y + 210, 130, 88, 0, 0, Math.PI * 2); brush.fill();
      brush.beginPath(); brush.moveTo(x + 130, y + 260); brush.lineTo(x + 100, y + 335); brush.lineTo(x + 202, y + 288); brush.fill();
    });
  }
  const blob = await new Promise<Blob | null>(resolve => surface.toBlob(resolve, 'image/png'));
  if (blob) await setEditorImage(blob);
});
el('addText').addEventListener('click', () => {
  snapshot(); const layer: TextLayer = { id: crypto.randomUUID(), text: 'YOUR CAPTION', x: .5, y: layers.length ? .85 : .15, size: 54, color: '#ffffff', outline: '#000000' };
  layers.push(layer); selectedLayer = layer.id; syncLayerControls(); drawEditor(); queueDraft();
});
el<HTMLSelectElement>('layerSelect').addEventListener('change', event => { selectedLayer = (event.target as HTMLSelectElement).value; syncLayerControls(); });
for (const [id, field] of [['layerText', 'text'], ['fontSize', 'size'], ['fontColor', 'color'], ['outlineColor', 'outline']] as const) {
  el<HTMLInputElement>(id).addEventListener('change', event => {
    const layer = currentLayer(); if (!layer) return; snapshot();
    const value = (event.target as HTMLInputElement).value;
    if (field === 'size') layer.size = Math.min(120, Math.max(16, Number(value) || 54));
    else layer[field] = value;
    syncLayerControls(); drawEditor(); queueDraft();
  });
}
el('removeText').addEventListener('click', () => { if (!currentLayer()) return; snapshot(); layers = layers.filter(x => x.id !== selectedLayer); selectedLayer = layers[0]?.id || ''; syncLayerControls(); drawEditor(); queueDraft(); });
el('undo').addEventListener('click', () => { if (!undoStack.length) return; redoStack.push(structuredClone(layers)); layers = undoStack.pop()!; selectedLayer = layers[0]?.id || ''; syncLayerControls(); drawEditor(); queueDraft(); });
el('redo').addEventListener('click', () => { if (!redoStack.length) return; undoStack.push(structuredClone(layers)); layers = redoStack.pop()!; selectedLayer = layers[0]?.id || ''; syncLayerControls(); drawEditor(); queueDraft(); });
let dragging = false;
canvas.addEventListener('pointerdown', event => {
  if (!layers.length) return;
  const rect = canvas.getBoundingClientRect();
  const x = (event.clientX - rect.left) / rect.width, y = (event.clientY - rect.top) / rect.height;
  let nearest = layers[0]; let distance = Infinity;
  for (const layer of layers) { const d = Math.hypot((layer.x - x) * canvas.width, (layer.y - y) * canvas.height); if (d < distance) { nearest = layer; distance = d; } }
  if (distance > 140) return;
  snapshot(); selectedLayer = nearest.id; dragging = true; canvas.setPointerCapture(event.pointerId); syncLayerControls();
});
canvas.addEventListener('pointermove', event => {
  if (!dragging) return; const layer = currentLayer(); if (!layer) return;
  const rect = canvas.getBoundingClientRect(); layer.x = Math.min(.95, Math.max(.05, (event.clientX - rect.left) / rect.width)); layer.y = Math.min(.95, Math.max(.05, (event.clientY - rect.top) / rect.height)); drawEditor();
});
canvas.addEventListener('pointerup', () => { if (dragging) { dragging = false; queueDraft(); } });
canvas.addEventListener('keydown', event => {
  const layer = currentLayer(); if (!layer || !['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown'].includes(event.key)) return;
  event.preventDefault(); snapshot();
  const step = event.shiftKey ? .05 : .01;
  if (event.key === 'ArrowLeft') layer.x = Math.max(.05, layer.x - step);
  if (event.key === 'ArrowRight') layer.x = Math.min(.95, layer.x + step);
  if (event.key === 'ArrowUp') layer.y = Math.max(.05, layer.y - step);
  if (event.key === 'ArrowDown') layer.y = Math.min(.95, layer.y + step);
  drawEditor(); queueDraft();
});
el('saveDraft').addEventListener('click', () => void saveEditorDraft());
el('exportPng').addEventListener('click', () => {
  canvas.toBlob(blob => { if (blob) download(blob, 'humour-hub-meme.png'); else el('editorMessage').textContent = 'Could not export PNG.'; }, 'image/png');
});
async function loadDraft(entry: LibraryEntry, navigate = true) {
  if (entry.type !== 'draft') return;
  draftId = entry.id; layers = structuredClone(entry.layers || []); selectedLayer = layers[0]?.id || '';
  if (entry.image) await setEditorImage(entry.image);
  else { editorImage = undefined; editorBlob = undefined; canvas.width = 900; canvas.height = 900; }
  undoStack = []; redoStack = []; syncLayerControls(); drawEditor(); if (navigate) switchView('editor');
}
async function restoreDraft() {
  const { editorDraftId } = await chrome.storage.local.get('editorDraftId');
  if (typeof editorDraftId === 'string') { const entry = await get(editorDraftId); if (entry?.type === 'draft') await loadDraft(entry, false); }
  if (!layers.length) { layers = [{ id: crypto.randomUUID(), text: 'YOUR CAPTION', x: .5, y: .15, size: 54, color: '#ffffff', outline: '#000000' }]; selectedLayer = layers[0].id; syncLayerControls(); drawEditor(); }
}
void restoreDraft().then(() => switchView(initialView));

// Local library
async function renderLibrary() {
  const list = el<HTMLDivElement>('libraryList'); list.replaceChildren();
  try {
    const query = el<HTMLInputElement>('librarySearch').value.trim().toLowerCase();
    const entries = (await all()).filter(x => `${x.title} ${x.input || ''} ${x.result || ''}`.toLowerCase().includes(query));
    if (!entries.length) { const p = document.createElement('p'); p.className = 'muted'; p.textContent = 'No saved items here yet.'; list.append(p); return; }
    for (const entry of entries) {
      const card = document.createElement('article'); card.className = 'library-item';
      const type = document.createElement('span'); type.className = 'badge'; type.textContent = entry.type;
      const title = document.createElement('h3'); title.textContent = entry.title;
      const timestamp = document.createElement('small'); timestamp.className = 'muted'; timestamp.textContent = dateLabel(entry.created);
      const body = document.createElement('p'); body.textContent = entry.result || entry.input || 'Editable draft';
      const actions = document.createElement('div'); actions.className = 'actions';
      if (entry.type === 'draft') { const open = document.createElement('button'); open.className = 'secondary'; open.textContent = 'Edit'; open.addEventListener('click', () => void loadDraft(entry)); actions.append(open); }
      else { const open = document.createElement('button'); open.className = 'secondary'; open.textContent = 'View'; open.addEventListener('click', () => { el<HTMLTextAreaElement>('appText').value = entry.input || ''; result.textContent = entry.result || ''; switchView('explain'); }); actions.append(open); }
      const del = document.createElement('button'); del.className = 'danger'; del.textContent = 'Delete'; del.setAttribute('aria-label', `Delete ${entry.title}`); del.addEventListener('click', async () => { await remove(entry.id); await renderLibrary(); }); actions.append(del);
      card.append(type, title, timestamp, body, actions); list.append(card);
    }
  } catch (error) { list.textContent = message(error); }
}
el('librarySearch').addEventListener('input', () => void renderLibrary());
el('exportLibrary').addEventListener('click', async () => { try { download(await exportLibrary(), 'humour-hub-library.json'); } catch (error) { el('libraryList').textContent = message(error); } });
el<HTMLInputElement>('importLibrary').addEventListener('change', async event => {
  const file = (event.target as HTMLInputElement).files?.[0]; if (!file) return;
  try { const count = await importLibrary(file); await renderLibrary(); el('libraryList').prepend(document.createTextNode(`Imported ${count} items. `)); }
  catch (error) { el('libraryList').textContent = message(error); }
});
el('clearLibrary').addEventListener('click', async () => {
  if (!confirm('Delete all local history, favorites, and drafts?')) return;
  await clear(); draftId = undefined; await chrome.storage.local.remove('editorDraftId'); await renderLibrary();
});

// Source labeled discovery
function renderSource(source: TrendSource): HTMLElement {
  const card = document.createElement('section'); card.className = 'panel';
  const title = document.createElement('h2'); title.textContent = source.label || source.source;
  const timestamp = document.createElement('p'); timestamp.className = 'muted'; timestamp.textContent = `Collected ${dateLabel(source.observed_at)}${source.stale ? ' · Stale data' : ''}`;
  card.append(title, timestamp);
  if (!source.items?.length) { const empty = document.createElement('p'); empty.className = 'muted'; empty.textContent = source.status === 'insufficient_data' ? 'Gathering enough observations to compare growth.' : source.status === 'unavailable' ? 'This source is unavailable right now.' : 'No trends to show yet.'; card.append(empty); }
  else for (const item of source.items) {
    const row = document.createElement('div'); row.className = 'trend-item';
    const link = document.createElement('a'); link.textContent = item.title; link.href = item.url; link.target = '_blank'; link.rel = 'noopener noreferrer';
    if (!/^https:\/\//.test(item.url)) { link.removeAttribute('href'); }
    const score = Number.isFinite(item.score) ? (source.source === 'wikipedia' ? `${item.score >= 0 ? '+' : ''}${(item.score * 100).toFixed(1)}%` : `+${Math.round(item.score)}`) : '—';
    const info = document.createElement('small'); info.textContent = `${item.score_label || (source.source === 'wikipedia' ? 'Readership growth' : 'Engagement gained')}: ${score} · ${dateLabel(item.observed_at || source.observed_at)}`;
    row.append(link, info); card.append(row);
  }
  return card;
}
async function renderTrends() {
  const container = el<HTMLDivElement>('trendSources'); container.textContent = 'Loading source data…';
  try {
    const data = await trends(); container.replaceChildren();
    for (const source of data.sources || []) container.append(renderSource(source));
    if (!data.sources?.length) container.textContent = 'No sources are enabled yet.';
  } catch (error) { container.textContent = message(error); }
}
el('refreshTrends').addEventListener('click', () => void renderTrends());

// Settings and startup
el('themeToggle').addEventListener('click', async () => { document.body.classList.toggle('dark'); await chrome.storage.local.set({ theme: document.body.classList.contains('dark') ? 'dark' : 'light' }); });
el('saveApiBase').addEventListener('click', async () => {
  try { await setBase(el<HTMLInputElement>('apiBase').value); el('settingsMessage').textContent = 'Service URL saved.'; await checkService(); }
  catch (error) { el('settingsMessage').textContent = message(error); }
});
async function checkService() {
  try {
    const [state, quota] = await Promise.all([status(), session()]);
    el('serviceStatus').textContent = state.ai_available && state.quota_available ? `AI service ready (${state.ai_provider === 'ollama' ? 'local model' : state.ai_provider === 'cloudflare' ? 'Cloudflare' : 'configured provider'}).` : 'AI is temporarily unavailable. The editor and library still work.';
    quotaLabel(quota);
  } catch (error) { el('serviceStatus').textContent = `Service unavailable: ${message(error)} The editor and library still work.`; }
}
async function start() {
  const settings = await chrome.storage.local.get(['theme', 'pendingContext']);
  document.body.classList.toggle('dark', settings.theme === 'dark');
  el<HTMLInputElement>('apiBase').value = await getBase() || configuredBase();
  if (settings.pendingContext) {
    const context = settings.pendingContext as { action: string; text?: string };
    await chrome.storage.local.remove('pendingContext');
    switchView('explain');
    el<HTMLTextAreaElement>('appText').value = context.text || '';
    result.textContent = `Selected text is ready to ${context.action}. Review it, then choose an action.`;
  }
  await checkService();
}
void start();
