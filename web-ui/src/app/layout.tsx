import type { Metadata } from 'next';
import './globals.css';
import { ThemeProvider } from '@/contexts/ThemeContext';
import { WebSocketProvider } from '@/contexts/WebSocketContext';

export const metadata: Metadata = {
    title: 'NeuroRift — Intelligence Dashboard',
    description: 'Terminal-Based Multi-Agent Intelligence System',
};

export default function RootLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang="en" data-theme="dark">
            <body>
                <ThemeProvider>
                    <WebSocketProvider>
                        {children}
                    </WebSocketProvider>
                </ThemeProvider>
            </body>
        </html>
    );
}
