import { Router, type IRouter } from "express";
import healthRouter from "./health";
import evaluationsRouter from "./evaluations";
import policyRouter from "./policy";

const router: IRouter = Router();

router.use(healthRouter);
router.use(evaluationsRouter);
router.use(policyRouter);

export default router;
