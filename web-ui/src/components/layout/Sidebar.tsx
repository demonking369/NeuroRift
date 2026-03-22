'use client';

import React, { useState } from 'react';
import { useTheme } from '@/contexts/ThemeContext';
import { useWS } from '@/contexts/WebSocketContext';

interface NavItem {
    id: string;
    label: string;
    icon: string;
}

const NAV_ITEMS: NavItem[] = [
    { id: 'scan',          label: 'Scan Control',       icon: '🎯' },
    { id: 'findings',      label: 'Findings',           icon: '🔍' },
    { id: 'neurocore',     label: 'NeuroCore',          icon: '🧠' },
    { id: 'notifications', label: 'Notifications',      icon: '📢' },
    { id: 'terminal',      label: 'Live Terminal',      icon: '💻' },
    { id: 'reports',       label: 'Reports',            icon: '📝' },
    { id: 'settings',      label: 'Settings',           icon: '⚙️' },
];

interface SidebarProps {
    activePanel: string;
    onNavigate: (panel: string) => void;
    collapsed: boolean;
    onToggleCollapse: () => void;
    mobileOpen: boolean;
    onCloseMobile: () => void;
}

export function Sidebar({
    activePanel,
    onNavigate,
    collapsed,
    onToggleCollapse,
    mobileOpen,
    onCloseMobile,
}: SidebarProps) {
    const { theme, toggleTheme } = useTheme();
    const { isConnected } = useWS();

    const handleNav = (id: string) => {
        onNavigate(id);
        onCloseMobile();
    };

    return (
        <>
            {/* Mobile overlay */}
            {mobileOpen && (
                <div
                    className="fixed inset-0 bg-black/50 z-40 md:hidden"
                    onClick={onCloseMobile}
                />
            )}

            <aside className={`sidebar ${collapsed ? 'collapsed' : ''} ${mobileOpen ? 'mobile-open' : ''}`}>
                {/* Logo */}
                <div className="sidebar-logo">
                    <div className="logo-icon">🧠</div>
                    {!collapsed && (
                        <>
                            <span className="logo-text">NeuroRift</span>
                            <span className="logo-version">v3</span>
                        </>
                    )}
                </div>

                {/* Connection status */}
                {!collapsed && (
                    <div style={{ padding: '8px 16px', display: 'flex', alignItems: 'center', gap: 8 }}>
                        <span className={`pulse ${isConnected ? '' : 'offline'}`} />
                        <span style={{ fontSize: 12, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                            {isConnected ? 'CONNECTED' : 'OFFLINE'}
                        </span>
                    </div>
                )}

                {/* Navigation */}
                <nav className="sidebar-nav">
                    {NAV_ITEMS.map((item) => (
                        <button
                            key={item.id}
                            className={`nav-item ${activePanel === item.id ? 'active' : ''}`}
                            onClick={() => handleNav(item.id)}
                            title={collapsed ? item.label : undefined}
                        >
                            <span className="nav-icon">{item.icon}</span>
                            {!collapsed && <span>{item.label}</span>}
                        </button>
                    ))}
                </nav>

                {/* Footer */}
                <div className="sidebar-footer">
                    {/* Theme toggle */}
                    <button
                        className="nav-item"
                        onClick={toggleTheme}
                        title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`}
                    >
                        <span className="nav-icon">{theme === 'dark' ? '☀️' : '🌙'}</span>
                        {!collapsed && <span>{theme === 'dark' ? 'Light Mode' : 'Dark Mode'}</span>}
                    </button>

                    {/* Collapse toggle (desktop only) */}
                    <button
                        className="nav-item"
                        onClick={onToggleCollapse}
                        style={{ display: 'none' }}
                        id="collapse-btn"
                    >
                        <span className="nav-icon">{collapsed ? '→' : '←'}</span>
                        {!collapsed && <span>Collapse</span>}
                    </button>
                    <style>{`@media (min-width: 769px) { #collapse-btn { display: flex !important; } }`}</style>
                </div>
            </aside>
        </>
    );
}
