import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'GhostFrame — Silent Mutations Are Not Silent',
  description:
    'Multi-frame variant impact scanner. Re-examines silent cancer mutations across all 6 reading frames to reveal hidden non-synonymous effects and neoantigen candidates.',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="h-full overflow-x-hidden">{children}</body>
    </html>
  );
}
