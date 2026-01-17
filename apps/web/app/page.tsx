'use client';

import { logger } from '@/lib/logger';

export default function Home() {
  // Log page view
  logger.info({ event: 'page_view', page: 'home' });

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <h1 className="text-4xl font-bold">Vantage</h1>
      <p className="mt-4 text-lg text-gray-600">
        Intelligent Lead Generation Platform
      </p>
    </main>
  );
}
