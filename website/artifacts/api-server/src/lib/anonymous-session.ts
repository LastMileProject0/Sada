import { createHash, createHmac, randomBytes, timingSafeEqual } from "node:crypto";
import type { RequestHandler } from "express";
import { publicOrigin } from "./public-origin";

export const ANONYMOUS_COOKIE = "__Host-sada-demo";
export const SESSION_SECONDS = 24 * 60 * 60;

/** Signed stateless bearer cookie; never accept an unsigned/chosen session ID.
 * No credential appears in URLs, response JSON, or persisted result payloads. */
export function createAnonymousSession(
  secret: string | undefined = process.env.SESSION_SECRET,
  now: () => number = Date.now,
): RequestHandler {
  if (!secret || Buffer.byteLength(secret) < 32) {
    throw new Error("A stable SESSION_SECRET of at least 32 bytes is required");
  }
  const sign = (payload: string) => createHmac("sha256", secret)
    .update(`sada-anonymous-session:${payload}`).digest();
  const valid = (token: string | undefined): string | undefined => {
    if (!token || token.length > 160) return;
    const match = /^v1\.([A-Za-z0-9_-]{43})\.([0-9]{10,11})\.([A-Za-z0-9_-]{43})$/.exec(token);
    if (!match) return;
    const issued = Number(match[2]);
    const time = Math.floor(now() / 1000);
    if (issued > time + 60 || time - issued >= SESSION_SECONDS) return;
    const payload = token.slice(0, token.lastIndexOf("."));
    const provided = Buffer.from(match[3]!, "base64url");
    const expected = sign(payload);
    if (provided.length !== expected.length || !timingSafeEqual(provided, expected)) return;
    return match[1];
  };
  return (req, res, next) => {
    res.setHeader("Cache-Control", "no-store");
    // Preview's HTTPS proxy can rewrite SameSite=Lax to None for embedding.
    // Therefore mutations must not rely on SameSite alone: browsers supply
    // an unforgeable Origin on POST, and cross-site fetches are never admitted.
    if (req.method === "POST" && (
      req.get("origin") !== publicOrigin(req) ||
      req.get("sec-fetch-site") === "cross-site"
    )) {
      res.status(403).json({ detail: "Cross-site evaluation requests are not allowed." });
      return;
    }
    // Reject ambiguous duplicate cookies rather than choose a fixation candidate.
    const values = (req.headers.cookie || "").split(";").map(part => part.trim())
      .filter(part => part.startsWith(`${ANONYMOUS_COOKIE}=`))
      .map(part => part.slice(ANONYMOUS_COOKIE.length + 1));
    let session = valid(values.length === 1 ? values[0] : undefined);
    if (!session && req.method === "POST") {
      session = randomBytes(32).toString("base64url");
      const payload = `v1.${session}.${Math.floor(now() / 1000)}`;
      const token = `${payload}.${sign(payload).toString("base64url")}`;
      res.cookie(ANONYMOUS_COOKIE, token, {
        secure: true, httpOnly: true, sameSite: "lax", path: "/",
        maxAge: SESSION_SECONDS * 1000,
      });
    }
    if (!session) {
      res.status(404).json({ detail: "Evaluation not found" });
      return;
    }
    res.locals.evaluationOwnerHash = createHash("sha256")
      .update("sada-owner-v1:").update(session).digest("hex");
    next();
  };
}
