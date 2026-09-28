import { copyFile, readFile, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const manifest = JSON.parse(await readFile(resolve(root, 'manifest.json'), 'utf8'));
const base = process.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';
const url = new URL(base);
if (!['https:', 'http:'].includes(url.protocol)) throw new Error('Invalid API URL');
if (url.protocol === 'http:' && !['localhost', '127.0.0.1'].includes(url.hostname)) {
  throw new Error('Production API URL must use HTTPS');
}
manifest.host_permissions = [`${url.protocol}//${url.hostname}/*`];
await writeFile(resolve(root, 'dist', 'manifest.json'), `${JSON.stringify(manifest, null, 2)}\n`);
for (const size of [16, 48, 128]) {
  await copyFile(resolve(root, `icon-${size}.png`), resolve(root, 'dist', `icon-${size}.png`));
}
