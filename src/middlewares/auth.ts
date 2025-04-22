
import { NextFunction, Request, Response } from 'express';
import { createLogger } from '../utils/logger.js';

const logger = createLogger('auth');

const authMiddleware = (req: Request, res: Response, next: NextFunction) => {
  let token: string | undefined;

  if (req.query.token && typeof req.query.token === 'string') {
    token = req.query.token;
    logger.debug('从查询参数中获取到 token');
  }

  else if (req.headers.authorization) {
    const authHeader = req.headers.authorization;
    if (authHeader.startsWith('Bearer ')) {
      token = authHeader.substring(7);
      logger.debug('从 Authorization 头中获取到 Bearer token');
    }
  }

  if (!token) {
    res.status(401).json({ success: false, message: '未提供认证 token' });
    return;
  }

  next();
};

export default authMiddleware;
