# Milestone v2.0 Requirements — Web Mode V3

## Backend (BACK)
- [ ] **BACK-01**: FastAPI app with WebSocket hub broadcasting pipeline state changes
- [ ] **BACK-02**: REST endpoints for scan control (start, stop, status)
- [ ] **BACK-03**: REST endpoint for scope file upload (multipart)
- [ ] **BACK-04**: WebSocket channel for NeuroCore status (loaded model, VRAM, active role)
- [ ] **BACK-05**: WebSocket channel for notification feed (events sent, channel, status)
- [ ] **BACK-06**: REST endpoints for report listing and download
- [ ] **BACK-07**: REST endpoints for config read/write (models.yaml, notifications.yaml)
- [ ] **BACK-08**: WebSocket channel for live scan terminal (agent reasoning, tool calls, model decisions)

## Scan Control (SCAN)
- [ ] **SCAN-01**: User can drag-and-drop a scope file to upload it
- [ ] **SCAN-02**: User can type target URL with real-time validation
- [ ] **SCAN-03**: User can start a scan with a prominent start button
- [ ] **SCAN-04**: User can stop a running scan
- [ ] **SCAN-05**: User can see live progress showing current pipeline stage

## Findings Dashboard (FIND)
- [ ] **FIND-01**: User can see all findings with severity color coding (critical=red, high=orange, medium=yellow, low=blue)
- [ ] **FIND-02**: User can expand a finding to see full evidence section
- [ ] **FIND-03**: User can one-click copy a finding as H1 report format
- [ ] **FIND-04**: User can filter findings by severity

## NeuroCore Monitor (NCORE)
- [ ] **NCORE-01**: User can see currently loaded model with animated pulse indicator
- [ ] **NCORE-02**: User can see real-time VRAM usage bar
- [ ] **NCORE-03**: User can see which role is currently active
- [ ] **NCORE-04**: User can load/unload models per button

## Notifications Hub (NOTIF)
- [ ] **NOTIF-01**: User can see live feed of notifications sent (event, channel, timestamp)
- [ ] **NOTIF-02**: User can test a notification channel with one click
- [ ] **NOTIF-03**: User can toggle channels on/off without editing YAML

## Live Scan Terminal (TERM)
- [ ] **TERM-01**: User can see real-time agent reasoning as formatted log
- [ ] **TERM-02**: User can see tool calls being made with arguments and results
- [ ] **TERM-03**: User can see model decisions (which model loaded, for what role)

## Reports (RPT)
- [ ] **RPT-01**: User can browse generated reports
- [ ] **RPT-02**: User can download reports

## Settings (SET)
- [ ] **SET-01**: User can view and edit models.yaml in-browser
- [ ] **SET-02**: User can view and edit notifications.yaml in-browser

## Shell & Navigation (NAV)
- [ ] **NAV-01**: All panels accessible from collapsible sidebar navigation
- [ ] **NAV-02**: Sidebar collapses for more screen space
- [ ] **NAV-03**: Mobile responsive — all panels usable on phone screen
- [ ] **NAV-04**: Dark cyberpunk theme as default
- [ ] **NAV-05**: Clean light theme toggle for professional contexts
- [ ] **NAV-06**: "Backend offline" state shown when API unreachable (no fake data)

## Traceability
| REQ-ID | Phase |
|--------|-------|
| BACK-01..08 | Phase 1 |
| NAV-01..06 | Phase 2 |
| SCAN-01..05, FIND-01..04, NCORE-01..04 | Phase 3 |
| NOTIF-01..03, TERM-01..03, RPT-01..02, SET-01..02 | Phase 4 |

## Future Requirements
- Operator Plane (manual tool execution terminal) — Phase 5+
- Multi-user auth and access control
- Report comparison and diff view

## Out of Scope
- Changing NeuroCore inference internals
- Adding new security scanning tools
- Modifying OpenClaw gateway protocol
