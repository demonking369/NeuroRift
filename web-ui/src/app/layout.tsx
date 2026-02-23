import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import '@/styles/globals.css';
import { CommandCenterFrame } from '@/components/webmode/CommandCenterFrame';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
    title: 'NeuroRift Web Mode - Command Interface',
    description: 'AI-native command interface for OpenClaw + NeuroRift.',
};

export default function RootLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang="en" suppressHydrationWarning>
            <body className={inter.className}>
                <CommandCenterFrame>
                    <main className="h-full">
                        {children}
                    </main>
                </CommandCenterFrame>
            </body>
        </html>
    );
}
