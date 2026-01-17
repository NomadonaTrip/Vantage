/**
 * Structured logging configuration using pino.
 *
 * Provides JSON logging for both browser and server-side Next.js code.
 */

import pino, { type Logger, type LoggerOptions } from 'pino';

// Log level from environment, defaults to 'info'
const LOG_LEVEL = process.env.NEXT_PUBLIC_LOG_LEVEL || 'info';

// Check if we're in a browser environment
const isBrowser = typeof window !== 'undefined';

// Base configuration shared between environments
const baseConfig: LoggerOptions = {
  level: LOG_LEVEL,
  // Add timestamp to all log entries
  timestamp: pino.stdTimeFunctions.isoTime,
};

// Browser-specific configuration
const browserConfig: LoggerOptions = {
  ...baseConfig,
  browser: {
    // Output logs as objects (not strings) for better debugging
    asObject: true,
    // Map pino levels to console methods
    write: {
      error: (o: object) => console.error(o),
      warn: (o: object) => console.warn(o),
      info: (o: object) => console.info(o),
      debug: (o: object) => console.debug(o),
      trace: (o: object) => console.trace(o),
    },
  },
};

// Server-specific configuration (JSON output)
const serverConfig: LoggerOptions = {
  ...baseConfig,
  // In development, use pino-pretty for readable output
  ...(process.env.NODE_ENV !== 'production' && {
    transport: {
      target: 'pino-pretty',
      options: {
        colorize: true,
        translateTime: 'SYS:standard',
        ignore: 'pid,hostname',
      },
    },
  }),
};

/**
 * Create a logger instance appropriate for the current environment.
 */
function createLogger(): Logger {
  if (isBrowser) {
    return pino(browserConfig);
  }
  return pino(serverConfig);
}

/**
 * The main logger instance for the application.
 *
 * @example
 * ```typescript
 * import { logger } from '@/lib/logger';
 *
 * logger.info({ event: 'user_login', userId: '123' });
 * logger.error({ event: 'api_error', error: err.message, statusCode: 500 });
 * ```
 */
export const logger = createLogger();

/**
 * Create a child logger with bound context.
 *
 * @param bindings - Key-value pairs to include in all log entries
 * @returns A child logger with the bound context
 *
 * @example
 * ```typescript
 * const searchLogger = createChildLogger({ component: 'SearchPage', searchId: 'abc123' });
 * searchLogger.info({ event: 'search_started' }); // Includes component and searchId
 * ```
 */
export function createChildLogger(bindings: Record<string, unknown>): Logger {
  return logger.child(bindings);
}

/**
 * Log level type for type-safe level checks.
 */
export type LogLevel = 'trace' | 'debug' | 'info' | 'warn' | 'error' | 'fatal';

/**
 * Check if the current log level would output for a given level.
 *
 * @param level - The log level to check
 * @returns True if logs at this level would be output
 */
export function isLevelEnabled(level: LogLevel): boolean {
  return logger.isLevelEnabled(level);
}

export default logger;
