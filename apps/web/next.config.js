/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  transpilePackages: ['@vantage/shared'],
  experimental: {
    instrumentationHook: true,
  },
};

// Wrap with Sentry configuration if available
const withSentryConfig = (() => {
  try {
    const { withSentryConfig: sentryConfig } = require('@sentry/nextjs');
    return sentryConfig;
  } catch {
    return (config) => config;
  }
})();

module.exports = withSentryConfig(nextConfig, {
  // Sentry webpack plugin options
  silent: true,
  org: process.env.SENTRY_ORG,
  project: process.env.SENTRY_PROJECT,
});
