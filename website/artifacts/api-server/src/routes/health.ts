import { Router, type IRouter } from "express";
import { pythonReady } from "../lib/python-service";

const router: IRouter = Router();

router.get("/healthz", async (_req, res): Promise<void> => {
  const ready = await pythonReady();
  res.setHeader("Cache-Control", "no-store");
  res.status(ready ? 200 : 503).json({ status: ready ? "ok" : "unavailable" });
});

export default router;
