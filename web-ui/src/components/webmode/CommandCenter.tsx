'use client';

import { CommandCenterSurface } from '@/components/webmode/CommandCenterSurface';
import { WebModeProvider } from '@/components/webmode/WebModeProvider';

export function CommandCenter() {
    return (
        <WebModeProvider>
            <CommandCenterSurface />
        </WebModeProvider>
    );
}
