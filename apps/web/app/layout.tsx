import type { Metadata } from 'next';
import '@/styles/globals.css';
import { AuthProvider } from '@/components/providers/auth-provider';

export const metadata: Metadata = {
  title: 'Vantage - Intelligent Lead Generation',
  description: 'AI-powered lead generation platform for agencies',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
