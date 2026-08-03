# Fitness-Coach-App Optimization Audit

**Date:** 2026-08-03 | **Scope:** Full project at `/vol1/1000/projects/fitness-coach-app`

---

## 1. Project Slimming — Dead Code, Unused Files, Bloat

### 🔴 P0 — Unused Image Files (7 files, ~3.5KB)
These PNG/SVG icons exist in `images/` but are **never referenced** in HTML, JS, or CSS:
- `images/icon-ai.png` + `images/icon-ai.svg`
- `images/icon-calendar.png` + `images/icon-calendar.svg`
- `images/icon-courses.png` + `images/icon-courses.svg`
- `images/icon-stats.png` + `images/icon-stats.svg`
- `images/icon-studio.png` + `images/icon-studio.svg`
- `images/icon-512.png` (no PWA manifest references it)
- `images/icon.svg` (not referenced)

Only `icon-192.png` is used (index.html:8,23,55; js/modal.js:50).

### 🔴 P0 — 14 Unused SVG Icon Exports in `js/utils.js`
Lines 88–107 export icon constants that are **never imported** by any other file:
- `ICON_CHEVRON` (line 94)
- `ICON_DROPDOWN` (line 95)
- `ICON_PLUS` (line 96)
- `ICON_CALENDAR` (line 97)
- `ICON_HOME` (line 98)
- `ICON_BAR` (line 99)
- `ICON_MSG` (line 100)
- `ICON_SEARCH` (line 101)
- `ICON_MIC` (line 102)
- `ICON_ACTIVITY` (line 103)
- `ICON_ERR_CIRCLE` (line 104)
- `ICON_REFRESH` (line 105)
- `ICON_DOLLAR` (line 106)
- `ICON_INFO` (line 107)

These are ~20 lines of dead code. Only `ICON_WARN`, `ICON_CHECK`, `ICON_X`, `ICON_TRASH`, `ICON_LIST`, `ICON_BAN`, `ICON_SETTINGS` are actually used.

### 🟡 P1 — Unused Export: `$id` in `js/utils.js`
- `js/utils.js:51` — `export function $id(id)` is exported but **never imported** by any file. (course.js uses it via direct import, but the import line shows it's imported from utils.js — wait, checking again: course.js does NOT import `$id` but uses it 60+ times. It must be using `document.getElementById` directly instead.)

Actually: `course.js` imports `$id` from utils.js at line 1. But `main.js` does NOT import `$id`. The function is used only by `course.js` and `course-calc.js`. Not truly dead, but worth noting the inconsistency — other files use `document.getElementById` directly (147 calls across the codebase).

### 🟡 P1 — Unused Sync Service Exports
- `js/sync-service.js:195` — `openDB`, `pushQueue`, `pullChanges` are exported but **never imported** by any other file. Only `queueOperation` and `fullSync` are used (imported by `data-service.js` and `main.js`).

### 🟡 P1 — `jsonwebtoken` Dependency (Unused in Server)
- `server/package.json:32` — `"jsonwebtoken": "^9.0.3"` is listed as a dependency but **never imported** in any server source file. The project uses `@fastify/jwt` instead (server/src/plugins/auth.ts). This is a dead dependency.

### 🟡 P1 — `uuid` Package Replaceable by Node.js Built-in
- `server/package.json` — `"uuid": "^14.0.1"` is used only in `server/src/agent/write-tools.ts:5` for `v4()`. Node.js 24 (current runtime) has `crypto.randomUUID()` built-in. The `uuid` package + `@types/uuid` can be removed.

### 🟡 P1 — `dotenv` Package Replaceable by Node.js Built-in
- `server/package.json` — `"dotenv": "^17.4.2"` is used only in `server/src/index.ts:1-2`. Node.js 24 supports `--env-file` flag natively. Could eliminate this dependency.

### 🟡 P1 — `react` + `react-dom` in server/node_modules (7.1MB phantom dependency)
- Pulled in by `prisma → @prisma/studio-core` (Prisma Studio UI). Not used by the app itself. Only bloats `node_modules` in dev. Not removable without Prisma changes, but worth noting: **536MB** total server node_modules.

### 🟡 P1 — `embedded-postgres` in Production Dependencies (60MB)
- `server/package.json:43` — `"embedded-postgres": "^18.4.0-beta.17"` is a **dev-only** tool (used in `server/scripts/start.js` for local dev). It should be in `devDependencies`, not `dependencies`. Currently adds 60MB to production installs.

### 🟢 P2 — `scripts/start-backend.bat` (Windows Script)
- `scripts/start-backend.bat` — 788-line Windows batch script. The project runs on Linux (NAS). This file is dead weight for the deployment target.

### 🟢 P2 — Oversized Files That Should Be Split

| File | Lines | Recommendation |
|------|-------|----------------|
| `js/ai.js` | 1052 | Split into `ai-chat.js` (streaming/rendering ~600 lines) + `ai-settings.js` + `ai-api.js` |
| `server/src/agent/write-tools.ts` | 954 | Split tool definitions from tool execution logic |
| `server/src/routes/admin.ts` | 908 | Split DNS/healthcheck logic from admin panel routes |
| `server/src/routes/ai.ts` | 729 | Split SSE streaming from tool orchestration |
| `css/pages/ai.css` | 815 | Split chat UI from settings UI |
| `css/pages/formula-editor.css` | 765 | Split block editor from template list |
| `js/main.js` | 656 | Extract initialization into separate modules |
| `js/course.js` | 655 | Extract recurring course logic (~200 lines) |
| `js/fe-compute.js` | 650 | Extract preview computation from UI rendering |
| `js/utils.js` | 648 | Split icon definitions (~30 lines) from DOM helpers from date utils |
| `js/data-service.js` | 635 | Extract IndexedDB operations from API fetch logic |

### 🟢 P2 — node_modules Size Summary
| Location | Size | Notes |
|----------|------|-------|
| `server/node_modules` | **536MB** | Prisma (170MB), @embedded-postgres (60MB), @rolldown (37MB), effect (33MB), @electric-sql (26MB) |
| `node_modules` (root) | **140MB** | Dev-only: eslint, vitest, vite, jsdom |

The `@rolldown`, `effect`, `@electric-sql` packages in server are transitive deps of Prisma — not directly controllable.

---

## 2. UI Style Consistency — Hardcoded Values Outside CSS Variables

### 🔴 P0 — Hardcoded Colors in CSS (Fallback Values Using Non-Existent Variables)

These use `var(--xxx, #fallback)` where the variable **does not exist** in `variables.css`:
- `css/pages/formula-editor.css:121` — `var(--warning-dark, #92400e)` — `--warning-dark` is **not defined** in variables.css
- `css/pages/formula-editor.css:122` — `var(--success-dark, #065f46)` — `--success-dark` is **not defined** in variables.css
- `css/pages/formula-editor.css:379` — `var(--warning-dark, #b45309)` — same missing var, **different fallback value** than line 121!
- `css/pages/formula-editor.css:580` — `var(--error, #e53e3e)` — `--error` is **not defined** in variables.css (should be `--danger`)

### 🟡 P1 — Hardcoded `rgba()` Values (15 instances)
These should use CSS variables for dark-mode compatibility:

| File:Line | Value | Should Be |
|-----------|-------|-----------|
| `css/components/guide.css:26` | `rgba(0,0,0,0.65)` | `var(--overlay-bg)` or new `--guide-overlay` |
| `css/components/guide.css:32` | `rgba(0,0,0,0.65)` | same |
| `css/components/guide.css:54` | `rgba(0,0,0,0.3)` | `var(--shadow-lg)` or new var |
| `css/components/modal.css:84` | `rgba(0,0,0,0.2)` | new `--modal-shadow` var |
| `css/components/navigation.css:11` | `rgba(91,123,158,0.3)` | `var(--primary)` with alpha |
| `css/components/navigation.css:15` | `rgba(255,255,255,0.2)` | new var |
| `css/components/navigation.css:50` | `rgba(194, 125, 125, 0.3)` | `var(--danger)` with alpha |
| `css/components/navigation.css:82` | `rgba(0,0,0,0.15)` | new var |
| `css/components/validation.css:24` | `rgba(194, 125, 125, 0.15)` | `var(--danger)` with alpha |
| `css/pages/ai.css:554` | `rgba(0,0,0,0.08)` | `var(--shadow)` |
| `css/pages/ai.css:797` | `rgba(107, 144, 128, 0.5)` | `var(--success)` with alpha |
| `css/utilities/responsive.css:479` | `rgba(0,0,0,0.4)` | `var(--overlay-bg)` |
| `css/utilities/responsive.css:499` | `rgba(0,0,0,0.3)` | new var |
| `css/utilities/responsive.css:511` | `rgba(0,0,0,0.12)` | new var |

### 🟡 P1 — Hardcoded `box-shadow` Values (12 instances outside variables)
All of these bypass the `--shadow` / `--shadow-lg` variables:
- `css/components/guide.css:32,54`
- `css/components/modal.css:84`
- `css/components/navigation.css:11,50,82`
- `css/pages/ai.css:554,797`
- `css/utilities/responsive.css:511`

### 🟡 P1 — Hardcoded Spacing Values (28 instances)
Files using raw `px` values instead of `--space-*` variables:

| File | Lines with hardcoded padding/margin |
|------|-------------------------------------|
| `css/components/inputs.css` | 309, 331, 436 |
| `css/components/navigation.css` | 5, 6, 14 |
| `css/pages/ai.css` | 211, 216, 229, 535, 597, 665 |
| `css/pages/calendar.css` | 89 |
| `css/pages/stats.css` | 69 |
| `css/pages/studios.css` | 12, 100 |
| `css/pages/formula-editor.css` | 106, 133, 164, 218, 251, 381, 384, 423 |
| `css/utilities/responsive.css` | 123, 557 |
| `css/utilities/animations.css` | 142 |

### 🟡 P1 — Hardcoded `font-size` Values (6 instances)
- `css/components/navigation.css:9` — `font-size: 12px` → should use `var(--text-xs)`
- `css/components/navigation.css:16` — `font-size: 13px` → should use `var(--text-sm)`
- `css/components/navigation.css:23` — `font-size: 16px` → should use `var(--text-lg)`
- `css/pages/ai.css:482` — `font-size: 16px` → `var(--text-lg)`
- `css/pages/ai.css:613` — `font-size: 14px` → `var(--text-base)`
- `css/utilities/animations.css:114,118` — `font-size: 12px` → `var(--text-xs)`

### 🟡 P1 — Hardcoded `font-weight` Values (2 instances)
- `css/components/navigation.css:16` — `font-weight: 600` → `var(--weight-semibold)`
- `css/utilities/animations.css:147` — `font-weight: 600` → `var(--weight-semibold)`

### 🟡 P1 — Hardcoded `border-radius` (1 instance)
- `css/components/validation.css:74` — `border-radius: 6px` → `var(--radius-sm)`

### 🟢 P2 — Inconsistent Transition Definitions (49 instances)
49 transition declarations across CSS files use hardcoded durations/timings instead of referencing `--transition-interactive` or dedicated transition variables. The `css/base/transitions.css` file defines theme-switch transitions but individual component transitions are all inline.

### 🟢 P2 — Mixed DOM Access Patterns
- `js/ai.js` uses `document.getElementById()` **26 times** (never uses `$id` helper)
- `js/course.js` uses `$id()` **60+ times** (imports it from utils.js)
- `js/studio.js` uses `document.getElementById()` **24 times**
- `js/main.js` uses `document.getElementById()` **24 times**
- Total: **147 raw `document.getElementById`** calls across files that could use the `$id` helper

### 🟢 P2 — Mixed `localStorage` Access Patterns
- `js/storage.js` provides a safe `storage` wrapper with try/catch
- `js/ai.js` bypasses it with **8 direct `localStorage.*` calls** (lines 43, 60, 65, 122, 142, 349, 758, 988)
- `js/sync-service.js` has **2 direct calls** (lines 110, 119)

---

## 3. Code Quality — Types, Console Logs, Error Handling

### 🔴 P0 — `console.log` in Production Frontend Code (7 instances)
These are debug logs that should be removed or gated behind a debug flag:

| File:Line | Content |
|-----------|---------|
| `js/ai.js:291` | `console.log('[AI] sending message:', text.substring(0, 50))` |
| `js/ai.js:314` | `console.log('[AI] SSE stream started')` |
| `js/ai.js:319` | `console.log('[AI] stream complete, text length:', ...)` |
| `js/ai.js:668` | `console.log('[AI] streaming bubble created, typing indicator visible')` |
| `js/ai.js:685` | `console.log('[AI] first chunk received, loader replaced with static avatar')` |
| `js/ai.js:715` | `console.log('[AI] bubble finalized, text length:', ...)` |
| `js/ai.js:734` | `console.log('[AI] step-info:', message)` |

### 🟡 P1 — `console.warn/error` in Frontend Code (47 instances)
While some are legitimate error reporting, many are redundant with user-facing toast messages:

**`js/ai.js`** — 17 console.warn/error calls (lines 45, 62, 66, 138, 239, 241, 262, 307, 308, 322, 363, 452, 551, 652, 767, 815, 857, 1003, 1006)

**`js/storage.js`** — 5 console.error calls (lines 5–9). The `storage` module already returns fallback values; the console.error is noisy for expected quota errors.

**`js/data-service.js`** — 5 console.warn calls (lines 37, 52, 173, 219, 531)

**`js/auth.js`** — 4 console.warn calls (lines 44, 82, 97, 119)

**`js/sync-service.js`** — 4 console.warn calls (lines 91, 95, 123, 147)

**Other files** — `js/course.js:437`, `js/course-calc.js:86`, `js/fe-compute.js:643`, `js/formula-editor.js:248`, `js/holidays.js:120`, `js/studio.js:144`

### 🟡 P1 — 29 `: any` Type Annotations in `server/src/agent/tools.ts`
The tools.ts file has **29 instances** of `: any` typing, making it the most loosely-typed file in the server:

- Lines 92–95: `courses: any[], keyFn: (c: any) => string, initFn: (c: any) => T, accFn: (acc: T, c: any) => void`
- Lines 111, 122, 133: `function _computeXxxRanking(courses: any[])`
- Line 144: `Record<string, any>`
- Lines 171, 173, 181: `courses: any[], allCourses: any[], conflicts: any[]`
- Lines 249, 283, 289, 347, 351, 430, 474, 539, 544, 566, 569, 575: `const where: any`, `const result: any`, `.map((s: any) =>`, `.filter((c: any) =>`

These should use Prisma-generated types or defined interfaces.

### 🟡 P1 — 17 `z.any()` in Server Zod Schemas
Zod `z.any()` defeats the purpose of schema validation:

| File | Count | Lines |
|------|-------|-------|
| `server/src/agent/write-tools.ts` | 7 | 753, 754, 755, 797, 801, 848, 852 |
| `server/src/routes/compute.ts` | 5 | 10, 11, 12, 14, 23, 25 |
| `server/src/routes/formulas.ts` | 3 | 30, 31, 32 |
| `server/src/routes/courses.ts` | 1 | 32 |
| `server/src/routes/studios.ts` | 1 | 15 |

The formula `params`, `blocks`, and `variables` fields should have proper Zod schemas since their structure is known (defined in `fe-params.js` and `fe-compute.js`).

### 🟡 P1 — Duplicated CONFLICT Error Handling (4 instances)
The same pattern is copy-pasted in multiple places:

```javascript
if (err.message === 'CONFLICT') {
  this.ui.toast('資料已被修改，請重新整理後再試', { type: 'error' });
  return;
}
```

- `js/course.js:270` (save existing)
- `js/course.js:308` (update with recurring)
- `js/course.js:324` (delete)
- `js/studio.js:170` (delete)

This should be extracted to a shared `handleConflictError(err, ui)` utility.

### 🟡 P1 — Inconsistent Error Handling in `js/ai.js`
The AI module has **16 try/catch blocks** with inconsistent patterns:
- Some catch with `console.warn` only (lines 45, 66, 241, 262, 307, 363, 767, 815, 1003, 1006)
- Some catch with `console.warn` + user feedback (lines 321, 451)
- Some catch with `console.error` only (lines 138, 551)
- Some catch with `console.warn` + fallback behavior (lines 61–67)
- Line 856: catch with `console.warn` only, no user feedback for failed history load

### 🟡 P1 — Silent `catch {}` and `catch { }` in Server Code
- `server/src/routes/admin.ts:96` — `catch {}` completely swallows DNS resolution errors
- `server/src/agent/formula-eval.ts:530-531` — `catch { params = []; }` and `catch { blocks = []; }` silently default on parse failure
- `server/src/plugins/auth.ts:32` — `catch { }` silently ignores JWT verification failure (returns 401 but no logging)
- `server/src/index.ts:55,68` — `catch { }` silently ignores errors

### 🟢 P2 — `js/ai.js` Repeated DOM Lookups
`document.getElementById('ai-chat-area')` is called **12 times** (lines 126, 192, 206, 350, 374, 476, 625, 651, 691, 735, 823, 990). Should be cached as a class property.

Similarly, `document.getElementById('ai-input')` appears at lines 281, 620, and `document.getElementById('ai-send-btn')` at line 604.

### 🟢 P2 — `js/ai.js` Bypasses `storage` Module
8 direct `localStorage` calls instead of using the safe `storage` wrapper:
- `localStorage.getItem('ai_settings')` — lines 43, 758
- `localStorage.setItem('ai_chat_history', ...)` — lines 60, 65
- `localStorage.getItem('ai_chat_history')` — line 122
- `localStorage.setItem('ai_settings', ...)` — line 142
- `localStorage.removeItem('ai_chat_history')` — lines 349, 988

### 🟢 P2 — `js/sync-service.js` Bypasses `storage` Module
- `localStorage.getItem('fc_last_sync')` — line 110
- `localStorage.setItem('fc_last_sync', ...)` — line 119

### 🟢 P2 — Server Routes Missing Logger Usage
These route files have **zero** logger calls, meaning errors are silently lost in production:
- `server/src/routes/auth.ts` (0 logger calls)
- `server/src/routes/courses.ts` (0)
- `server/src/routes/studios.ts` (0)
- `server/src/routes/compute.ts` (0)
- `server/src/routes/formulas.ts` (0)
- `server/src/routes/sync.ts` (0)
- `server/src/agent/tools.ts` (0)
- `server/src/agent/write-tools.ts` (0)

Only `admin.ts`, `ai.ts`, and `formula-eval.ts` use the logger.

---

## Summary Statistics

| Metric | Value |
|--------|-------|
| Total JS lines (frontend) | 13,117 |
| Total CSS lines | 3,536 |
| Total TS lines (server) | 5,278 |
| Files > 500 lines | 15 |
| Unused icon exports | 14 |
| Unused image files | 9 |
| Dead npm dependencies | 2 (`jsonwebtoken`, potentially `uuid`/`dotenv`) |
| Misplaced dev deps | 1 (`embedded-postgres` in prod deps) |
| Hardcoded colors in CSS | 20 |
| Hardcoded spacing in CSS | 28 |
| Hardcoded font-size in CSS | 6 |
| `console.log` in production JS | 7 |
| `console.warn/error` in frontend | 47 |
| `: any` in server TS | 29 |
| `z.any()` in server schemas | 17 |
| Silent `catch {}` in server | 5 |
| node_modules total | **676MB** (536MB server + 140MB root) |
