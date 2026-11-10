**Documentation-only backlog / technical continuation record. DRAFT — DO NOT MERGE.**

Preserve the planned ROMarr UI consistency initiative so a future session can resume without relying on conversation memory. Header/sidebar alignment comes first, followed by a comprehensive page audit and small, independently verified cleanup changes. This record does not implement or deploy the initiative.
**Latest status (November 10, 2026 PST):** UI-01 (desktop header/divider alignment) and UI-02 (hide the inactive global Filter on Add New) were accepted upstream via [ROMarr PR #145](https://github.com/BlizzHacker/romarr/pull/145), merged at `a41b8bdeb3b52fa42dd12a16df14b84f3f037541`, and included in the official [v1.8.1 release](https://github.com/BlizzHacker/romarr/releases/tag/v1.8.1). The release notes credit `@TenchiMisaki` and report production deployment. The owner separately reports the change live; the owner's CT107 Docker revision was **not** independently inspected. Fork implementation [PR #5](https://github.com/TenchiMisaki/romarr/pull/5) is now closed/merged following safe fork-main synchronization. **The broader UI consistency audit remains open; this documentation-only Backlog PR stays draft/open.** See §12.\n\n**Current progress (November 9, 2026 PST):** UI-01 desktop header/divider and UI-02 inactive Add New Filter have since been browser-previewed and implemented together in a separate, unmerged [fork PR #5](https://github.com/TenchiMisaki/romarr/pull/5). The historical observations and proposed separate-PR sequence below are preserved as originally written; **§11 is the latest status and supersedes older "unmeasured / no implementation PR" statements.** No deployed-code or automated-test PASS is claimed.


## 1. Authorization, scope and provenance

Prepared November 9, 2026 (America/Los_Angeles). The owner explicitly authorized one documentation-only draft Backlog PR in the personal fork, a new isolated notes branch from fork main, a companion file under docs/proposals/, and the complete same record in the PR body. No application changes, production/preview operations, upstream submission, main-branch update or merge are authorized by this task.

The initiating discussion was “UI Polish: Standardize Header Height.” The owner described cleaning up all the various pages as a major goal and identified header alignment as the first step. The later “Bug: Zip instead a Zip Issue” discussion established Backlog PRs as complete future-session handoffs, not short feature summaries. Its November 9 closeout reports that updated Homelab references 00 and 70 were published, including decision HL-GIT-03 and section 1.1. The owner directed this session to that discussion after older local references were found.

**Reference access limitation:** Local copies of 00/10/50/70 were consulted for relevant history, boundaries and process. Local 00/70 predate the November 9 backlog amendment. The November 9 publication confirmation and process were recovered from the named conversation; the updated Project Knowledge files themselves were not independently read or hash-verified in this session. Do not label this a fresh full current-document audit. The owner's current explicit instructions specify the backlog procedure used here.

Private source records remain private. Do not publish local hostnames, IP addresses, account paths, credentials, configuration, browser sessions, ROM files or download details in future additions.

## 2. Pinned repository state and related work

- Personal fork: [TenchiMisaki/romarr](https://github.com/TenchiMisaki/romarr), public, main verified at `041a367cedeb1c4b66365a9daea6a095cc753d55`.
- Upstream: [BlizzHacker/romarr](https://github.com/BlizzHacker/romarr), main verified at `9bf31ffcef3913798252e4c678f12f1544b07a2a`.
- Notes branch: `notes/ui-consistency-roadmap`, created from the pinned personal-fork main, not the newer upstream main or an existing contribution/review branch.
- Companion record: `docs/proposals/ui-consistency-roadmap.md`.
- Fork PR inventory checked across all states: #1 metadata correction review (merged), [#2 full metadata comparison](https://github.com/TenchiMisaki/romarr/pull/2) (open review-only), and [#3 BlueRoms backlog](https://github.com/TenchiMisaki/romarr/pull/3) (open). No duplicate UI consistency backlog found.
- Upstream PR inventory checked across all states. [#134](https://github.com/BlizzHacker/romarr/pull/134) and [#136](https://github.com/BlizzHacker/romarr/pull/136) already merged responsive sidebar work. Preserve and evaluate that implementation rather than proposing it as missing.
- [#140 Metadata persistence](https://github.com/BlizzHacker/romarr/pull/140) is now merged, as is [#143](https://github.com/BlizzHacker/romarr/pull/143). Earlier discussion calling #140 active is historical. Do not modify its branches or mix its behavior into this initiative.
- GitHub Issues remain disabled on the fork. Earlier attempts to use parent/child issues failed according to the prior discussion; no issue numbers were actually created. Previously suggested roadmap issue numbers were illustrative. Do not repeat the incorrect Settings-link detour or change repository settings to implement this backlog.

These are point-in-time repository facts, not proof of released, installed or browser-verified behavior. Fork main differs from upstream main; no synchronization is part of this record.

## 3. Intended outcome and constraints

Make existing ROMarr pages visually consistent while preserving the current design, navigation and behavior. Avoid a broad redesign, feature removal or one large cleanup patch. Shared layout corrections should precede repeated page-specific overrides.

Initial goal: align the sidebar brand/header and page top bar so their boundaries are visually coherent at applicable desktop sizes, with intentional responsive behavior. Exact pixel height, accepted tolerance and whether wrapping requires a minimum rather than fixed height are **UNDECIDED**. No current screenshot measurements or reproduced defect are claimed.

Preserve navigation groups, selected-route indication, search, theme/accent controls, keyboard operation, mobile drawer, focus handling, scrolling, existing accessible names and no-script fallback. Do not make Metadata lookups, settings persistence or other asynchronous interactions regress as an incidental layout change.

## 4. Source inspection and implementation anchors

Focused source inspection only, against [romarr/ui.py at the pinned upstream revision](https://github.com/BlizzHacker/romarr/blob/9bf31ffcef3913798252e4c678f12f1544b07a2a/romarr/ui.py). This is not a full source review, browser reproduction or validated patch.

Relevant locations at that revision:

- Around lines 118–191: sidebar rail, brand area, footer and sticky top-bar styles; inspect actual padding, borders, font metrics, controls and box sizing together.
- Around lines 481–507: earlier 820px and 540px responsive rules change rail widths, brand sizing/padding and top padding.
- Around lines 511–560: later category-navigation rules redefine rail width and provide the 700px drawer transition; the 701–820px rule adjusts main margin. CSS cascade/order is relevant. Do not edit an earlier rule in isolation and assume it wins.
- Around lines 578–605: no-script navigation/theme fallback rules.
- Around lines 1103–1172: sidebar interaction/focus-related code to inspect before changing structural markup.
- Around line 1228: route-specific top title assignment; around line 1238: page-renderer registry begins.
- Around line 5758 onward: navigation markup and native toggle.

The presence of multiple media rules is a source observation, not proof of the visual defect's root cause. Future investigation must inspect the complete relevant selectors, markup, renderer lifecycle and tests at a freshly pinned revision.

**Proposed approach, not implemented:** measure existing top/brand bounding boxes and computed styles, then consider one shared header sizing rule or token with consistent border/box sizing and alignment. Prefer minimum sizing that accommodates content where appropriate; do not force a chosen height before testing long titles, zoom and mobile controls. Preserve intentional differences between permanent desktop navigation and the mobile drawer.

## 5. Incremental roadmap

- [ ] Establish an isolated baseline and reproduce/measure header alignment.
- [ ] Implement and validate the smallest header/sidebar alignment correction under separate development authorization.
- [ ] Audit every actual route/page from the then-current navigation and renderer inventory.
- [ ] Define concise shared standards for header geometry, spacing, margins, section headings, reusable layout and control placement.
- [ ] Standardize filters, search fields, dropdowns and buttons without changing their functional semantics.
- [ ] Address confirmed page-specific inconsistencies in small independent changes.
- [ ] Validate responsive behavior across pages and retain before/after evidence.

Do not freeze a historical count of 31 or 32 pages into the acceptance criterion. Generate the current route inventory, including conditional/hidden pages, and record exclusions with reasons.

For each audited page capture route/name, source renderer, viewport and theme, observed layout, intended exception versus actual inconsistency, reproducible steps, screenshot/measurement evidence where useful, impact, proposed smallest correction and acceptance checks.

Prioritize overlapping/clipped/unusable content above inconsistent layout or filter placement, and those above minor whitespace or subtle alignment polish. These are triage rules, not claims that every listed defect exists.

## 6. Validation and acceptance plan

All future behavior checks below are **NOT TESTED for this initiative**.

| Area | Required evidence |
|---|---|
| Header alignment | Before/after geometry at the same viewport, font state and zoom; documented intended boundary and tolerance |
| Breakpoints | Wide desktop and immediately around current 820px, 700px and 540px rules; inspect actual current breakpoints again |
| Content stress | Long page titles, search field, visible controls, text zoom and narrow windows without clipping or overlap |
| Navigation | Every route remains reachable; group expansion and selected state preserved; Back/Forward and direct navigation work |
| Mobile drawer | Open/close, scrim, focus entry/return, keyboard behavior, scrolling and viewport-height handling preserved |
| Accessibility | Visible focus, readable contrast, zoom/reflow, reduced motion and meaningful control names |
| Themes | Existing light/dark/sepia and accent choices remain legible and aligned |
| Fallback | Existing no-script behavior remains usable where supported |
| Functional regression | Relevant page controls, forms and asynchronous navigation remain operational |
| Review | Inspect entire scoped diff, run relevant existing tests and CodeRabbit, disposition findings; report missing coverage |
| Runtime | Separately authorized isolated preview verification, exact restore and stable health evidence if preview is modified |

Tests must match the change. Static syntax, simulated DOM, screenshots, CodeRabbit and actual application tests are distinct evidence. No previous Metadata test count or upstream suite report proves this UI initiative works.

## 7. Safety, recovery and rejected shortcuts

Keep production, shared downloads, real ROM libraries and protected Project Knowledge unchanged. A preview container is not assumed safe merely because it has a separate name: prior documentation records shared writable download access. Future UI tests should avoid acquisition/import/cleanup and use isolated benign fixtures where needed.

If later authorized to patch preview, first verify node and guest identity, service/container/image/source, access, backup and recovery prerequisites. Preserve the exact original outside the container, provide independent recovery and immediate revert, restart only the approved service if necessary, restore the exact original by hash and verify stability. Recheck current 10/50 safeguards, including any newer recovery requirements, before APPLY. A restart alone does not remove a source patch.

Rejected or deferred approaches: broad redesign; unmeasured arbitrary fixed heights; page-by-page duplicated CSS when a shared correction is appropriate; issue creation requiring a settings detour; mixing with Metadata review work; assuming merged means installed; promoting source inspection into runtime PASS.

No runtime change occurs for this backlog, so operational rollback is not required. This notes branch and draft are the durable record; do not merge or delete them automatically.

## 8. Evidence gaps and continuation checklist

Missing: original detailed header screenshots/measurements, any earlier exact CSS proposal not present in the retrieved discussion, a full current page inventory, complete source-review coverage, local installed revision, browser/device baseline and automated regression fixtures for this initiative. Do not reconstruct missing evidence from guesses.

On resumption:

1. Read this entire PR body and companion file; compare for drift and preserve newer evidence.
2. Read actual newest Homelab 00/10/50/70, especially 70 section 1.1; do not treat the older local copies as current.
3. Recheck fork/upstream main, related issues/PRs, existing backlog and relevant releases. Determine whether upstream already addressed the intended behavior.
4. Pin an implementation baseline separately from this historical notes-branch base; preserve all existing main/contribution/review branches.
5. Recover prior screenshots or reproduce the alignment with recorded viewport, theme, zoom and source revision.
6. Complete relevant source and page inventory, choose the smallest correction, and obtain the appropriate development/runtime authorization before implementation.
7. Run meaningful tests, review and isolated visual acceptance; preserve failures and coverage gaps.
8. Update both this file and the full PR body with findings, rejected attempts, exact source/test evidence and next steps under the applicable authorization.
9. Consider a separate upstream submission only after its independent source-review, verification, Preview and owner-approval requirements are met.

## 9. Verification evidence for this documentation task

Performed: prior-conversation recovery; relevant local reference consultation with version limitation disclosed; live fork/upstream identities and SHAs; all-state PR and fork branch inventories; focused pinned UI source inspection; raw Markdown/link structure review and privacy review. No duplicate UI backlog appeared in the inspected fork PR inventory.

Official guidance consulted: [creating a pull request](https://docs.github.com/en/pull-requests/how-tos/create-pull-requests/creating-a-pull-request) and [GitHub Markdown syntax](https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax).

**GITHUB PREVIEW: NOT VERIFIED.** Native Write/Preview was not inspected. API readback is separate from rendered Preview and does not certify upstream submission readiness.

Application code changes: NONE. Production/preview operations: NONE. Runtime tests: NONE. Full codebase review: NOT PERFORMED. CodeRabbit review: NOT RUN for this documentation record. This draft records future work; it does not claim that the UI defect is fixed.

## 10. Source-based UI audit expansion — November 9, 2026 (America/Los_Angeles)

**Status: READ-ONLY SOURCE AUDIT COMPLETE FOR THE INITIAL NAVIGABLE UI INVENTORY; VISUAL AND RUNTIME ACCEPTANCE NOT TESTED.** This is a dated continuation of the owner-requested audit after creating this backlog; it adds findings without changing earlier evidence or implying any issue is fixed. The owner approved updating **this existing documentation-only draft PR and its companion** after reviewing the audit. That approval does **not** include code changes, upstream publication, merging, runtime access, or protected Homelab Project Knowledge edits.

### 10.1 Baseline, coverage and provenance

- Exact upstream source inspected: [\`BlizzHacker/romarr@9bf31ffcef3913798252e4c678f12f1544b07a2a\`, \`romarr/ui.py\`](https://github.com/BlizzHacker/romarr/blob/9bf31ffcef3913798252e4c678f12f1544b07a2a/romarr/ui.py), file blob SHA \`ca32bad5eccfb7715219e1886402d607c170b79d\`. Upstream \`main\` remained at this commit when the backlog update was preflighted.
- Personal fork \`main\`: \`041a367cedeb1c4b66365a9daea6a095cc753d55\`. Its frontend blob differs; this backlog branch is **not** the implementation baseline. Re-pin both source trees before later implementation.
- Inventory reviewed: six sidebar navigation groups, **32 named routes**, each with a \`RENDER.<route>\` declaration, shared shell, responsive CSS, navigation/search lifecycle, representative page-top markup, and relevant existing tests. This is a **scoped structural/source audit**, not a full source-code security/functional audit and not a rendered-pixel or installed-version audit.
- User-reported original observation: the divider between sidebar logo/header and main header appears vertically misaligned on pages, particularly where the top filter disappears. No original screenshot, viewport dimensions, computed heights, zoom setting, browser measurements, or live reproduction was provided in this audit.
- Effective Homelab guidance \`00\`, \`10\`, \`50\`, \`70\` was independently retrieved and read from Project Knowledge for the November 9 follow-up. This **supersedes the earlier Section 1 local-document access gap for this dated audit only**. The documents' historical PR #140 and preview statuses are dated; a current GitHub PR state cannot be inferred from them.
- Source audit and GitHub read-only calls: performed. DOM/browser execution, pixel comparisons, screenshots, local pytest/Node/Chromium test runs, actual preview and production inspection: **NOT TESTED**.

### 10.2 Complete navigable page inventory (source structure only)

| Sidebar group | Routes (source renderers) | Source-derived main presentation / review target |
|---|---|---|
| Library (4) | \`library\` (Games), \`add\` (Add New), \`discover\` (Discover), \`search\` (Interactive Search) | Game-cover grid and filters; separate search forms; mode/shelf controls; consistent top spacing |
| Wanted (3) | \`missing\`, \`lists\`, \`calendar\` | Action rows over tables; date controls and calendar cards |
| Activity (3) | \`queue\`, \`history\`, \`blocklist\` | Action rows, standalone tables, blocked-item card/empty state |
| Hub (4) | \`hub\` (Plugins), \`portal\` (Library Shell), \`peers\` (Friends), \`ecosystem\` | Plugin catalogue/search/chips, long tabs, embedded library shell, information cards |
| Settings (10) | \`general\`, \`media\`, \`profiles\`, \`indexers\`, \`clients\`, \`libraries\`, \`connections\`, \`metadata\`, \`setup\`, \`getstarted\` | Reusable settings form helper, card headers, controls/actions, status tables, setup flow |
| System (8) | \`status\`, \`stats\`, \`update\`, \`platforms\`, \`collections\`, \`manualimport\`, \`tasks\`, \`logs\` | Information cards, audit and planning forms, large tables, scrolling logs |

**Inventory interpretation:** A renderer declaration and existing test contracts are not evidence that each page's layout was rendered successfully. Count actual routes from the current \`NAV\` and \`RENDER\` at each new source revision; track conditional/hidden pages separately. No page-specific visual defect should be claimed solely because two renderers use different markup.

### 10.3 Findings and precise anchors (source evidence vs. untested user impact)

| ID / priority | Source-grounded finding | Risk / boundary | Minimal proposed follow-up |
|---|---|---|---|
| UI-01 / First implementation | [\`#brand\` and \`#top\` styles](https://github.com/BlizzHacker/romarr/blob/9bf31ffcef3913798252e4c678f12f1544b07a2a/romarr/ui.py#L118-L192) independently set padding, font geometry and different border tokens (\`--line-soft\` vs \`--line\`). No shared height token. In [\`go(page)\`](https://github.com/BlizzHacker/romarr/blob/9bf31ffcef3913798252e4c678f12f1544b07a2a/romarr/ui.py#L1206-L1230), hiding \`#search\` on most routes changes natural header content. | **Likely explanation** for owner-reported misalignment, not yet browser-measured root cause. | Measure brand/top rectangles, border coordinates, computed padding and input visibility before selecting shared sizing; preserve mobile close button and title behavior. |
| UI-02 / Medium, separate UX correction | \`go(page)\` shows the global top \`Filter…\` on both \`library\` and \`add\`, but the [input handler near the JS boot](https://github.com/BlizzHacker/romarr/blob/9bf31ffcef3913798252e4c678f12f1544b07a2a/romarr/ui.py#L5689-L5722) returns unless the active page is \`library\`. [Add New](https://github.com/BlizzHacker/romarr/blob/9bf31ffcef3913798252e4c678f12f1544b07a2a/romarr/ui.py#L1696-L1710) has a separate game-search form. | **Source-confirmed inert visible control on Add New**; real-user reproduction not performed. Filter text may persist in the global field when returning to Games (verify). | Decide whether to hide the global filter on Add New or explicitly assign it a meaningful role. Do not combine with UI-01; keep original behavior unchanged in CSS-only patch. |
| UI-03 / Medium maintainability | Shared \`.page\`, \`.card\`, \`.row\`, \`.btn\`, \`.field\` and \`.cat-bar\` rules exist, but renderers add many differing inline margins, gaps, widths, font sizes and headers. [Games controls](https://github.com/BlizzHacker/romarr/blob/9bf31ffcef3913798252e4c678f12f1544b07a2a/romarr/ui.py#L1530-L1605), [Wanted action row](https://github.com/BlizzHacker/romarr/blob/9bf31ffcef3913798252e4c678f12f1544b07a2a/romarr/ui.py#L1817-L1833), [Queue row](https://github.com/BlizzHacker/romarr/blob/9bf31ffcef3913798252e4c678f12f1544b07a2a/romarr/ui.py#L3273-L3293), and [Settings rows](https://github.com/BlizzHacker/romarr/blob/9bf31ffcef3913798252e4c678f12f1544b07a2a/romarr/ui.py#L3898-L4025) are representative. | **Implementation differences verified**, but visual inconsistency and desired normalization must be decided by screenshots. | Establish a small set of common page-top layout patterns **after** visually comparing action rows, filters, tabs and headings; do not force every page into the same component. |
| UI-04 / Higher accessibility review | [ROM Hub filter chips](https://github.com/BlizzHacker/romarr/blob/9bf31ffcef3913798252e4c678f12f1544b07a2a/romarr/ui.py#L1307-L1324), [Library Shell tabs](https://github.com/BlizzHacker/romarr/blob/9bf31ffcef3913798252e4c678f12f1544b07a2a/romarr/ui.py#L2750-L2759), and [Ecosystem tabs](https://github.com/BlizzHacker/romarr/blob/9bf31ffcef3913798252e4c678f12f1544b07a2a/romarr/ui.py#L2951-L2987) create clickable \`<span class="chip">\` elements with \`onclick\` wiring but no inspected keyboard equivalent. [Games tiles](https://github.com/BlizzHacker/romarr/blob/9bf31ffcef3913798252e4c678f12f1544b07a2a/romarr/ui.py#L1624-L1639) are clickable \`<div>\` elements. | **Source-confirmed keyboard-semantic concern**: ordinary span/div elements do not naturally participate in Tab/Enter/Space navigation. Actual assistive-technology testing not done. | Separate accessible native-button semantics, focus/pressed-state and key navigation review while keeping current look and mouse behavior. Test screen reader and keyboard when available. |
| UI-05 / Responsive risk | Earlier [820px/540px breakpoints](https://github.com/BlizzHacker/romarr/blob/9bf31ffcef3913798252e4c678f12f1544b07a2a/romarr/ui.py#L481-L507) overlap with later [701–820px and ≤700px sidebar rules](https://github.com/BlizzHacker/romarr/blob/9bf31ffcef3913798252e4c678f12f1544b07a2a/romarr/ui.py#L511-L560); the later desktop rules retain the 222px rail through 701px. \`#top h1\` uses \`white-space:nowrap\`, and \`.chip\` also prevents wrapping. | Source-confirmed cascade and wrapping constraints; clipping or overflow **NOT TESTED**. Long title examples include Collections and Library Shell. | Test computed styles and actual layout at 320/375/390 and around 540/700/701/820/821px, at 100% and increased zoom. Preserve native/no-script drawer fallback and close-control clearance. |
| UI-06 / Responsive risk | [Missing](https://github.com/BlizzHacker/romarr/blob/9bf31ffcef3913798252e4c678f12f1544b07a2a/romarr/ui.py#L1817-L1833) and [Queue](https://github.com/BlizzHacker/romarr/blob/9bf31ffcef3913798252e4c678f12f1544b07a2a/romarr/ui.py#L3273-L3293) output multiple table columns directly under the page; [Libraries](https://github.com/BlizzHacker/romarr/blob/9bf31ffcef3913798252e4c678f12f1544b07a2a/romarr/ui.py#L3970-L4000) has seven columns. The [direct-table styling](https://github.com/BlizzHacker/romarr/blob/9bf31ffcef3913798252e4c678f12f1544b07a2a/romarr/ui.py#L297-L311) intentionally provides its own card-like chrome, not a scroll wrapper. | Wide table overflow is a **hypothesis**, not observed. Changes could disrupt tables or scrollbars. | Measure real overflow first. If confirmed, use the smallest localized responsive/scroll treatment; preserve standalone-table appearance. |
| UI-07 / Layout dependency | [ROM Hub \`.cat-scroll\`](https://github.com/BlizzHacker/romarr/blob/9bf31ffcef3913798252e4c678f12f1544b07a2a/romarr/ui.py#L212-L216) uses \`max-height:calc(100vh - 340px)\`, Library Shell embeds a \`height:74vh\` iframe, and Logs uses \`max-height:70vh\`. | Shared top-header height changes can alter space available, especially on short screens; behavior **NOT TESTED**. | Compare scrolling, sticky header, footer reachability, nested-scroll usability and focused control visibility before/after UI-01. |
| UI-08 / Preservation | Existing shared UI styling and responsive navigation are established. [PR #134](https://github.com/BlizzHacker/romarr/pull/134) and [PR #136](https://github.com/BlizzHacker/romarr/pull/136) are **merged** and document historical desktop/mobile/no-script/keyboard Chromium coverage. Existing \`tests/test_sidebar.py\`, \`tests/sidebar_dom.js\`, \`tests/test_ui_pages.py\`, and \`tests/test_ui.py\` provide regression starting points. | Do **not** confuse reported PR test histories with reruns on current source or browser geometry verification for the header change. | Reuse tests for equivalent unchanged behavior and add a focused real-browser header-boundary assertion plus screenshot comparisons on the final patch SHA. |

### 10.4 Source evidence supporting shared-first implementation

- [Shared components and styles](https://github.com/BlizzHacker/romarr/blob/9bf31ffcef3913798252e4c678f12f1544b07a2a/romarr/ui.py#L194-L316) already include filter strips, cards, forms, buttons, tables and empty states. Retain the visual language; avoid creating a duplicate design framework.
- Main template near [\`page()\`](https://github.com/BlizzHacker/romarr/blob/9bf31ffcef3913798252e4c678f12f1544b07a2a/romarr/ui.py#L5754-L5771) renders \`#rail > #brand\`, \`#main > #top\` (hamburger, \`h1\`, \`#search\`), and \`#page\`. The page header and content live in different DOM containers; normalizing the header may cause a small vertical content-origin shift even if no content styles are edited.
- Distinct page intentions should remain: Games has platform chips and filters, ROM Hub has searchable catalogue chips, Calendar has date controls, Settings uses forms, Queue/History deliberately display direct tables, and Logs has a separate scrolling log view.
- CSS-only proposed patch **must not** alter typography, labels, search/filter semantics, card/table dimensions, button action, navigation state, modal focus, data loading or API calls. Determine \`height\` vs \`min-height\` from measured content geometry and overflow, **not** the former provisional 66/60/56px sizes.

### 10.5 Acceptance and test matrix (planned, none executed in this audit)

| Target | Planned measurement / regression check |
|---|---|
| Desktop search visible | Games and Add New: sidebar brand bottom border vs top-header border; title/search geometry; unchanged field interaction (including documented Add New inert behavior until separate UX change) |
| Desktop search hidden | Representative pages from every nav group, including Calendar, Metadata, Stats, Queue, and Logs; no header-height jump on navigation |
| Breakpoints | At least 320, 375, 390, 540, 700, 701, 820, 821 and wide desktop viewport widths; use actual rendered browser pixels and record zoom/font settings |
| Menus and keyboard | Native/JS mobile drawer, hamburger close control, focus entry/return, direct/hash navigation, all 32 routes and Back/Forward |
| Text and accessibility | Long top titles, large text zoom, labels/control names, keyboard-only chips/tiles, visible focus, reduced motion |
| Content | No unexpected movement beyond header-origin normalization, no altered card/grid/table sizing, no new horizontal/vertical page overflow |
| Specialized scroll | ROM Hub catalogue; Library Shell iframe; Logs; long Settings/Collections pages; short-height viewports |
| Themes | Dark, light and warm/sepia, chosen accent, readable border/color distinction |
| Quality | Existing targeted Python/Node tests, new browser bounding-rect assertion with measured allowed delta, before/after screenshots, applicable CodeRabbit review of **separate implementation PR** |
| Operational isolation | No production or preview interaction unless independently approved and protected under current \`10\` recovery gates |

**Important:** Rendering in a real browser has **not** been performed; none of these test rows is a PASS. No exact alignment delta or fix is yet proven.

### 10.6 Prioritized follow-up and future-assistant resume sequence

1. **UI-01 first: align shared header boundary.** Re-pin current upstream/fork and create a separate isolated **implementation** branch only with fresh owner approval. Build a browser-measured baseline (source SHA, viewport width/height, theme, zoom, visible/hidden top filter, header boxes and dividers). Select minimal shared CSS rule and validate against all 32 page routes. Keep the global filter's present behavior unchanged for this CSS patch.
2. **UI-04 accessible controls / UI-02 Add New filter:** Treat as independent usability improvements. First determine desired UX and test true keyboard/tab/activation behavior. Do not roll semantic or JS edits into the header-alignment diff.
3. **UI-03 page-top consistency audit:** Capture per-page screenshots/measurements and document justified exceptions. Choose a small reusable pattern for action rows, filters, tabs and card headings rather than applying one universal layout.
4. **UI-05/06/07 responsive and scroll polish:** Prioritize confirmed clipping, overflow, unusable controls and nested scroll issues. Verify before changing.
5. **Then detailed per-page cleanup:** Create individually scoped, source-grounded changes with before/after evidence, independent review and rollback. Keep functionality and aesthetics unless the owner explicitly chooses a different design.

**Unresolved:** No measured header heights; no original screen captures; no browser fixture proving the owner-reported visual issue; no broad accessibility audit; no visual confirmation of table overflow; no live installed ROMarr revision. Do not convert these gaps into assertions of failure. Earlier source-only inventory is reusable for this pinned SHA but must be rechecked when code changes.

### 10.7 Audit evidence register / publication boundaries

- **Source read:** \`romarr/ui.py\` CSS shell, route titles/search, 32 \`RENDER\` declarations and representative markup; associated sidebar/page test files; merged PR #134/#136 descriptions. **SOURCE INSPECTED**, not execution.
- **GitHub state:** This Backlog PR remains documentation-only in \`TenchiMisaki/romarr\`. Review PR #2 and unrelated Backlog PR #3 are separate. No feature or CodeRabbit code-review PR is created by this audit.
- **Current Project reference access:** \`00\`/\`10\`/\`50\`/\`70\` current documents independently read for the November 9 update. Later Project Knowledge publication/OneDrive sync: **NOT MODIFIED OR VERIFIED**.
- **Tests:** Validation performed: **source and repository-state inspection only**. Python/Node syntax/pytest/Chromium/browser measurements/real hardware/preview/production: **NOT TESTED**.
- **GitHub Preview:** **NOT VERIFIED** unless actual Write and Preview tabs are subsequently inspected. API read-back and Markdown file equality alone are not rendered Preview evidence.
- **Change boundaries:** This update is expected to change only the versioned Markdown backlog file and its matching draft PR body. Do not merge, convert draft, close, retarget to upstream, trigger CodeRabbit, change production or preview, or edit protected homelab references under this authorization.

## 11. Browser measurements and implementation progress — November 9, 2026 PST

**Status amendment / authority:** The original §1–§10 investigation remains preserved as dated evidence. In this later session the owner explicitly approved (a) testing the UI in the development browser, (b) creating a focused fork implementation PR, (c) combining the two small top-bar corrections in that existing implementation PR, and (d) updating this backlog. This is **not** approval to merge the fork PR, promote upstream, modify running containers or change protected homelab references. Where prior §10 said measurements were unavailable, no implementation PR existed, or UI-01 and UI-02 must be separate, the **newer observed results and owner decision below supersede that planning status**, without retroactively changing the earlier audit.

### 11.1 Reproduced desktop and mobile baseline

Measurements were reported from a Chromium-based development browser on November 9, 2026 PST using read-only DOM geometry scripts. They represent the **running development preview at the time**, not a confirmed match to GitHub's latest source SHA. Public backlog details intentionally omit the private lab address, node identity and service configuration.

| Layout / page | CSS viewport | Sidebar brand height | Main top-bar height | Divider offset (brand bottom minus top bottom) | Global Filter |
| --- | --- | ---: | ---: | ---: | --- |
| Desktop — Games (`#library`) | 1920 × 911 | 65px | 62.50px | +2.50px | Visible |
| Desktop — Settings / Metadata (`#metadata`) | 1920 × 911 | 65px | 53.34px | +11.66px | Hidden |
| Narrow responsive layout — Games | 500 × 575 | 65px | 58.59px | +6.41px | Visible |
| Narrow responsive layout — Settings / Metadata | 500 × 575 | 65px | 58.59px | +6.41px | Hidden |

For both desktop pages the computed border colors differed: `#brand` = `rgb(31, 37, 48)` / `--line-soft`, whereas `#top` = `rgb(40, 46, 58)` / `--line`. Desktop top-bar height depends on whether the filter is rendered. At widths ≤700px the sidebar is a slide-out drawer, not a permanent connected desktop rail, so the 6.41px narrow-layout offset **does not itself establish a user-visible divider defect**. Initial measurements at 1920px after manually shrinking a Chrome window were misleading because the inspector still reported its original 1920px tab; corrected narrow-window measurements subsequently confirmed `mobileLayout:true` at 500px. This is a desktop responsive test, **not physical-phone validation**.

### 11.2 Temporary browser-only fixes and observed results

**Header/divider UI-01 experiment:** A temporary `<style>` element inserted through the developer console applied this desktop-only rule:

```css
@media (min-width: 821px) {
  #top {
    min-height: 65px;
    border-bottom-color: var(--line-soft);
  }
}
```

The script validated that the test was running on the intended development-origin page, was on Games, and that the 65px brand baseline matched before applying the style. Results:

| Desktop route | Original offset | Post-override offset | Post-override border colors |
| --- | ---: | ---: | --- |
| Games (`#library`) | 2.50px | **0px — PASS** | Match |
| Settings / General (`#general`) | Not measured before | **0px — PASS** | Match |
| Settings / Metadata (`#metadata`) | 11.66px | **0px — PASS** | Match |

The CSS test applied only within that browser document, was not persisted, and would disappear on refresh. No running application files or containers were updated by the browser test. Existing global `box-sizing:border-box` includes padding and border in the 65px min-height. This is **browser geometry evidence for the experimental override**, not execution of the later Git commit or proof of stress/responsive accessibility.

**Add New global Filter UI-02 experiment:** At `#add`, another temporary browser script changed only the DOM's `#search` visibility using the existing `hide` class. The reported `RESULT_JSON` showed `globalFilterBefore:true`, `globalFilterAfter:false`, `dedicatedGameFormPreserved:true`, `gameInputPresent:true`, `platformSelectPresent:true`, and `searchButtonPresent:true`; script reported **PASS**. This confirmed that hiding the global Filter did not remove the separate **Game**, **Platform**, and **Search & Grab** form elements. **No actual game request, indexer search, API submission, or Games → Add New → Games regression was executed.** Refresh restores the original page state.

Source-level explanation: `go(page)` had allowed `#search` on both `library` and `add`, while the global Filter `oninput` handler returns immediately unless the route is `library`. Add New independently uses `#g-name`, `#g-plat` and `#g-go`. The owner elected to hide the inactive shared Filter on Add New instead of assigning it new functionality.

### 11.3 Current combined implementation: fork PR #5 (separate from this draft backlog)

- **PR:** [TenchiMisaki/romarr#5 — Fix top header alignment and inactive Add New filter](https://github.com/TenchiMisaki/romarr/pull/5).
- **PR type and scope:** Non-draft **fork-to-fork-main implementation PR**, open/unmerged at last check. Its source branch is `fix/desktop-header-divider-alignment`, based on personal-fork `main` commit `041a367cedeb1c4b66365a9daea6a095cc753d55`. This backlog remains a separate, **draft documentation-only** PR.
- **Combined implementation head:** `131fcc616912f74d89f63b2381cc9ba7bd907ce6` (after initial header-only commit `8aa8f716be37e4c1769f21060a140be3d5f3ff2e`). **One modified file:** `romarr/ui.py`, exactly **3 additions / 1 deletion** versus fork main, in two scoped source locations.
- **Header CSS:** adds the desktop-scoped media query above and an explanatory comment; retains existing mobile CSS and its drawer behavior.
- **Filter routing:** replaces `$('#search').classList.toggle('hide', !['library','add'].includes(page));` with `$('#search').classList.toggle('hide', page !== 'library');`. The global Filter remains shown only on Games. The Add New dedicated request form and the underlying global search input handler are unchanged.
- **Reason for combining:** The owner initially preferred separate submissions, but after both browser previews opted for **one small cohesive top-bar correction PR**. It is a tightly scoped exception to the earlier separate-PR roadmap, **not** a general rule to group unrelated UI fixes.
- **CodeRabbit:** the header-only commit `8aa8f716` received a completed review reporting **no actionable comments**. Its result **cannot** be promoted to the combined head. At this backlog-update check the CodeRabbit check for `131fcc6169` was **completed with success status; inspect comments/threads for actual findings**; recheck the exact-head check, full current comment body and review threads. A successful check only proves the review finished, not that no findings exist.
- **GitHub verification for combined head:** PR title/base/head and source diff independently read back. No upstream PR or deployment was performed by this branch update. Exact GitHub rendered **Write/Preview** remains **NOT VERIFIED**.
- **Tests:** browser-only experiments above **PASS within their stated scope**; committed-source syntax/pytest/Chromium/real running-app tests remain **NOT TESTED**. The deployed development source revision is not verified to equal this GitHub commit.

### 11.4 Remaining work and safe resumption order

1. **Finish combined PR #5 before upstream proposal.** Recheck its exact head SHA and CodeRabbit completion; inspect all inline threads and comments for actual actionable suggestions. Resolve real problems only via a separately authorized revision and repeat exact-head review. Do not merge or submit upstream by implication.
2. **Run focused source and UI tests on the combined committed revision** without assuming browser preview is equivalent: verify no Python/HTML/JS syntax break, Games filter still updates Games, Add New has no visible inactive global Filter, its dedicated game form works through non-destructive navigation and input checks, back-navigation preserves/clears state as intended, desktop dividers remain aligned when input visibility changes, and no breakpoint regression around 700/701/820/821px or long-title/zoom stress. Do not execute real game requests during a layout test. Record actual test commands/versions/results only when run.
3. **Keep runtime APPLY gated:** Current homelab reference `10` documents the independent five-minute preview recovery watchdog as **NOT INSTALLED/ACCEPTED**. A fork PR and browser-only DOM override do not authorize or prove a live container patch. Production must remain untouched. Verify precise preview source/backup/hash/recovery protections before any later owner-approved deployment.
4. **Resume the wider 32-route UI audit** from §10.2–§10.6. Next priorities: UI-04 semantic keyboard/accessibility behavior; UI-03 page-top action/filter/card spacing patterns; UI-05 breakpoint/clipping; UI-06 wide-table overflow (still a hypothesis until measured); UI-07 scrolling/short viewport behavior; detailed route-by-route checks thereafter. Use small separate future changes, actual visual/browser evidence, focused tests and a justified exception list rather than a wholesale redesign.
5. **Maintain documentation integrity:** this draft backlog PR description and this Markdown companion should be kept **byte-for-byte synchronized**. Update current status with dated amendments rather than erasing the original source-only audit. Any new upstream operation, staging work, merge or protected homelab reference publication needs its own explicit scope and approval.

**Evidence status at this update:** GitHub fork branch/source/PR diffs were read back; browser observations were supplied by the owner in-session; no local syntax/test runner or live container was executed by this backlog update. Project Knowledge and OneDrive copies were not changed. **GITHUB PREVIEW: NOT VERIFIED.**

### 11.5 Exact-head CodeRabbit review completion — November 9, 2026 PST

**New verified evidence, after the preceding §11.3 check:** The CodeRabbit GitHub check on combined fork PR #5 head `131fcc616912f74d89f63b2381cc9ba7bd907ce6` completed with conclusion **success** at `2026-11-10T03:33:40Z` (November 9, 2026 PST). GitHub's CodeRabbit [review comment](https://github.com/TenchiMisaki/romarr/pull/5#issuecomment-6757992099) explicitly states **“No actionable comments were generated in the recent review.”** Its embedded coverage metadata identifies the same exact head SHA, and a separate read of PR #5's review threads found **zero threads**. Therefore: **exact-head CodeRabbit review complete, no actionable findings observed in this review**. This supersedes the earlier “review still requires inspection” status, without erasing its dated evidence. It does **not** certify automated tests, all possible issues, upstream acceptance, deployment, or a future amended commit.

**Next gate:** Focused source/runtime-independent testing of the actual combined committed revision remains pending; do not treat the earlier browser-only experiments as executed-code PASS. Validate navigation/filter behavior, relevant responsive boundaries, long titles/zoom and no-script/accessibility cases where practical; separately authorize any protected preview deployment, upstream submission or merge. PR #5 and this backlog PR remain **open and unmerged** at this check.

## 12. First UI Improvements Merged Upstream and Released — November 10, 2026 (America/Los_Angeles)

**Latest disposition:** The initial two scoped UI improvements, UI-01 and UI-02, are **MERGED UPSTREAM and INCLUDED IN THE OFFICIAL v1.8.1 RELEASE**. This supersedes the earlier *open/unmerged, not submitted, and not released* statements in §§5, 10, and 11 **as of the milestones below**; those historical observations and their evidence remain preserved. The wider 32-route UI consistency work is **not completed**.

### 12.1 Independently confirmed publication and ancestry

| Milestone | Verified evidence | Scope |
|---|---|---|
| Initial fork implementation | [Fork PR #5](https://github.com/TenchiMisaki/romarr/pull/5), final contributor head `09845c28073b16493aa0ab112ad234d5e9dcc7c4` | Two cohesive UI changes in `romarr/ui.py`, separate from this draft backlog |
| Official acceptance | [Upstream PR #145](https://github.com/BlizzHacker/romarr/pull/145) **merged** by `BlizzHacker` on November 9, 2026 at 22:13 PST (November 10, 06:13 UTC) | Official `main` merge commit `a41b8bdeb3b52fa42dd12a16df14b84f3f037541` |
| Personal-fork reconciliation | [Fork-sync workflow run 42769987481](https://github.com/TenchiMisaki/romarr-fork-sync/actions/runs/42769987481) | Safe non-force fast-forward of fork `main` to `a41b8bd`; upstream/fork `main` observed identical. Fork PR #5 then reported **merged** at November 9, 22:39 PST because its base contained the upstream merge; this is **not** a second upstream PR |
| Official release | [ROMarr v1.8.1](https://github.com/BlizzHacker/romarr/releases/tag/v1.8.1), published November 10, 2026 at 05:22 PST (13:22 UTC) | GitHub comparison of `a41b8bd` and tag `v1.8.1` reported **identical** at the check. Release notes explicitly credit `@TenchiMisaki` for #145 |

### 12.2 The first two implemented fixes

- **UI-01 — Completed for its scoped desktop change:** At desktop widths **821px and above**, sidebar branding and the main header use matching 60px heights and divider color. Mobile and broader responsive acceptance remain separate testing scopes.
- **UI-02 — Completed for its scoped route behavior:** The global top **Filter** appears on **Games** only and is hidden on **Add New**, where it had no filtering action. Add New's dedicated Game, Platform and Search & Grab controls remain separate.
- **Out of scope for this implementation:** The general 32-route consistency audit, other page spacing/control issues, accessibility review, clipping and scrolling concerns, comprehensive mobile testing and any broader redesign. Do not treat the two merged fixes as completion of those tasks.

### 12.3 Evidence and deployment boundaries

**Direct GitHub verification:** Official PR #145 merge, fork PR #5 merged state, matching upstream/fork default-branch tips, and GitHub release/tag comparison were checked. The maintainer's **v1.8.1 release notes report** a green full test suite (approximately 2,300 tests) and deployment/verification on the maintainer's production install. Those are **maintainer-reported release statements**, not tests independently rerun for this backlog amendment.

**Owner report:** The owner confirms that the contributed change is live. This is recorded separately from GitHub's source merge and the maintainer's deployment report. The specific installed ROMarr Docker image digest, code revision and behavior on the owner's `pve-garage/CT107` have **NOT been independently checked**. Do not claim that an upstream merge, a release, or this documentation change updated the owner's container. Earlier scoped browser previews and CodeRabbit evidence in §11 remain dated; they are not retroactively a final-release runtime test.

**No operational mutation:** This update changes only the documentation record. It does not modify ROMarr source, either default branch, the release, production/preview containers, release tags, or any protected Homelab references.

### 12.4 Remaining backlog and next resumption

UI-01 and UI-02 have reached upstream merge and release; retain their prior uncompleted checkboxes in §5 as **historical planning**, superseded by this newer status. Continue the main UI consistency initiative from §10's original 32-route source inventory, refreshing against the actual current upstream source before new work. Prioritize source-grounded follow-up areas UI-03 (page/control spacing), UI-04 (keyboard/accessibility), UI-05 (responsive widths/clipping), UI-06 (table overflow), and UI-07 (scrolling/short viewport); none is marked fixed or runtime-verified by PR #145.

**Backlog lifecycle:** Keep [this PR #4](https://github.com/TenchiMisaki/romarr/pull/4) **draft, open, labeled `backlog`**, on `notes/ui-consistency-roadmap` with base `TenchiMisaki/romarr:main`. Do not merge, close, remove its label, change its base, or modify an implementation branch simply to record this milestone. The PR description and `docs/proposals/ui-consistency-roadmap.md` are intended to remain exactly synchronized. `GITHUB PREVIEW: NOT VERIFIED` unless the owner later checks GitHub's rendered Write/Preview.



## 13. Related Update-page backlog — November 10, 2026 (America/Los_Angeles)

**Cross-reference only; this remains the global UI-consistency backlog.** A separate, independently scoped [draft Backlog PR #6 — ROMarr System → Update: Build Identity, Correct Update Status, and Docker Guidance](https://github.com/TenchiMisaki/romarr/pull/6) now owns the proposed **System → Update** screen's version status, build identity, update check/auto-apply semantics, Git/Docker update guidance and minimal per-page UI improvements. Its companion is [`docs/proposals/romarr-system-update-build-identity-plan.md`](https://github.com/TenchiMisaki/romarr/blob/notes/romarr-system-update-version-identity-plan-20261110/docs/proposals/romarr-system-update-build-identity-plan.md); [the proposed rendered mockup](https://github.com/TenchiMisaki/romarr/blob/notes/romarr-system-update-version-identity-plan-20261110/docs/proposals/assets/romarr-system-update-page-proposed.svg) deliberately follows the **existing** page card order and controls instead of redrawing the sidebar or navigation. This UI backlog keeps ownership of global component consistency, navigation/header styling, responsive widths and accessibility; do **not** implement a second Update-page redesign here.

**Implementation distinction:** PR #6 remains **DRAFT / NOT TO MERGE**. Its proposed five child PRs are separate from this UI roadmap. The first foundation candidate is already present on an isolated fork [`feature/romarr-build-provenance-pr1`](https://github.com/TenchiMisaki/romarr/tree/feature/romarr-build-provenance-pr1) at commit [`631933c`](https://github.com/TenchiMisaki/romarr/commit/631933ccb57fa257b3b92bbdc0ec66be46a77a00), where the API and both Docker variants carry optional source provenance. It is **not yet a merged/installed UI improvement**, and non-tag images still retain an unknown release version pending subsequent changes. No finished non-draft implementation PR, exact-head CodeRabbit clearance, full-suite/docker-image/live-UI result or upstream acceptance was found/claimed by this cross-reference.

**Reusable UI validation from the prior Sidebar v26 investigation:** The older November 6 report had a browser/static check matrix for 32 routes, desktop/mobile navigation, keyboard focus/Tab/Escape, responsive scrolling and theme states, but was based on an older upstream commit and expressly lacked full-suite/live-patched acceptance. Reuse the *test categories and caution about evidence*, never transfer a historical PASS to this new Update-page commit. For later PR #6 child UI work, verify existing **This install** three tiles, extra compact build/ref line, four-row **Automatic updates**, button visibility, container guidance, conditional plugin table/log, long SHA/ref escaping, narrow viewport and theme consistency. Coordinate layout changes with this general UI backlog so that source of truth and acceptance criteria do not drift.

**Audit-dependent related issue, owned only by PR #6 child PR 3:** Current source allows separate scheduled/manual update-check paths, holds the queue lock only through queue inspection and then launches a detached updater using shared script/log filenames. Overlap is a **source-derived plausible race, NOT runtime reproduced**. The dedicated Update-system backlog proposes single-flight launch coordination and fault-injection interleaving tests. Do not modify global UI structure or produce an independent code PR in this backlog to fix it.

**Status and verification:** This dated pointer is documentation only. PR #4 remains **draft/open/backlog, not merged**, with the originally accepted UI-01/UI-02 progress and the historical rest of the roadmap unchanged. Fork/upstream main matched at `a41b8bd` in the read-only audit. No live Docker, Proxmox, production, preview, fork `main`, protected Homelab reference, browser screenshot or CodeRabbit action was performed by this update. **GITHUB PREVIEW: NOT VERIFIED** by connector readback.

**Future-session rule:** Check the latest PR #6 for Update-page-specific data/acceptance changes *before* editing that screen under this broader UI initiative. Cross-reference new related child PRs in both backlogs only when independently verified; do not mark the broad UI audit or the Update system completed based on a planning PR or unmerged feature branch.
