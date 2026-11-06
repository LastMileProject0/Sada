import { json, type ErrorRequestHandler, type RequestHandler } from "express";
import { publicOrigin } from "./public-origin";

export const REQUEST_LIMITS = {
  windowMs: 60_000, submissions: 6, reads: 120, clients: 1_000, admitted: 2,
} as const;

/** Bounded, process-local counters. Never trust arbitrary forwarded client IDs.
 * Express trusts only the loopback gateway; other peers use their socket IP. */
export function createRequestProtection(now = Date.now): RequestHandler[] {
  const clients = new Map<string, { start: number; submissions: number; reads: number }>();
  let admitted = 0;
  const admission: RequestHandler = (req, res, next) => {
    res.setHeader("Cache-Control", "no-store");
    if (req.method !== "POST" && req.method !== "GET" && req.method !== "HEAD") {
      next();
      return;
    }
    const time = now();
    for (const [key, value] of clients) {
      if (time - value.start >= REQUEST_LIMITS.windowMs) clients.delete(key);
    }
    const key = req.ip || req.socket.remoteAddress || "unknown";
    let client = clients.get(key);
    if (!client) {
      if (clients.size >= REQUEST_LIMITS.clients) {
        res.setHeader("Retry-After", "60");
        res.status(503).json({ detail: "Request capacity reached. Please retry later." });
        return;
      }
      client = { start: time, submissions: 0, reads: 0 };
      clients.set(key, client);
    }
    const counter = req.method === "POST" ? "submissions" : "reads";
    if (client[counter] >= REQUEST_LIMITS[counter]) {
      res.setHeader("Retry-After", String(Math.max(1, Math.ceil(
        (client.start + REQUEST_LIMITS.windowMs - time) / 1_000,
      ))));
      res.status(429).json({ detail: "Evaluation request limit reached. Please retry later." });
      return;
    }
    client[counter]++;
    if (req.method === "POST") {
      if (req.headers["content-encoding"] &&
          req.headers["content-encoding"].toLowerCase() !== "identity") {
        res.status(415).json({ detail: "Compressed request bodies are not supported." });
        return;
      }
      if (!req.is("application/json")) {
        res.status(415).json({ detail: "Evaluation requests require application/json." });
        return;
      }
      if (admitted >= REQUEST_LIMITS.admitted) {
        res.setHeader("Retry-After", "2");
        res.status(503).json({ detail: "Evaluation capacity reached. Please retry later." });
        return;
      }
      admitted++;
      let released = false;
      const release = () => {
        if (!released) { released = true; admitted--; }
      };
      res.once("finish", release);
      res.once("close", release);
    }
    next();
  };
  return [admission, json({ limit: "4kb", inflate: false, strict: true })];
}

/** No browser cross-origin API use is needed by SADA. Explicit opt-in only.
 * Same-origin requests do not need Access-Control-Allow-Origin headers. */
export function createOriginProtection(origins: string[] = []): RequestHandler {
  const trusted = new Set(origins.filter(Boolean).map(origin => {
    const parsed = new URL(origin);
    if (!["http:", "https:"].includes(parsed.protocol) || parsed.origin !== origin) {
      throw new Error("Trusted origins must be exact HTTP(S) origins");
    }
    return parsed.origin;
  }));
  return (req, res, next) => {
    const origin = req.get("origin");
    if (!origin) { next(); return; }
    const sameOrigin = publicOrigin(req);
    if (origin !== sameOrigin && !trusted.has(origin)) {
      res.setHeader("Cache-Control", "no-store");
      res.status(403).json({ detail: "Cross-origin API access is not allowed." });
      return;
    }
    res.vary("Origin");
    if (trusted.has(origin)) {
      res.setHeader("Access-Control-Allow-Origin", origin);
      res.setHeader("Access-Control-Allow-Methods", "GET, HEAD, POST");
      res.setHeader("Access-Control-Allow-Headers", "Content-Type");
    }
    if (req.method === "OPTIONS") { res.sendStatus(204); return; }
    next();
  };
}

export const requestErrorHandler: ErrorRequestHandler = (error, req, res, _next) => {
  const status = [400, 413, 415].includes(error.status) ? error.status : 500;
  if (status === 500) req.log?.error("API request failed");
  res.setHeader("Cache-Control", "no-store");
  res.status(status).json({ detail: status === 413 ? "Request body exceeds the 4 KiB limit."
    : status === 415 ? "Unsupported request encoding or character set."
    : status === 400 ? "Invalid JSON request." : "Request failed." });
};
