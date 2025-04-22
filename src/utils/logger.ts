import { pino } from 'pino'

const baseLogger = pino({
  level: process.env.LOG_LEVEL || 'info',
  transport: {
    target: 'pino-pretty',
    options: {
      colorize: true,
      translateTime: 'SYS:standard',
      ignore: 'pid,hostname,tag',
      messageFormat: '[{tag}] {msg}'
    }
  }
})

export const createLogger = (tag: string) => baseLogger.child({
  tag
})