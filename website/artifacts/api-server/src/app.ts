import express, { type Express } from "express";
import pinoHttp from "pino-http";
import router from "./routes";
import { logger } from "./lib/logger";
import { createOriginProtection, createRequestProtection, requestErrorHandler } from "./lib/request-protection";
import { createAnonymousSession } from "./lib/anonymous-session";

export function createApp(): Express {
  const app: Express = express();
  app.set("trust proxy", "loopback");

  app.use(
    pinoHttp({
      logger,
      serializers: {
        req(req) {
          return {
            id: req.id,
            method: req.method,
            url: req.url?.split("?")[0],
          };
        },
        res(res) {
          return {
            statusCode: res.statusCode,
          };
        },
      },
    }),
  );
  app.use("/api", createOriginProtection(
    (process.env.SADA_ALLOWED_ORIGINS || "").split(",").map(origin => origin.trim()),
  ));
  app.use("/api/evaluations", ...createRequestProtection());
  app.use("/api/evaluations", createAnonymousSession());
  // Separate bounded policy budget; existing evaluation limits are unchanged.
  app.use("/api/policy", ...createRequestProtection());
  app.use("/api/policy", createAnonymousSession());

  app.use("/api", router);
  app.use(requestErrorHandler);
  return app;
}

export default createApp();
