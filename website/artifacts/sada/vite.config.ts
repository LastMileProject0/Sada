import path from 'path';
import { existsSync, realpathSync } from 'node:fs';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
import { defineConfig, type Plugin } from 'vite';

import runtimeErrorOverlay from '@replit/vite-plugin-runtime-error-modal';

const rawPort = process.env.PORT;

if (!rawPort) {
  throw new Error(
    'PORT environment variable is required but was not provided.',
  );
}

const port = Number(rawPort);

if (Number.isNaN(port) || port <= 0) {
  throw new Error(`Invalid PORT value: "${rawPort}"`);
}

const basePath = process.env.BASE_PATH;

if (!basePath) {
  throw new Error(
    'BASE_PATH environment variable is required but was not provided.',
  );
}

// Do not allow Vite's workspace-root discovery to expose backend resources.
const frontendRoots = [
  path.resolve(import.meta.dirname),
  path.resolve(import.meta.dirname, '../../node_modules'),
  path.resolve(import.meta.dirname, '../../lib/api-client-react/src'),
];
const privateFiles = [
  '.env', '.env.*', '*.{crt,pem}', '**/.git/**',
  '**/backend/**', '**/.sada_api/**', '**/.agents/**', '**/attached_assets/**',
  '**/*.{py,pyc,pyo,xlsx,xls,zip,db}', '**/*.sqlite*',
];

function previewFileBoundary(base: string): Plugin {
  const roots = frontendRoots.map(root => realpathSync(root));
  const privatePath = /(?:^|\/)(?:backend|\.sada_api|\.agents|attached_assets)(?:\/|$)|\.(?:py[co]?|xlsx?|zip|db|sqlite[^/]*)(?:$|\/)/i;
  const allowed = (file: string) => roots.some(root => file === root || file.startsWith(`${root}/`));
  return {
    name: 'sada-preview-file-boundary',
    enforce: 'pre',
    configureServer(server) {
      // Runs before Vite's transforms, raw-file serving and SPA fallback.
      server.middlewares.use((req, res, next) => {
        try {
          let url = (req.url ?? '/').split(/[?#]/, 1)[0];
          for (let i = 0; i < 8; i++) {
            const decoded = decodeURIComponent(url);
            if (decoded === url) break;
            url = decoded;
          }
          if (decodeURIComponent(url) !== url || /[\0-\x1f]/.test(url)) throw new Error();
          url = url.replaceAll('\\', '/');
          if (privatePath.test(path.posix.normalize(url))) throw new Error();
          const fsIndex = url.indexOf('/@fs/');
          const relativeUrl = base !== '/' && url.startsWith(base)
            ? url.slice(base.length) : url;
          const file = fsIndex >= 0
            ? path.resolve(url.slice(fsIndex + '/@fs'.length))
            : path.resolve(import.meta.dirname, `.${relativeUrl.startsWith('/') ? relativeUrl : `/${relativeUrl}`}`);
          const target = existsSync(file) ? realpathSync(file) : file;
          if (!allowed(target) || privatePath.test(target)) throw new Error();
          next();
        } catch {
          res.writeHead(403, { 'Content-Type': 'text/plain; charset=utf-8', 'Cache-Control': 'no-store' });
          res.end('Forbidden');
        }
      });
    },
  };
}

export default defineConfig({
  base: basePath,
  plugins: [
    previewFileBoundary(basePath),
    react(),
    tailwindcss(),
    runtimeErrorOverlay(),
    ...(process.env.NODE_ENV !== 'production' &&
    process.env.REPL_ID !== undefined
      ? [
          await import('@replit/vite-plugin-cartographer').then((m) =>
            m.cartographer({
              root: path.resolve(import.meta.dirname, '..'),
            }),
          ),
          await import('@replit/vite-plugin-dev-banner').then((m) =>
            m.devBanner(),
          ),
        ]
      : []),
  ],
  resolve: {
    alias: {
      '@': path.resolve(import.meta.dirname, 'src'),
      '@assets': path.resolve(
        import.meta.dirname,
        '..',
        '..',
        'attached_assets',
      ),
    },
    dedupe: ['react', 'react-dom'],
  },
  root: path.resolve(import.meta.dirname),
  build: {
    outDir: path.resolve(import.meta.dirname, 'dist/public'),
    emptyOutDir: true,
  },
  server: {
    port,
    strictPort: true,
    host: '0.0.0.0',
    allowedHosts: true,
    fs: {
      strict: true,
      allow: frontendRoots,
      deny: privateFiles,
    },
  },
  preview: {
    port,
    host: '0.0.0.0',
    allowedHosts: true,
  },
});
