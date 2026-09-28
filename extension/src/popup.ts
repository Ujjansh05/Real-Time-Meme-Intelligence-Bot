import { explain, remix, session, status, type Language, type Quota } from './api';
import { newEntry, save } from './store';

function element<T extends HTMLElement>(id: string): T { return document.getElementById(id) as T; }
const textInput = element<HTMLTextAreaElement>('memeText');
const imageInput = element<HTMLInputElement>('imageFile');
const preview = element<HTMLImageElement>('preview');
const result = element<HTMLDivElement>('result');
const favoriteButton = element<HTMLButtonElement>('saveFavorite');
let image: File | undefined;
let lastResult = '';
let previewUrl: string | undefined;

function quotaLabel(quota?: Quota) {
  if (!quota) return;
  const reset = quota.reset_at ? new Date(quota.reset_at).toLocaleString() : 'tomorrow';
  element('quota').textContent = `${quota.remaining} AI actions remaining · resets ${reset}`;
}
function showError(error: unknown) {
  result.textContent = error instanceof Error ? error.message : 'Something went wrong.';
  favoriteButton.classList.add('hidden');
}
function showImage(file: File) {
  if (!['image/png', 'image/jpeg', 'image/webp'].includes(file.type) || file.size > 5 * 1024 * 1024) {
    showError(new Error('Choose a PNG, JPEG, or WebP image up to 5 MB.')); return;
  }
  image = file;
  if (previewUrl) URL.revokeObjectURL(previewUrl);
  previewUrl = URL.createObjectURL(file);
  preview.src = previewUrl;
  preview.classList.remove('hidden');
}
imageInput.addEventListener('change', () => { if (imageInput.files?.[0]) showImage(imageInput.files[0]); });
document.addEventListener('paste', event => {
  const file = Array.from(event.clipboardData?.files || []).find(x => x.type.startsWith('image/'));
  if (file) { event.preventDefault(); showImage(file); }
});

async function act(kind: 'explain' | 'remix') {
  const buttons = [element<HTMLButtonElement>('explain'), element<HTMLButtonElement>('remix')];
  buttons.forEach(button => button.disabled = true);
  favoriteButton.disabled = false; favoriteButton.textContent = 'Save to favorites';
  result.textContent = 'Working…';
  favoriteButton.classList.add('hidden');
  try {
    const input = {
      text: textInput.value.trim(), image,
      file: image, language: element<HTMLSelectElement>('language').value as Language,
      topic: element<HTMLInputElement>('topic').value.trim(), tone: element<HTMLSelectElement>('tone').value,
    };
    const data = kind === 'explain' ? await explain(input) : await remix(input);
    lastResult = kind === 'explain' ? (data as { explanation: string }).explanation : (data as { variations: string[] }).variations.map((v, i) => `${i + 1}. ${v}`).join('\n\n');
    result.textContent = lastResult;
    favoriteButton.classList.remove('hidden');
    quotaLabel(data.quota);
    await save(newEntry('history', textInput.value.trim().slice(0, 80) || image?.name || 'Image meme', { input: textInput.value.trim(), result: lastResult }));
  } catch (error) { showError(error); }
  finally { buttons.forEach(button => button.disabled = false); }
}

element('explain').addEventListener('click', () => void act('explain'));
element('remix').addEventListener('click', () => void act('remix'));
favoriteButton.addEventListener('click', async () => {
  if (!lastResult) return;
  try {
    await save(newEntry('favorite', textInput.value.trim().slice(0, 80) || image?.name || 'Favorite meme', { input: textInput.value.trim(), result: lastResult }));
    favoriteButton.textContent = 'Saved ✓';
    favoriteButton.disabled = true;
  } catch (error) { showError(error); }
});
function openWorkspace(fragment = 'explain') { void chrome.tabs.create({ url: chrome.runtime.getURL(`app.html#${fragment}`) }); }
element('openWorkspace').addEventListener('click', () => openWorkspace());
element('openEditor').addEventListener('click', () => openWorkspace('editor'));
Promise.all([status(), session()]).then(([state, quota]) => {
  element('status').textContent = state.ai_available && state.quota_available ? 'AI service ready' : 'AI temporarily unavailable · editor still works';
  quotaLabel(quota);
}).catch(() => { element('status').textContent = 'Service unavailable · editor still works'; });
