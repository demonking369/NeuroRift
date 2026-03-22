# Milestone v2.0 Roadmap — Web Mode V3

## Phase 1: FastAPI Backend + WebSocket Hub
**Goal:** Build the real-time data layer that powers every dashboard panel.

**Requirements:** BACK-01, BACK-02, BACK-03, BACK-04, BACK-05, BACK-06, BACK-07, BACK-08

**Success Criteria:**
1. FastAPI server starts and accepts WebSocket connections
2. Scan start/stop/status REST endpoints return correct pipeline state
3. WebSocket broadcasts NeuroCore status, notification feed, and scan terminal events
4. Scope file upload endpoint accepts and validates files
5. Config endpoints read/write models.yaml and notifications.yaml

---

## Phase 2: Frontend Shell — Navigation + Themes + Mobile
**Goal:** Build the app shell with routing, dual themes, and responsive layout.

**Requirements:** NAV-01, NAV-02, NAV-03, NAV-04, NAV-05, NAV-06

**Success Criteria:**
1. Sidebar navigation renders all 8 panel links, collapses on toggle
2. Cyberpunk dark theme applied as default with neon green/cyan accents
3. Light theme toggle works and persists across sessions
4. Layout is fully usable on mobile phone screen (375px width)
5. "Backend offline" banner shown when WebSocket fails to connect

---

## Phase 3: Core Panels — Scan Control + Findings + NeuroCore
**Goal:** Build the three most critical panels with live WebSocket data.

**Requirements:** SCAN-01..05, FIND-01..04, NCORE-01..04

**Success Criteria:**
1. Scope file drag-drop uploads to backend and shows confirmation
2. Start/Stop buttons trigger scan and reflect live pipeline stage
3. Findings list renders with correct severity colors and expandable evidence
4. H1 report copy button copies formatted finding to clipboard
5. NeuroCore monitor shows live model name with animated pulse, real-time VRAM bar, active role

---

## Phase 4: Auxiliary Panels — Notifications + Terminal + Reports + Settings
**Goal:** Complete all remaining panels.

**Requirements:** NOTIF-01..03, TERM-01..03, RPT-01..02, SET-01..02

**Success Criteria:**
1. Notification feed shows live events with channel and timestamp
2. Test button sends a test notification and shows result
3. Channel toggles update config without YAML editing
4. Live scan terminal shows formatted agent reasoning and tool calls in real time
5. Reports panel lists and downloads generated reports
6. Settings panel loads and saves YAML configs

---

## Phase 5: Integration Test + Production Push
**Goal:** End-to-end verification and deployment.

**Requirements:** All

**Success Criteria:**
1. All panels render correctly on desktop and mobile
2. WebSocket connections remain stable across panel switches
3. Theme toggle works without page reload
4. Backend offline state shown correctly when API stopped
5. All changes committed and pushed to main
