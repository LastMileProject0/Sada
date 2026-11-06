import arabicRegular from '@fontsource/noto-sans-arabic/files/noto-sans-arabic-arabic-400-normal.woff2?url';
import arabicBold from '@fontsource/noto-sans-arabic/files/noto-sans-arabic-arabic-700-normal.woff2?url';
import latinRegular from '@fontsource/noto-sans-arabic/files/noto-sans-arabic-latin-400-normal.woff2?url';
import latinBold from '@fontsource/noto-sans-arabic/files/noto-sans-arabic-latin-700-normal.woff2?url';

let cachedCSS: string | undefined;

async function localFont(url: string, signal: AbortSignal) {
  const controller = new AbortController();
  const abort = () => controller.abort();
  signal.addEventListener('abort', abort, { once: true });
  if (signal.aborted) abort();
  const timer = setTimeout(abort, 10000);
  try {
    // Public bundled assets only; no report data, cookies, CDN or font service.
    const resolved = new URL(url, window.location.href);
    if (resolved.origin !== window.location.origin) throw new Error('Nonlocal report font');
    const response = await fetch(resolved, { credentials: 'omit', signal: controller.signal });
    if (!response.ok) throw new Error('Report font unavailable');
    const bytes = new Uint8Array(await response.arrayBuffer());
    if (bytes.length < 100 || bytes.length > 2 * 1024 * 1024) throw new Error('Invalid report font');
    let binary = '';
    for (let i = 0; i < bytes.length; i += 8192) binary += String.fromCharCode(...bytes.subarray(i, i + 8192));
    return `data:font/woff2;base64,${btoa(binary)}`;
  } finally {
    clearTimeout(timer);
    signal.removeEventListener('abort', abort);
  }
}

export async function reportFontCSS(signal: AbortSignal) {
  signal.throwIfAborted();
  if (cachedCSS) return cachedCSS;
  const fonts = await Promise.all([
    localFont(arabicRegular, signal), localFont(arabicBold, signal),
    localFont(latinRegular, signal), localFont(latinBold, signal),
  ]);
  signal.throwIfAborted();
  cachedCSS = fonts.map((url, i) => `@font-face{font-family:${i < 2 ? 'SADAArabic' : 'SADALatin'};font-weight:${i % 2 ? 700 : 400};font-style:normal;src:url("${url}") format("woff2");}`).join('');
  return cachedCSS;
}
