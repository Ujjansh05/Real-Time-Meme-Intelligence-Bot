export type TextLayer = { id: string; text: string; x: number; y: number; size: number; color: string; outline: string };
export type LibraryEntry = {
  id: string;
  type: 'history' | 'favorite' | 'draft';
  title: string;
  created: number;
  input?: string;
  result?: string;
  image?: Blob;
  layers?: TextLayer[];
};

const DB_NAME = 'humour-hub-library';
function database(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const open = indexedDB.open(DB_NAME, 1);
    open.onupgradeneeded = () => {
      const store = open.result.createObjectStore('entries', { keyPath: 'id' });
      store.createIndex('type', 'type');
      store.createIndex('created', 'created');
    };
    open.onsuccess = () => resolve(open.result);
    open.onerror = () => reject(open.error);
  });
}
function transaction<T>(mode: IDBTransactionMode, callback: (store: IDBObjectStore, resolve: (value: T) => void, reject: (reason: unknown) => void) => void): Promise<T> {
  return database().then(db => new Promise<T>((resolve, reject) => {
    const tx = db.transaction('entries', mode);
    tx.oncomplete = () => db.close();
    tx.onerror = () => reject(tx.error);
    callback(tx.objectStore('entries'), resolve, reject);
  }));
}
export function save(entry: LibraryEntry): Promise<void> {
  return transaction('readwrite', (store, resolve, reject) => {
    const req = store.put(entry);
    req.onsuccess = () => resolve(); req.onerror = () => reject(req.error);
  });
}
export function get(id: string): Promise<LibraryEntry | undefined> {
  return transaction('readonly', (store, resolve, reject) => {
    const req = store.get(id);
    req.onsuccess = () => resolve(req.result as LibraryEntry | undefined); req.onerror = () => reject(req.error);
  });
}
export function all(): Promise<LibraryEntry[]> {
  return transaction('readonly', (store, resolve, reject) => {
    const req = store.getAll();
    req.onsuccess = () => resolve((req.result as LibraryEntry[]).sort((a, b) => b.created - a.created));
    req.onerror = () => reject(req.error);
  });
}
export function remove(id: string): Promise<void> {
  return transaction('readwrite', (store, resolve, reject) => {
    const req = store.delete(id); req.onsuccess = () => resolve(); req.onerror = () => reject(req.error);
  });
}
export function clear(): Promise<void> {
  return transaction('readwrite', (store, resolve, reject) => {
    const req = store.clear(); req.onsuccess = () => resolve(); req.onerror = () => reject(req.error);
  });
}
export function newEntry(type: LibraryEntry['type'], title: string, extra: Partial<LibraryEntry>): LibraryEntry {
  return { id: crypto.randomUUID(), type, title, created: Date.now(), ...extra };
}
function blobToDataUrl(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result as string); reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(blob);
  });
}
export async function exportLibrary(): Promise<Blob> {
  const entries = await all();
  const serialized = await Promise.all(entries.map(async entry => ({ ...entry, image: entry.image ? await blobToDataUrl(entry.image) : undefined })));
  return new Blob([JSON.stringify({ version: 1, entries: serialized })], { type: 'application/json' });
}
export async function importLibrary(file: File): Promise<number> {
  if (file.size > 25 * 1024 * 1024) throw new Error('Library file is too large.');
  const data = JSON.parse(await file.text());
  if (data.version !== 1 || !Array.isArray(data.entries)) throw new Error('Unsupported library file.');
  let count = 0;
  for (const candidate of data.entries.slice(0, 500)) {
    if (!candidate || !['history', 'favorite', 'draft'].includes(candidate.type) || typeof candidate.title !== 'string') continue;
    let image: Blob | undefined;
    if (typeof candidate.image === 'string' && /^data:image\/(png|jpeg|webp);base64,/.test(candidate.image)) {
      image = await (await fetch(candidate.image)).blob();
      if (image.size > 5 * 1024 * 1024) continue;
    }
    await save({
      id: crypto.randomUUID(), type: candidate.type, title: candidate.title.slice(0, 120), created: Date.now(),
      input: typeof candidate.input === 'string' ? candidate.input.slice(0, 4000) : undefined,
      result: typeof candidate.result === 'string' ? candidate.result.slice(0, 12000) : undefined,
      image,
      layers: Array.isArray(candidate.layers) ? candidate.layers.slice(0, 20).filter((x: any) => x && typeof x.text === 'string' && typeof x.x === 'number' && typeof x.y === 'number') : undefined,
    });
    count++;
  }
  return count;
}
