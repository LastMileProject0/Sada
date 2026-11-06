import type { ReportBlock } from './report-pdf-content';

export const PAGE_WIDTH = 794, PAGE_HEIGHT = 1123, MAX_PAGES = 48;
const css = `
*{box-sizing:border-box}
body{margin:0;background:white;color:#14213d;font-family:SADALatin,SADAArabic,sans-serif}
.pdf-page{position:relative;width:794px;height:1123px;background:white;padding:80px 42px 50px;overflow:hidden}
.pdf-header{position:absolute;top:0;left:0;right:0;height:61px;background:#101c36;color:#fff;display:flex;align-items:center;justify-content:space-between;padding:10px 42px;border-bottom:4px solid #18c8d1;font-size:15px;font-weight:700}
.pdf-header span:last-child{font-size:11px;color:#d6cef5}
.pdf-footer{position:absolute;bottom:15px;left:42px;right:42px;border-top:1px solid #a8b7cc;padding-top:6px;font-size:10px;display:flex;justify-content:space-between;color:#405578}
.pdf-content{height:993px;overflow:hidden;font-size:13px;line-height:1.65;display:flow-root}
[dir=rtl] .pdf-content{font-size:14px;line-height:1.75}
h1{font-size:25px;color:#101c36;line-height:1.6;margin:6px 0 12px}
h2{font-size:17px;color:#173b65;border-bottom:2px solid #18c8d1;margin:14px 0 8px;padding-bottom:4px;line-height:1.6}
h3{font-size:14px;color:#634198;margin:10px 0 5px;line-height:1.7}
h4{font-size:13px;color:#173b65;margin:9px 0 4px;line-height:1.7}
p,li{margin:5px 0;white-space:pre-wrap;overflow-wrap:anywhere}
li{display:block;padding-inline-start:12px;border-inline-start:2px solid #c1dfe6}
.warning{border-inline-start:3px solid #18c8d1;background:#f0f8fc;padding:10px 13px;margin:8px 0;font-size:12px}
.provenance{font-weight:700;color:#173b65}
table{border-collapse:collapse;table-layout:fixed;width:100%;margin:7px 0;overflow-wrap:anywhere;line-height:1.65;font-size:12px}
[dir=rtl] table{font-size:13px}
th,td{border:1px solid #cbd5e1;padding:6px 8px;text-align:start;vertical-align:top;white-space:pre-wrap}
th{width:47%;background:#f0f3f9;font-weight:700;color:#173b65}
.comparison th,.comparison td{width:auto;font-size:11px;padding:6px}
.comparison thead th{background:#173b65;color:#fff;font-weight:700}
`;

export async function paginateReport(blocks: ReportBlock[], language: 'en' | 'ar',
  title: string, fonts: string, signal: AbortSignal) {
  const frame = document.createElement('iframe');
  frame.setAttribute('sandbox', 'allow-same-origin');
  frame.setAttribute('aria-hidden', 'true');
  frame.tabIndex = -1;
  Object.assign(frame.style, { position: 'fixed', left: '-100000px', top: '0', width: '794px', height: '1123px', border: '0' });
  const loaded = new Promise<void>((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error('Report rendering timed out')), 10000);
    frame.onload = () => { clearTimeout(timer); resolve(); };
    frame.onerror = () => { clearTimeout(timer); reject(new Error('Report rendering unavailable')); };
  });
  frame.srcdoc = `<!doctype html><html lang="${language}" dir="${language === 'ar' ? 'rtl' : 'ltr'}"><head><meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; font-src data:; img-src data:; base-uri 'none'; form-action 'none'"><style>${fonts}${css}</style></head><body></body></html>`;
  document.body.append(frame);
  try {
    await loaded;
    signal.throwIfAborted();
    const doc = frame.contentDocument!;
    await Promise.all(['400', '700'].flatMap(weight => [
      doc.fonts.load(`${weight} 14px SADAArabic`, 'تقرير التقييم'),
      doc.fonts.load(`${weight} 14px SADALatin`, 'SADA Report'),
    ]));
    if (doc.fonts.size < 4) throw new Error('Report fonts unavailable');
    const pages: HTMLElement[] = [];
    let content: HTMLElement;
    let section = title;
    let subheading: HTMLElement | undefined;
    const addPage = () => {
      if (pages.length >= MAX_PAGES) throw new Error('Report exceeds PDF page limit; use HTML');
      const page = doc.createElement('div');
      page.className = 'pdf-page';
      page.dir = language === 'ar' ? 'rtl' : 'ltr';
      const header = doc.createElement('div');
      header.className = 'pdf-header'; header.dir = 'ltr';
      for (const text of ['صدى | SADA', section === title ? title : `${title} — ${section}`]) {
        const span = doc.createElement('span'); span.textContent = text; header.append(span);
      }
      content = doc.createElement('div'); content.className = 'pdf-content';
      const footer = doc.createElement('div'); footer.className = 'pdf-footer';
      page.append(header, content, footer); doc.body.append(page); pages.push(page);
    };
    addPage();
    const append = (block: ReportBlock) => {
      const last = content.lastElementChild as HTMLTableElement | null;
      if (block.table && last?.dataset.table === String(block.table)) {
        const row = block.node.querySelector('tr')!.cloneNode(true);
        last.tBodies[0].append(row);
        return () => row.parentNode?.removeChild(row);
      }
      const node = block.node.cloneNode(true) as HTMLElement;
      if (block.table) {
        node.dataset.table = String(block.table);
        if (block.tableHeader) node.prepend(block.tableHeader.cloneNode(true));
      }
      content.append(node);
      return () => node.remove();
    };
    let pending: ReportBlock[] = [];
    for (const block of blocks) {
      signal.throwIfAborted();
      if (block.heading) {
        if (block.node.tagName === 'H2') { section = block.node.textContent ?? title; subheading = undefined; }
        if (block.node.tagName === 'H4') subheading = block.node;
        pending.push(block); continue;
      }
      const group = [...pending, block];
      pending = [];
      const wasEmpty = !content!.children.length;
      const undo = group.map(append);
      if (content!.scrollHeight > content!.clientHeight) {
        undo.reverse().forEach(remove => remove());
        if (wasEmpty) throw new Error('Report block exceeds printable area; use HTML');
        addPage();
        if (!group.some(b => b.heading) && block.table && subheading) {
          content!.append(subheading.cloneNode(true));
        }
        group.forEach(append);
        if (content!.scrollHeight > content!.clientHeight) throw new Error('Report block exceeds printable area; use HTML');
      }
    }
    // No silent dropped headings or clipped content.
    if (pending.length) throw new Error('Incomplete report layout; use HTML');
    for (const [index, page] of pages.entries()) {
      const footer = page.querySelector('.pdf-footer')!;
      for (const text of ['SADA', language === 'ar' ? `صفحة ${index + 1} من ${pages.length}` : `Page ${index + 1} / ${pages.length}`]) {
        const span = doc.createElement('span'); span.textContent = text; footer.append(span);
      }
    }
    return { pages, dispose: () => frame.remove() };
  } catch (error) {
    frame.remove();
    throw error;
  }
}
