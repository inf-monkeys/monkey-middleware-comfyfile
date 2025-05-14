import { Router } from "express";

import { cancelAllWorkflows, cancelWorkflow, runWorkflow } from './services/task.js';
import { getAllInstances } from "./services/instance.js";
import _ from "lodash";
import { nanoid } from "nanoid";

const router = Router();

router.post('/run', async (req, res) => {
  try {
    const params = req.body;
    const taskId = nanoid();
    req.on('close', async () => {
      await cancelWorkflow(taskId);
    });
    const result = await runWorkflow(taskId, params);
    res.json(result);
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

router.delete('/task/:taskId', async (req, res) => {
  try {
    const taskId = req.params.taskId;
    await cancelWorkflow(taskId);
    res.json({
      success: true
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error
    });
  }
});

router.delete('/task/all', async (req, res) => {
  try {
    await cancelAllWorkflows();
    res.json({
      success: true
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error
    });
  }
});

export default router;
