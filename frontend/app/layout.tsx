import type { Metadata } from 'next';
import { Oxanium, DM_Sans, JetBrains_Mono } from 'next/font/google';
import './globals.css';

const oxanium = Oxanium({
  subsets: ['latin'],
  weight: ['400', '600', '700', '800'],
  variable: '--font-display',
  display: 'swap',
});

const dmSans = DM_Sans({
  subsets: ['latin'],
  weight: ['300', '400', '500'],
  style: ['normal', 'italic'],
  variable: '--font-body',
  display: 'swap',
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  weight: ['400', '500'],
  variable: '--font-data',
  display: 'swap',
});

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
    <html
      lang="en"
      className={`h-full antialiased ${oxanium.variable} ${dmSans.variable} ${jetbrainsMono.variable}`}
    >
      <body className="h-full overflow-x-hidden">{children}</body>
    </html>
  );
}
