import type { Request } from "express";

const configured = process.env.SADA_PUBLIC_ORIGIN;
if (configured) {
  const parsed = new URL(configured);
  if (parsed.protocol !== "https:" || parsed.origin !== configured) {
    throw new Error("SADA_PUBLIC_ORIGIN must be an exact HTTPS origin");
  }
}
if (process.env.NODE_ENV === "production" && !configured) {
  throw new Error("Production requires an explicit SADA_PUBLIC_ORIGIN");
}

/** Production uses a server-owned canonical origin, not spoofable proxy headers. */
export function publicOrigin(req: Request): string {
  return configured || `${req.protocol}://${req.get("host")}`;
}
