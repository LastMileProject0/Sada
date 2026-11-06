import { Router, type IRouter, type Request, type Response } from "express";
import { pythonUrl } from "../lib/python-service";

const router: IRouter = Router();

/** Fixed, private upstream and allowlisted paths only. Python owns validation
 * and execution; this layer never interprets or changes engine results. */
async function forward(req: Request, res: Response, path: string): Promise<void> {
  try {
    const upstream = await fetch(pythonUrl(path), {
      method: req.method === "HEAD" ? "GET" : req.method,
      // Discard all caller-supplied internal headers. Only verified middleware
      // ownership crosses the private Node -> Python boundary.
      headers: {
        "Content-Type": "application/json",
        ...(path.startsWith("evaluations")
          ? { "X-SADA-Owner": String(res.locals.evaluationOwnerHash) } : {}),
      },
      ...(req.method === "POST" ? { body: JSON.stringify(req.body) } : {}),
      signal: AbortSignal.timeout(120_000),
    });
    if (!upstream.headers.get("content-type")?.includes("application/json")) {
      throw new Error("Unexpected upstream content type");
    }
    const body: unknown = await upstream.json();
    const retryAfter = upstream.headers.get("retry-after");
    if (retryAfter) res.setHeader("Retry-After", retryAfter);
    res.setHeader("Cache-Control", "no-store");
    res.status(upstream.status).json(body);
  } catch {
    req.log.warn("Python evaluation service unavailable");
    res.status(503).json({ detail: "Evaluation service unavailable. Please retry." });
  }
}

router.get("/health", async (req, res): Promise<void> => {
  await forward(req, res, "health");
});
router.post("/evaluations", async (req, res): Promise<void> => {
  await forward(req, res, "evaluations");
});
router.get("/evaluations/:id", async (req, res): Promise<void> => {
  const id = String(req.params.id);
  if (!/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(id)) {
    res.status(404).json({ detail: "Evaluation not found" });
    return;
  }
  await forward(req, res, `evaluations/${id}`);
});

export default router;
