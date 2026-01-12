import { app } from '../config';

export const logger = {
  error: (message: string, error?: unknown, context?: Record<string, unknown>) => {
    if (app.debugMode) {
      console.error(`[ERROR] ${message}`, error, context);
    }
  },

  warn: (message: string, context?: Record<string, unknown>) => {
    if (app.debugMode) {
      console.warn(`[WARN] ${message}`, context);
    }
  },

  info: (message: string, context?: Record<string, unknown>) => {
    if (app.logLevel === 'debug') {
      console.info(`[INFO] ${message}`, context);
    }
  },
};
