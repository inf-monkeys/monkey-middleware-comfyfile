import { Router } from "express";

import { runWorkflow } from './services/task.js';
import { getAllInstances } from "./services/instance.js";
import _ from "lodash";
import { createLogger } from './utils/logger.js';

const router = Router();

// 创建 logger 实例
const logger = createLogger('routes');

router.post('/run', async (req, res) => {
  try {
    const params = req.body;
    const result = await runWorkflow(params);
    res.json({
      success: true,
      data: result
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error
    });
  }
});

router.get('/instances', (_req, res) => {
  res.json({
    success: true,
    data: getAllInstances().map(instance => _.pick(instance, ['url', 'healthz', 'lastCheck', 'busy']))
  });
});

export default router;
