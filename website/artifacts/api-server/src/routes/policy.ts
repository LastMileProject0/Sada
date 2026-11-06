import { Router, type IRouter } from "express";
import { pythonUrl } from "../lib/python-service";

const router: IRouter = Router();
router.post("/policy/explain", async (req, res): Promise<void> => {
  res.setHeader("Cache-Control", "no-store");
  try {
    const upstream = await fetch(pythonUrl("policy/explain"), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-SADA-Owner": res.locals.evaluationOwnerHash,
      },
      body: JSON.stringify(req.body),
      // Original explainer permits one citation retry; hosted calls have 30s timeouts.
      signal: AbortSignal.timeout(185_000),
    });
    if (!upstream.headers.get("content-type")?.includes("application/json")) {
      throw new Error("Unexpected policy response");
    }
    const body: unknown = await upstream.json();
    const retry = upstream.headers.get("retry-after");
    if (retry) res.setHeader("Retry-After", retry);
    res.status(upstream.status).json(body);
  } catch {
    req.log.warn("Policy service unavailable");
    res.status(503).json({ detail: "Policy service unavailable" });
  }
});
export default router;
