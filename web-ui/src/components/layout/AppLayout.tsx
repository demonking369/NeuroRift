'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { Sidebar } from './Sidebar';
import { useWS } from '@/contexts/WebSocketContext';

// Panel imports
import { ScanControl } from '@/components/panels/ScanControl';
import { FindingsDashboard } from '@/components/panels/FindingsDashboard';
import { NeuroCoreMonitor } from '@/components/panels/NeuroCoreMonitor';
import { NotificationsHub } from '@/components/panels/NotificationsHub';
import { LiveTerminal } from '@/components/panels/LiveTerminal';
import { ReportsPanel } from '@/components/panels/ReportsPanel';
import { SettingsPanel } from '@/components/panels/SettingsPanel';

const PANELS: Record<string, React.ComponentType> = {
    scan: ScanControl,
    findings: FindingsDashboard,
    neurocore: NeuroCoreMonitor,
    notifications: NotificationsHub,
    terminal: LiveTerminal,
    reports: ReportsPanel,
    settings: SettingsPanel,
};

const PANEL_TITLES: Record<string, string> = {
    scan: 'Scan Control',
    findings: 'Findings Dashboard',
    neurocore: 'NeuroCore Monitor',
    notifications: 'Notifications Hub',
    terminal: 'Live Scan Terminal',
    reports: 'Reports',
    settings: 'Settings',
};

export function AppLayout() {
    const [activePanel, setActivePanel] = useState('scan');
    const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
    const [mobileOpen, setMobileOpen] = useState(false);
    const { isConnected } = useWS();

    const ActiveComponent = PANELS[activePanel] || ScanControl;

    return (
        <div className="app-layout">
            <Sidebar
                activePanel={activePanel}
                onNavigate={setActivePanel}
                collapsed={sidebarCollapsed}
                onToggleCollapse={() => setSidebarCollapsed(c => !c)}
                mobileOpen={mobileOpen}
                onCloseMobile={() => setMobileOpen(false)}
            />

            <main className={`main-content ${sidebarCollapsed ? 'sidebar-collapsed' : ''}`}>
                {/* Mobile header */}
                <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    marginBottom: 20,
                }}>
                    <button
                        className="mobile-menu-btn btn btn-ghost btn-sm"
                        onClick={() => setMobileOpen(true)}
                    >
                        ☰
                    </button>
                    <h1 style={{
                        fontSize: 20,
                        fontWeight: 700,
                        letterSpacing: '-0.02em',
                    }}>
                        {PANEL_TITLES[activePanel]}
                    </h1>
                    <div style={{ width: 40 }} /> {/* spacer */}
                </div>

                {/* Backend offline banner */}
                {!isConnected && (
                    <div className="offline-banner">
                        <span className="pulse offline" />
                        <span>Backend offline — dashboard will reconnect automatically</span>
                    </div>
                )}

                {/* Active panel */}
                <ActiveComponent />
            </main>
        </div>
    );
}
