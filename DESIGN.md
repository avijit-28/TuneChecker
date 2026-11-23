# DESIGN.md: UI/UX Design System

**Product:** Sales Call Quality Analysis Agent
**Source of truth:** `PRD.md` (v1.0). Requirement IDs (M1, FR-T5, etc.) are referenced throughout.
**Audience:** Designers and AI coding assistants implementing the interface. Follow this document literally. Do not make independent design decisions. If something is not specified here, reuse the closest existing component and flag the gap.
**Status:** Draft v1.0. No application code is specified here, only design tokens, layouts, behavior and copy.

---

## Table of Contents
1. Brand Identity
2. Color System
3. Typography
4. Layout and Design Tokens
5. Application Navigation
6. Screens (A-G)
7. Component Specifications
8. Responsive Design
9. Accessibility
10. Visual Direction and References
11. Design Rules
12. Design Decision Log
13. Appendix: Token Reference (CSS custom properties) and Copy Deck

---

## 1. Brand Identity

### 1.1 Positioning
A calm, precise analysis tool for sales managers. The interface behaves like an auditor's workbench: it shows a verdict, then immediately shows the proof. It never celebrates, never decorates, and never claims more than the evidence supports.

### 1.2 Brand Attributes and How the UI Expresses Them
| Attribute | UI expression |
|---|---|
| Trust and reliability | Consistent layouts, honest states (no fake progress), explicit failure messages, no overclaiming copy |
| AI-powered intelligence | A restrained "AI interpretation" label (sparkle icon) wherever the model wrote the content. No robot imagery, no glowing effects |
| Professional performance analysis | Dense-but-ordered data layouts, tabular numerals, neutral palette with one brand accent |
| Clarity and transparency | Verdict first, evidence next, transcript always one click away. Settings used are always visible on a result |
| Evidence-based decisions | Verbatim quotes are visually distinct from AI text (see 7.12, 7.13). Every verdict and action item links to a transcript line |

### 1.3 Name and Mark
- **Display name:** "Sales Call Quality Agent" (short form in sidebar and tab title). Full product name "Sales Call Quality Analysis Agent" is used on the About page and document title.
- **Logo mark:** Lucide `audio-lines` icon, 24px, in `--color-primary`, followed by the wordmark in Inter 600, 16px. No custom illustration, no gradient. Collapsed sidebar shows the icon only.
- **Favicon:** the same icon on a solid `--color-primary` rounded square, white glyph.

### 1.4 What to Avoid (explicit)
- Cartoon or character illustrations, mascots, confetti, emoji in UI chrome.
- Gradients (except none: zero gradients are used anywhere in this system).
- Decorative blobs, glassmorphism, glow shadows, parallax.
- Animated counters, bouncing, pulsing "AI thinking" effects.
- Celebratory copy ("Great job!", "Awesome!").

### 1.5 Iconography
- **Library:** Lucide (outline). One library only.
- **Sizes:** 16px (inline with text and in chips), 20px (default in buttons, nav, cards), 24px (empty-state headers, banner icons use 20px), 48px (verdict icon, empty-state glyph inside a 72px circle).
- **Stroke:** 1.75px at 20px and 24px, 2px at 16px. Icons inherit `currentColor`.
- **Icon families with fixed meaning (do not mix):**
| Meaning | Icons |
|---|---|
| Tone RED | `shield-alert` |
| Tone GREEN | `shield-check` |
| Tone not analyzed | `shield` (outline) |
| System success | `circle-check` |
| System warning | `triangle-alert` |
| System error | `octagon-x` |
| System info | `info` |
| AI-generated content | `sparkles` |
| Verbatim transcript quote | `quote` |

Rule: the shield family is **reserved for tone**. The circle-check / triangle-alert / octagon-x family is **reserved for system states**. Never swap them.

---

## 2. Color System

All colors are tokens. **Never use a raw hex value in a component**; always reference a token. Values below are the only permitted colors in the product. Contrast targets: normal text >= 4.5:1, large text and UI component boundaries >= 3:1. Implementers must run an automated contrast check (axe or equivalent) on every screen in both themes.

### 2.1 Theme Behavior
- Default follows the operating system (`prefers-color-scheme`).
- A theme toggle in the top bar offers **System / Light / Dark**. The choice persists in `localStorage` (wrapped in try/catch; falls back to System).
- Theme is applied via `data-theme="light|dark"` on `<html>`; tokens are defined for both.

### 2.2 Core Palette

| Token | Light | Dark | Usage |
|---|---|---|---|
| `--color-primary` | `#4338CA` | `#8E9BFF` | Brand, primary buttons, links, active nav, focus accents |
| `--color-primary-hover` | `#3730A3` | `#A9B4FF` | Primary hover |
| `--color-primary-active` | `#2E2A8A` | `#C0C8FF` | Primary pressed |
| `--color-primary-subtle` | `#EEF0FF` | `#1C2250` | Tinted backgrounds (selected rows, AI-interpretation blocks, rep speaker segments) |
| `--color-primary-border` | `#C7CCF8` | `#3A4590` | Borders on subtle primary surfaces |
| `--color-on-primary` | `#FFFFFF` | `#0B0E17` | Text/icons on solid primary |
| `--color-secondary` | `#475569` | `#A3AEC2` | Secondary buttons, secondary icons |
| `--color-secondary-subtle` | `#EEF1F5` | `#1D2436` | Secondary button background, neutral chips |
| `--color-bg` | `#F5F6FA` | `#0B0E17` | App background |
| `--color-surface` | `#FFFFFF` | `#131826` | Cards, panels, tables, inputs |
| `--color-surface-elevated` | `#FFFFFF` | `#1B2132` | Modals, popovers, dropdown menus, toasts (with shadow) |
| `--color-surface-sunken` | `#EEF0F6` | `#0F1320` | Table headers, input wells, customer transcript segments |
| `--color-text-primary` | `#111827` | `#EDF0F7` | Headings, body |
| `--color-text-secondary` | `#4A5568` | `#B4BCCF` | Supporting text, labels |
| `--color-text-tertiary` | `#5B6678` | `#8E98AE` | Hints, timestamps, metadata |
| `--color-text-disabled` | `#9AA3B2` | `#5A6480` | Disabled text (exempt from contrast, always paired with disabled styling) |
| `--color-border` | `#DDE1EA` | `#2A3147` | Card and table borders |
| `--color-border-strong` | `#B9C0CF` | `#3D4663` | Input borders (meets 3:1 vs surface in light mode: verify), dividers needing emphasis |
| `--color-divider` | `#E7EAF1` | `#222942` | Row separators, section dividers |
| `--color-focus-ring` | `#4338CA` | `#B3BCFF` | Focus indicator (2px ring, 2px offset) |
| `--color-scrim` | `rgba(17,24,39,0.48)` | `rgba(0,0,0,0.64)` | Modal and drawer overlay |

### 2.3 Tone Classification Colors (RED / GREEN): reserved tokens

**These tokens are used ONLY for tone classification (verdict banner, tone badges, tone chart segments, tone filters, evidence marker on a RED verdict). They must never be used for system success, system error, form validation, or any other purpose.**

| Token | Light | Dark | Usage |
|---|---|---|---|
| `--tone-red-solid` | `#B42318` | `#F97066` | Solid RED badge fill, chart segment |
| `--tone-red-on-solid` | `#FFFFFF` | `#1A0705` | Text on solid RED |
| `--tone-red-fg` | `#B42318` | `#FDA29B` | RED text/icons on tinted background |
| `--tone-red-bg` | `#FEF3F2` | `#2D1210` | RED tinted background |
| `--tone-red-border` | `#FDA29B` | `#7A2E26` | RED tinted border |
| `--tone-green-solid` | `#067647` | `#32D583` | Solid GREEN badge fill, chart segment |
| `--tone-green-on-solid` | `#FFFFFF` | `#04170D` | Text on solid GREEN |
| `--tone-green-fg` | `#067647` | `#6CE9A6` | GREEN text/icons on tinted background |
| `--tone-green-bg` | `#ECFDF3` | `#0C2417` | GREEN tinted background |
| `--tone-green-border` | `#75E0A7` | `#1C5A3A` | GREEN tinted border |
| `--tone-none-solid` | `#5B6678` | `#8E98AE` | "Not analyzed" chart segment and badge outline |
| `--tone-none-bg` | `#EEF1F5` | `#1D2436` | "Not analyzed" badge background |
| `--tone-none-border` | `#C9D0DD` | `#3D4663` | "Not analyzed" badge border |

Semantics (fixed):
- **RED** means exactly: "Negative sales representative tone detected, supported by verified transcript evidence under the configured criteria."
- **GREEN** means exactly: "No negative sales representative tone detected under the configured criteria." It does **not** mean "good", "excellent" or "approved". Never write copy that implies positive quality.
- **Not analyzed** (neutral) means the call has no tone result (in progress, failed, or partial).

### 2.4 System State Colors (generic application states)

Deliberately **different hues** from the tone colors so RED/GREEN are never confused with error/success.

| Token | Light | Dark | Hue family |
|---|---|---|---|
| `--success-fg` | `#0E7490` | `#5EC9E0` | Cyan |
| `--success-bg` | `#ECFEFF` | `#0A2630` | |
| `--success-border` | `#A5F3FC` | `#155E75` | |
| `--warning-fg` | `#854D0E` | `#FACC15` | Gold |
| `--warning-bg` | `#FEFCE8` | `#2A2108` | |
| `--warning-border` | `#FDE68A` | `#6B5410` | |
| `--error-fg` | `#C2410C` | `#FB923C` | Vermilion orange |
| `--error-bg` | `#FFF7ED` | `#2E1608` | |
| `--error-border` | `#FDBA74` | `#7C3A12` | |
| `--error-solid` | `#C2410C` | `#FB923C` | Destructive button fill |
| `--error-on-solid` | `#FFFFFF` | `#1A0A02` | Text on destructive button |
| `--info-fg` / `--info-bg` / `--info-border` | alias of `--color-primary` / `--color-primary-subtle` / `--color-primary-border` | alias | Info banners |

Usage rules:
- System success (cyan) is used for: upload complete, settings saved, stage completed, export complete. It always carries the `circle-check` icon.
- System error (vermilion) is used for: failures, validation errors, destructive buttons. It always carries the `octagon-x` icon.
- System warning (gold) is used for: low speaker-role confidence, partial analysis, unverifiable evidence dropped, settings-differ notices. It always carries the `triangle-alert` icon.

### 2.5 Speaker and Highlight Colors (transcript)
| Token | Light | Dark | Usage |
|---|---|---|---|
| `--speaker-rep-bar` | `#4338CA` | `#8E9BFF` | 3px left bar on rep segments |
| `--speaker-rep-bg` | `#EEF0FF` | `#1C2250` | Rep segment background (same as primary-subtle) |
| `--speaker-customer-bar` | `#8A94A8` | `#6B7694` | 3px left bar on customer segments |
| `--speaker-customer-bg` | `#EEF0F6` | `#0F1320` | Customer segment background (same as surface-sunken) |
| `--speaker-unknown-bar` | `#8A94A8` | `#6B7694` | Dashed 3px left bar, no fill, for unlabeled segments |
| `--highlight-search` | `#FEF08A` | `#6B5410` | Search match background (text stays `--color-text-primary`) |
| `--highlight-search-current` | `#FACC15` | `#A16207` | Current search match |
| `--highlight-evidence-underline` | alias `--tone-red-solid` | alias | 2px underline of evidence span (RED verdict only) |
| `--highlight-linked` | alias `--color-primary-subtle` + 2px outline `--color-focus-ring` | | Segment currently linked from a clicked evidence/action card |

Customer and rep segments are distinguished by **label, bar style, background and alignment position**, never by color alone (see 7.12).

### 2.6 Chart Colors
Tone distribution chart (see 6A) uses tone tokens plus non-color encodings:
| Series | Fill | Pattern (required) |
|---|---|---|
| RED | `--tone-red-solid` | Diagonal stripes (45deg, 2px lines every 6px, `--tone-red-on-solid` at 35% opacity) |
| GREEN | `--tone-green-solid` | Solid |
| Not analyzed | `--tone-none-solid` at 40% opacity | Dotted (1.5px dots every 6px) |

### 2.7 Contrast Notes
- Text on tinted tone backgrounds uses the matching `*-fg` token (>= 4.5:1 in both themes by construction; verify).
- Solid badges use `*-on-solid` text (>= 4.5:1).
- `--color-text-tertiary` must only be used at 12px+ for supplementary content, never for the only copy carrying essential meaning.

---

## 3. Typography

### 3.1 Font Families
| Role | Family | Fallback stack |
|---|---|---|
| UI and body | **Inter** (variable, weights 400-700) | `Inter, ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif` |
| Monospace (timestamps, file metadata, JSON) | **JetBrains Mono** (400, 500) | `"JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, Consolas, monospace` |

Fonts are self-hosted or loaded from Google Fonts with `font-display: swap`. Enable `font-feature-settings: "tnum" 1, "cv11" 1` for numerals on data elements (KPI numbers, tables, timestamps, counts) so digits align.

### 3.2 Type Scale
| Token | Size / line height | Weight | Use |
|---|---|---|---|
| `--text-display` | 36px / 44px | 700 | KPI numbers only |
| `--text-verdict` | 32px / 40px | 700, letter-spacing 0.02em | RED/GREEN verdict word |
| `--text-h1` | 28px / 36px | 600 | Page titles |
| `--text-h2` | 22px / 30px | 600 | Section titles |
| `--text-h3` | 18px / 26px | 600 | Card and panel titles |
| `--text-h4` | 16px / 24px | 600 | Sub-section titles, modal titles |
| `--text-body-lg` | 16px / 24px | 400 | Explanations, helper paragraphs, empty-state body |
| `--text-body` | 14px / 20px | 400 | Default UI text, table cells, form labels (weight 500 for labels) |
| `--text-body-sm` | 13px / 18px | 400 | Secondary metadata, chip text |
| `--text-caption` | 12px / 16px | 500 | Captions, helper and error text under inputs, overlines |
| `--text-overline` | 12px / 16px | 600, uppercase, letter-spacing 0.06em | Panel eyebrows ("FROM THE TRANSCRIPT") |

Page-level base font size is 16px; sizes above are in px for clarity and implemented in rem. Minimum rendered text size is 12px. Users' browser font-size and zoom up to 200% must not break layouts.

### 3.3 Weights
400 regular (body), 500 medium (labels, buttons-secondary, chips), 600 semibold (headings, buttons, table headers), 700 bold (KPI numbers, verdict).

### 3.4 Transcript Typography (priority: readability)
| Element | Spec |
|---|---|
| Transcript text | Inter 400, **15px / 24px**, `--color-text-primary`, `max-width: 72ch` within the segment text column, `text-wrap: pretty`, `hyphens: manual` |
| Speaker label | Inter 600, 12px / 16px, `--color-text-primary` ("Sales Rep" / "Customer" / "Speaker unknown") |
| Timestamp | JetBrains Mono 500, 12px / 16px, `--color-text-tertiary`, format `m:ss` (or `h:mm:ss` for >= 1 hour), tabular |
| Segment spacing | 12px vertical padding, 8px gap between segments |
| Mobile | Transcript text 16px / 26px |
| Quoted text in evidence/action cards | Inter 400 italic **not used**; use normal style inside the quote block with the quote icon (see 7.13). Quotes are verbatim, wrapped in typographic quotes |

### 3.5 Data and Metric Typography
| Element | Spec |
|---|---|
| KPI number | `--text-display`, tabular numerals, `--color-text-primary` (tone cards use matching `*-fg` for the number) |
| KPI label | `--text-body-sm`, `--color-text-secondary`, weight 500 |
| KPI delta/footnote | `--text-caption`, `--color-text-tertiary` |
| Table numerals | 14px tabular |
| File metadata (name, size, duration) | Filename in Inter 500 14px; size and duration in JetBrains Mono 400 13px |
| Chart axis and legend text | 12px / 16px, `--color-text-secondary` |

---

## 4. Layout and Design Tokens

### 4.1 Spacing Scale (4px base)
`--space-0: 0`, `--space-1: 4px`, `--space-2: 8px`, `--space-3: 12px`, `--space-4: 16px`, `--space-5: 20px`, `--space-6: 24px`, `--space-8: 32px`, `--space-10: 40px`, `--space-12: 48px`, `--space-16: 64px`.
Use only these values for padding, margin and gap. Default card padding is `--space-6` (24px), compact cards `--space-4` (16px).

### 4.2 Border Radius
| Token | Value | Use |
|---|---|---|
| `--radius-xs` | 4px | Inline highlights, small chips inside text |
| `--radius-sm` | 6px | Inputs, buttons, chips, tabs |
| `--radius-md` | 8px | Cards, tables, panels, transcript segments |
| `--radius-lg` | 12px | Modals, verdict card, upload drop zone |
| `--radius-full` | 9999px | Pills, status dots, avatar-like circles, toggle track |

### 4.3 Shadows and Elevation
| Token | Light | Dark | Use |
|---|---|---|---|
| `--shadow-none` | none | none | Cards (rely on 1px border) |
| `--shadow-sm` | `0 1px 2px rgba(16,24,40,0.06)` | `0 1px 2px rgba(0,0,0,0.4)` | Buttons (secondary), sticky save bar |
| `--shadow-md` | `0 4px 12px rgba(16,24,40,0.10)` | `0 4px 12px rgba(0,0,0,0.5)` | Dropdown menus, popovers, toasts |
| `--shadow-lg` | `0 12px 32px rgba(16,24,40,0.16)` | `0 12px 32px rgba(0,0,0,0.6)` | Modals, mobile drawer |
Rule: cards are flat (1px `--color-border`, no shadow). Shadows are only for floating layers. In dark mode, floating layers also get a 1px `--color-border` outline.

### 4.4 Z-Index Scale
`--z-base: 0`, `--z-sticky: 100` (sticky panels, table headers), `--z-topbar: 200`, `--z-sidebar: 210`, `--z-dropdown: 300`, `--z-scrim: 400`, `--z-modal: 410`, `--z-toast: 500`.

### 4.5 Motion
- Durations: `--motion-fast: 120ms`, `--motion-base: 200ms`. Easing: `cubic-bezier(0.2, 0, 0, 1)`.
- Allowed motion: hover/focus color transitions, dropdown/modal fade (+ 4px translate), drawer slide, accordion height, spinner rotation, toast slide-in, skeleton shimmer.
- Not allowed: bouncing, scaling on hover, counting animations, progress bars that advance without real data.
- `prefers-reduced-motion: reduce`: disable translate/slide and shimmer (use static skeleton), keep opacity fades at 0ms, spinners become a static icon plus text "In progress".

### 4.6 Containers and Breakpoints
| Name | Range | Page side padding | Content max width |
|---|---|---|---|
| Mobile | < 640px | 16px | 100% |
| Tablet | 640-1023px | 24px | 100% |
| Laptop | 1024-1439px | 32px | 100% |
| Desktop | >= 1440px | 32px | 1360px, centered in space right of sidebar |

Text-heavy containers (About/Help article, modals): max width 720px (page) / 480-560px (modals).

### 4.7 Grid System
- 12 columns on Laptop and Desktop, 8 columns on Tablet, 4 columns on Mobile.
- Gutter: 24px (Laptop/Desktop), 16px (Tablet/Mobile). Vertical rhythm between cards: 24px (16px on Mobile).
- Cards span whole columns; do not use fractional widths.

### 4.8 App Shell Dimensions
| Element | Spec |
|---|---|
| Top bar | Height **64px** (56px on Mobile). `--color-surface`, 1px bottom border `--color-border`. Sticky, `--z-topbar` |
| Sidebar expanded | Width **248px**. `--color-surface`, 1px right border. Fixed, full height below no overlap with top bar (the top bar spans the content area only; the sidebar contains the logo at the top, 64px tall) |
| Sidebar collapsed | Width **72px** (icons only, tooltips on hover/focus) |
| Content area | `margin-left` = sidebar width, padding per breakpoint, background `--color-bg` |
| Page header | `--text-h1` title, optional 14px description in `--color-text-secondary`, actions right-aligned; 24px below it before content |

### 4.9 Card Layouts
| Card type | Padding | Header | Notes |
|---|---|---|---|
| Standard card | 24px | Title `--text-h3`, optional action at right, 16px gap to body | 1px border, `--radius-md`, `--color-surface` |
| Compact card | 16px | `--text-body` 600 | Used for evidence cards, action cards, KPI cards |
| KPI card | 20px | Label top, number below, footnote bottom | Min height 112px |
| Verdict card | 32px | Custom (see 6D) | `--radius-lg`, tone-tinted |
| Panel (results screen) | 0 body padding, header 16px 20px with 1px bottom divider | Title + count chip + tools | Scrolls internally where specified |

---

## 5. Application Navigation

### 5.1 Structure (fixed order)
| Order | Label | Icon (Lucide) | Route |
|---|---|---|---|
| 1 | Dashboard | `layout-dashboard` | `/` |
| 2 | Upload Call | `upload` | `/upload` |
| 3 | Call History | `history` | `/calls` |
| 4 | Analysis Settings | `sliders-horizontal` | `/settings` |
| 5 | About / Help | `circle-help` | `/help` |

Group: items 1-3 in the primary group; items 4-5 below a divider, pinned to the bottom of the sidebar. Call detail routes (`/calls/:id`, `/calls/:id/processing`) keep **Call History** active.

### 5.2 Sidebar Item States
| State | Spec |
|---|---|
| Default | 44px height, 12px horizontal padding, icon 20px + label 14px/500, `--color-text-secondary`, transparent background, `--radius-sm`, 8px outer margin |
| Hover | Background `--color-secondary-subtle`, text `--color-text-primary` |
| Focus-visible | 2px `--color-focus-ring` ring, 2px offset (never remove) |
| Active (current page) | Background `--color-primary-subtle`, text and icon `--color-primary`, weight 600, 3px left indicator bar in `--color-primary` inside the item's left edge; `aria-current="page"` |
| Pressed | Background one step darker than hover (`--color-primary-border` at 40% when active) |
| Disabled | Not used for nav items |
| Collapsed | 72px rail; icon centered; label hidden (still in DOM as `aria-label`); tooltip on hover/focus after 300ms showing the label, placed right; active state keeps bar and tinted background |
| Badge (optional) | Call History shows a count chip of in-progress calls when > 0 (`--color-secondary-subtle` bg, 12px text). Chip text is accompanied by an `aria-label` like "2 calls in progress" |

Sidebar header: logo mark + wordmark (64px high). A collapse/expand toggle (`panel-left-close` / `panel-left-open`, 20px) sits at the bottom of the sidebar above the pinned items group. State persists in `localStorage` (try/catch).

### 5.3 Top Bar
- Left: on Mobile the hamburger (`menu`) button; on all sizes the page breadcrumb (for call detail: "Call History / {call name}", 14px, last segment `--color-text-primary` 500, earlier segments are links).
- Right: **Upload call** primary button (hidden on the Upload page and on Mobile where it becomes an icon button `upload`, 40x40), theme toggle (icon button `sun-moon` opening a 3-item menu: System, Light, Dark).
- No avatar, no notifications, no global search (not in PRD).

### 5.4 Responsive Navigation
| Breakpoint | Behavior |
|---|---|
| Desktop (>= 1440) | Sidebar expanded by default, user can collapse |
| Laptop (1024-1439) | Sidebar expanded by default, user can collapse |
| Tablet (640-1023) | Sidebar collapsed (72px rail) by default; expanding overlays content with scrim (does not push) |
| Mobile (< 640) | Sidebar hidden. Hamburger opens a 280px drawer from the left with scrim, close on item select, Escape, scrim click, or swipe-left. Focus trapped in the drawer while open; focus returns to the hamburger on close |

Skip link: first focusable element is "Skip to main content" (visible on focus), targeting `<main id="main">`.

---

## 6. Screens

General rules for every screen:
- Page = `<main>` with one `<h1>`. Sections use `<h2>`.
- Every async region has loading (skeleton), empty, error and populated states.
- Skeletons mirror the final layout (same heights), use `--color-surface-sunken`, no spinners for lists/cards (spinners only for button loading and in-progress stages).
- Errors use the Banner (7.10) inline in the region where the failure happened, with a recovery action.

### 6A. Dashboard (`/`)

**Purpose:** at-a-glance state of analyzed calls, a path to upload, and the most recent results.

**Header:** H1 "Dashboard". Description: "Overview of analyzed calls and recent follow-ups." Action: primary button **Upload call** (icon `upload`).

**Layout (Laptop/Desktop, 12-col grid):**
```
[ KPI: Total analyzed ][ KPI: RED ][ KPI: GREEN ][ KPI: Awaiting analysis ]   (3 cols each)
[ Tone distribution (5 cols)          ][ Recent call analyses table (7 cols)  ]
[ Recent action items (12 cols, 2-column list on Desktop, 1-column on Laptop)  ]
```

**KPI cards (4):**
| Card | Number | Footnote | Number color |
|---|---|---|---|
| Total calls analyzed | Count of calls with status Complete | "All time" | `--color-text-primary` |
| RED tone calls | Count of Complete calls with RED | "{n}% of analyzed calls" (omit when total = 0) | `--tone-red-fg` |
| GREEN tone calls | Count of Complete calls with GREEN | "{n}% of analyzed calls" | `--tone-green-fg` |
| Calls awaiting analysis | Count of calls Uploaded or in progress | If any failed: link "{n} need attention" (opens Call History filtered to Failed), `--error-fg` text with `octagon-x` 16px | `--color-text-primary` |

RED and GREEN KPI cards also show their shield icon (20px) in the top-right corner and the word in the label ("RED tone calls"), so color is never the only cue. Cards are links to Call History pre-filtered by that tone (RED / GREEN / In progress); entire card focusable with visible focus ring; hover darkens border to `--color-border-strong`.

**Tone distribution card:**
- Title: "Tone distribution". Subtitle: "Analyzed calls only" (`--color-text-secondary`).
- Visualization: a **single horizontal stacked bar** (full width, 32px tall, `--radius-sm`), segments: RED (striped), GREEN (solid), and "Not analyzed" (dotted) only if calls awaiting analysis exist. Segment widths proportional to counts. Minimum visible width 4px for nonzero counts.
- Beneath the bar: legend rows with swatch (same pattern as bar), label ("RED", "GREEN", "Not analyzed"), count, and percentage. Counts tabular, right-aligned.
- Hover/focus on a segment: tooltip "RED: 3 calls (30%)". Segments are keyboard-focusable (`tabindex=0`, `role="img"` on the bar with `aria-label` summarizing "Tone distribution: 3 RED, 7 GREEN, 2 not analyzed").
- Toggle in card header: **Chart | Table** (segmented control). Table view is a real `<table>` with the same figures (accessible alternative).
- Empty (0 calls): bar replaced by text "No analyzed calls yet." with link "Upload your first call".

**Recent call analyses table (5 most recent):** columns Call, Uploaded, Status, Tone, (action) "View". "View all calls" link in the card header to `/calls`. Row click or View button opens `/calls/:id`. Uses Table component (7.7) in compact density.

**Recent action items (5 most recent across Complete calls):** each is an Action Item Card (compact variant, 7.14) showing task, owner chip ("Owner: Not specified" when null), deadline chip ("Deadline: Not specified" when null), and call name link + timestamp. Heading "Recent action items" with "View call" per item. Empty: "No action items yet. They appear here after a call is analyzed."

**States:**
| State | Spec |
|---|---|
| Loading | Skeleton KPI cards (4), skeleton bar and 5 skeleton rows; `aria-busy="true"` on region |
| Empty (no calls) | Replace the whole grid with the "No calls uploaded" empty state (6G.1) |
| Error | Region-level Banner (error) "We couldn't load your dashboard" with **Try again** |
| Partial (e.g., calls load, action items fail) | Failing card shows inline error banner and Retry; other cards remain |

### 6B. Upload Call (`/upload`)

**Purpose:** get a valid `.m4a` recording to the server with immediate, specific validation feedback. Covers M1, M2, FR-U1 to FR-U6.

**Header:** H1 "Upload call". Description: "Upload a recording to transcribe it, check the sales rep's tone, and list action items."

**Layout:** Two columns on Laptop/Desktop: left (8 cols) upload card; right (4 cols) "Before you upload" card. Single column on Tablet/Mobile (instructions card below upload card).

**Upload card, states:**

1. **Idle (drop zone)**
   - Dashed 2px border `--color-border-strong`, `--radius-lg`, min height 280px, `--color-surface`.
   - Center: 24px `upload` icon in a 56px circle `--color-primary-subtle` with icon `--color-primary`; line 1 "Drag and drop an .m4a recording here" (`--text-h4`); line 2 "or" (`--color-text-tertiary`); button **Browse files** (primary); line 3 caption "Supports .m4a, up to 50 MB, 10 seconds to 30 minutes" with a chip `.m4a` (`--color-secondary-subtle`, mono font).
   - Hidden file input accepts `.m4a,audio/mp4,audio/x-m4a`. The drop zone is a `button`-like focusable region (Enter/Space opens the picker).
   - Drag-over: border solid `--color-primary`, background `--color-primary-subtle`, text "Drop to upload".
   - Hover (non-drag): border `--color-primary`.

2. **File selected, client validation**
   - Drop zone is replaced by a **File card** (see below) with row-level status.
   - Instant client checks (extension, size). If duration can be read from file metadata by the browser, show it; otherwise show "Duration: checked after upload" (do not guess).
   - Client check fails: file card shows error state with a specific message (below) and buttons **Choose another file** (primary) and **Remove** (ghost). **Start analysis** is disabled.
   - Client check passes: file card shows a neutral "Ready to upload" and buttons **Start analysis** (primary) and **Remove** (ghost). Below the card, a settings summary line: "Active settings: Sensitivity Medium - 3 tone criteria - Commitments and follow-ups" with link "Review settings" (opens `/settings` in the same tab). This matches PRD 6.1 step 4.

3. **Uploading**
   - File card shows a determinate progress bar from **real upload bytes** (percentage and "12.4 MB of 31.8 MB"). Primary button replaced by **Cancel upload** (secondary). No other actions.
   - Cancel aborts the request, discards the partial upload, returns to the Idle state, and shows a neutral toast "Upload canceled".

4. **Uploaded, validating**
   - On upload completion the app navigates to the Processing screen (6C) for that call, with a success toast "Upload complete". Server-side validation runs as stage 1 there.
   - If the server rejects the file during validation, the Processing screen shows stage 1 failed (6C) with the specific reason and a "Upload a different file" action.

5. **Upload failed (network/server)**
   - File card error state: "Upload failed. Check your connection and try again." Buttons **Retry upload** (primary) and **Remove**. Retry re-sends the same file without re-selecting it. Partial progress is reset.

**File card (component spec):**
- Container `--color-surface-sunken`, 1px border, `--radius-md`, 16px padding.
- Left: 40px file icon tile (`file-audio`, 20px) on `--color-primary-subtle`.
- Middle: filename (14px/500, truncate with title tooltip, middle-ellipsis for long names), second line: size and duration in mono 13px separated by a middle dot ("31.8 MB - 12:48").
- Right: status chip (Ready, Uploading, Failed) and overflow actions as described.
- Error text sits under the metadata line in `--error-fg` with `octagon-x` 16px, `role="alert"`.

**Client validation messages (exact copy):**
| Condition | Message |
|---|---|
| Wrong extension / type | "This file isn't an .m4a recording. Convert it to .m4a and try again." |
| File too large | "This file is {size}, which is over the 50 MB limit. Upload a smaller recording." |
| Zero-byte file | "This file is empty. Choose a different recording." |
| More than one file dropped | "Upload one recording at a time. Only the first file was selected." (warning toast; first file kept) |
| Duration out of range (when readable) | "This recording is {duration}. Recordings must be between 0:10 and 30:00." |

Server-side checks (type signature, integrity, duration, silence) are reported on the Processing screen (see 6C and 6G for copy).

**"Before you upload" card (instructions):**
- Title "Before you upload".
- Checklist (icon `check` 16px in `--color-secondary`, neutral; not green):
  - "Use a consented or synthetic recording."
  - "File format: .m4a (single file)."
  - "Size up to 50 MB; length 10 seconds to 30 minutes."
  - "Best results: two speakers, clear audio, English."
  - "Audio and transcript are sent to third-party AI services for processing." with link "How your data is handled" (links to `/help#privacy`).

### 6C. Processing (`/calls/:id/processing`)

**Purpose:** truthfully show which pipeline stage is running and what happened. Covers M10, FR-E1 to FR-E5.

**Header:** H1 = call file name. Breadcrumb "Call History / {name}". Meta line: "Uploaded {datetime} - {size} - {duration if known}". Right side: overall status chip.

**Layout:** a centered card (max width 720px) containing a **vertical stepper** with 7 stages; below the card, a helper line. On Desktop the card is centered in the content area.

**Stages (fixed order, fixed labels):**
| # | Label | In-progress description | Notes |
|---|---|---|---|
| 1 | Audio validation | "Checking file type, size, length and audio integrity." | Fails here make no paid API calls (FR-U5) |
| 2 | Audio transcription | "Converting speech to text with timestamps." | |
| 3 | Speaker identification | "Separating speakers and identifying the sales rep." | May end as **Unavailable** (warning), not failure |
| 4 | Tone analysis | "Evaluating the sales rep's tone against your settings." | |
| 5 | Evidence extraction | "Verifying supporting quotes against the transcript." | Covers the verbatim-verification step (M6, FR-T8) |
| 6 | Action-item extraction | "Finding commitments and follow-ups." | |
| 7 | Analysis completion | "Saving results." | |

Implementation note: the backend must emit a status event per stage. If two stages run in one model call, the UI still shows both stages and advances them using real events (for example evidence verification begins after the model response). Never advance a stage without an event.

**Stage row anatomy:** 48px min height; left: 24px status icon in a connected vertical line (2px `--color-divider`; segment between two completed stages uses `--color-border-strong`); center: label (14px/600) and description or result text (13px, `--color-text-secondary`); right: elapsed time in mono for completed stages ("0:07") and live elapsed for the running stage (ticks from real timestamps).

**Stage states:**
| State | Icon | Label style | Description |
|---|---|---|---|
| Pending | Hollow circle 16px, `--color-border-strong` | `--color-text-tertiary` | "Waiting" |
| In progress | 20px spinner (2px stroke, `--color-primary`, 800ms linear). Reduced motion: static `loader` icon + text "In progress" | `--color-text-primary` | In-progress description above, live elapsed time |
| Completed | `circle-check` in `--success-fg` | `--color-text-primary` | Short real result: e.g., "Transcript ready - 142 segments", "Speakers identified - 2 speakers", "3 verified quotes", "4 action items found" |
| Failed | `octagon-x` in `--error-fg` | `--error-fg` 600 | Specific reason (see 6G copy) + stage-specific actions inline: **Retry** (primary, small) |
| Unavailable | `triangle-alert` in `--warning-fg` | `--color-text-primary` | e.g., "Speaker identification unavailable. The transcript will show no speaker labels." Processing continues only as defined in 6G.6 |
| Skipped/Blocked | Hollow circle with dash, `--color-text-tertiary` | `--color-text-tertiary` | "Not run because an earlier stage failed" |

**Rules (honesty):**
- **No percentage bar and no estimated completion** for processing (the only determinate bar in the product is the upload byte progress). A static line under the card may say "Most 5-minute calls finish in under 2 minutes." (target from PRD; caption style). It is never shown as a countdown.
- A stage shows Completed only after the server confirms it.
- The overall status chip reflects the real call status: Validating / Transcribing / Analyzing (in progress, `--color-primary-subtle`), Complete (`--success-*`), Failed (`--error-*`), Partial (`--warning-*`). Tone is **not** shown until analysis completes.
- Status updates arrive by polling or server-sent events; `aria-live="polite"` region announces stage changes ("Audio transcription completed. Speaker identification in progress.").
- Network loss while watching: Banner (warning) "We lost connection. Processing continues on the server. Reconnecting..." with a **Retry now** button; on reconnect, state refreshes from the server.

**Footer helper (in-progress):** "You can leave this page. Processing continues, and the call appears in Call History." Link button "Go to Call History".

**On completion:** the page shows a success banner (system success) "Analysis complete" with a primary button **View analysis** and auto-navigates after 1.5s unless the user has focus inside the stepper (then it does not auto-navigate). Toast "Analysis complete".

**On failure:** card header shows an error Banner summarizing the failed stage with actions:
- Transcription/analysis failure: **Retry {stage}** (primary), **Back to Call History** (secondary).
- Validation failure: **Upload a different file** (primary), **Back to Call History** (secondary).
- If transcription succeeded and analysis failed: also **View transcript** (secondary) which opens the Results screen in Partial state (6D.7).

### 6D. Call Analysis Results (`/calls/:id`)
The most important screen. The design principle: **verdict, then proof, then context.** Covers M4-M9, M13, FR-T1 to FR-T9, FR-A1 to FR-A6, FR-D1 to FR-D7.

**Header:** Breadcrumb "Call History / {call name}". H1 = call file name (editable not supported; no rename). Meta line: "Uploaded {date, time} - Duration {m:ss} - {n} segments". Right actions: **Export** (secondary button with dropdown: "Download JSON", "Download Markdown"), overflow menu (`ellipsis`): "Delete call" (opens destructive modal 7.8).

**Desktop/Laptop layout:**
```
[ Tone Overview card (12 cols, full width)                                      ]
[ Notice banners (role confidence, dropped evidence) as needed, 12 cols         ]
[ Left column (5 cols)                       ][ Right column (7 cols)           ]
[  Evidence panel                            ][  Transcript panel (sticky)      ]
[  Action Items panel                        ][                                 ]
[  Settings used for this analysis (collapsed)]                                  ]
```
- Right column (Transcript) is **sticky**: `position: sticky; top: 88px` (top bar 64px + 24px), height `calc(100vh - 112px)`, internal vertical scroll. Left column scrolls with the page.
- Laptop (1024-1439): same 5/7 split.
- Tablet and Mobile: see section 8 (tabbed layout).

#### D.1 Tone Overview Card
Tone-tinted container: `--tone-red-bg` + 1px `--tone-red-border` for RED; `--tone-green-bg` + 1px `--tone-green-border` for GREEN; `--tone-none-bg` for not analyzed. `--radius-lg`, padding 32px. 3-part layout (Desktop: 3 columns 4/5/3 of the 12-col inner grid; Laptop same; stack on Tablet/Mobile):

**Part 1: Verdict block**
- Overline "SALES REP TONE".
- Row: 48px shield icon (`shield-alert` for RED / `shield-check` for GREEN) in tone `*-fg`, then the **verdict pill**: solid fill (`--tone-*-solid`), text `--tone-*-on-solid`, `--text-verdict` 32/40, padding 8px 20px, `--radius-md`. Text: "RED" or "GREEN".
- Below pill (16px/24px, `--tone-*-fg` 600): RED: "Negative tone detected"; GREEN: "No negative tone detected".
- Caption (13px `--color-text-secondary`): "Based on the sales rep's speech only."

**Part 2: Explanation (AI interpretation)**
- Overline with `sparkles` icon: "AI INTERPRETATION" (`--color-primary`).
- Explanation paragraph (`--text-body-lg`, max 4 lines then "Show more" toggle). For GREEN, copy is the model's brief explanation, which must not claim positive traits it cannot support (FR-T7). Prepend nothing; the text is rendered as returned and sanitized.
- Below: link-style button "Jump to evidence" (RED only), scrolls to the Evidence panel.

**Part 3: Facts**
| Fact | Display |
|---|---|
| Supporting evidence | "{n} verified quote(s)" with `quote` icon 16px. For GREEN with 0: "No evidence of negative tone found" (text only) |
| Confidence | See below |
| Sensitivity used | "Sensitivity: {Low/Medium/High}" chip (secondary) |

**Confidence indicator (shown with every verdict; M7):**
- Component: 3-segment meter (each segment 24x6px, `--radius-full`) plus a label "Confidence: High / Medium / Low". Filled segments use `--color-text-secondary` (neutral, **not** tone colors) so confidence is not conflated with RED/GREEN. Label always present (not color/length alone).
- Next to it, a "Why?" ghost icon button (`info`, 16px) opening a popover that lists the **actual factors** behind the level: (a) number of verified evidence quotes, (b) speaker-role confidence (from the role inference step), (c) amount of rep speech analyzed (seconds), (d) whether any evidence was dropped on verification. Example: "Medium: Only one verified quote. Speaker roles were inferred with high confidence. 2:14 of rep speech analyzed."
- **Method note (required for honesty):** confidence is a rule-based level derived from those factors, not a statistical probability, and the popover says so: "This level is derived from the factors above. It is not a probability."
- If the backend cannot supply the factors, the indicator is hidden and replaced by the caption "Confidence not available for this analysis." Never display a numeric percentage.
- When the PRD limited-evidence condition applies (very short rep speech or uncertain attribution), show a warning Banner directly below the card: "Limited evidence. {Specific reason}. Treat this result with caution."

#### D.2 Notice Banners (conditionally rendered under the Tone Overview)
| Condition | Banner |
|---|---|
| Role confidence low (FR-S3, FR-S4) | Warning: "We aren't certain which speaker is the sales rep. Tone analysis depends on this." Actions: **Review speaker roles** (opens Swap Roles modal, 7.8) |
| Evidence dropped by verification (M6) | Warning: "{n} quote(s) couldn't be verified in the transcript and were excluded from the evidence." Action: "Learn more" (links to `/help#evidence`) |
| Settings differ from current saved settings | Info (neutral): "This analysis used earlier settings. Your current settings are different and apply only to new analyses." Action: **View settings** |
| Speaker identification unavailable | Warning: "Speaker labels are unavailable for this call" (see 6G.6) |

#### D.3 Evidence Panel
Panel header: title "Evidence" with count chip (e.g., "3"). Subtitle (13px, `--color-text-secondary`): "Quotes from the sales rep that support the verdict. Verified against the transcript."

Body: vertical list of **Evidence Cards** (7.13), 12px gap, ordered by timestamp ascending, each numbered E1, E2... Card contents:
1. Header row: Evidence ID chip (E1), criterion chip (e.g., "Dismissive", neutral chip), timestamp link (mono, `play` is **not** used because audio playback is V2; use a `corner-down-right` icon and the label "Go to 03:42").
2. **From the transcript**: overline "FROM THE TRANSCRIPT" with `quote` icon; quote block (verbatim text in quotes, 15px, left border 3px `--color-border-strong`, 12px left padding); speaker label "Sales Rep" + timestamp under it.
3. **AI interpretation**: overline "AI INTERPRETATION" with `sparkles`; tinted block (`--color-primary-subtle`, `--radius-sm`, 12px padding) with the "Why this supports the classification" explanation (14px).
4. Footer: tone-colored marker only on RED verdicts: a 4px left edge on the whole card in `--tone-red-solid`. On GREEN verdicts (no evidence), the panel shows the empty state below.

Interaction: clicking the card, the quote, or "Go to {time}" scrolls the Transcript panel to the segment, applies the linked highlight (7.12) for 2.5s (persistent while the card has focus), and moves visible focus to the segment (programmatic, `tabindex=-1`), announcing "Showing transcript at 03:42". Pressing Escape returns focus to the card.

**Evidence panel states:**
| State | Spec |
|---|---|
| RED with evidence | List of evidence cards |
| GREEN | Empty state (compact, no illustration): icon `shield-check` in `--tone-green-fg` 24px; text "No evidence of negative tone was found under your current criteria." Secondary text "If this seems wrong, review your tone criteria and sensitivity in Analysis Settings." (link) |
| Insufficient evidence | Compact warning block "Not enough sales rep speech to find evidence." |
| Loading | 3 skeleton evidence cards |
| Error (evidence fetch) | Inline error banner with Retry |

#### D.4 Transcript Panel
Panel header: title "Transcript"; right side tools: **Search input** (compact, 280px, `search` icon, placeholder "Search transcript", clear button `x` when non-empty), match counter ("3 of 12", `aria-live="polite"`), prev/next buttons (`chevron-up`, `chevron-down`, 32x32). Enter = next, Shift+Enter = previous, Escape clears.
Sub-header row (sticky within the panel): speaker legend: two chips: "Sales Rep" (rep bar/color sample) and "Customer" (customer bar/color sample), each with a 3px bar swatch; when roles are uncertain, a text link "Swap roles" appears at the right (opens modal 7.8).

Body: scrolling list of **Transcript Segments** (7.12). Each segment: timestamp column (56px, mono 12px), content column with speaker label and text. Rep and customer segments are visually distinct by: 3px left bar color/style, background tint, and **label text** (and rep segments are not indented; customer segments have a 16px left inset) so the distinction survives grayscale and color-blindness.

- Search matches: highlighted with `--highlight-search`; current match `--highlight-search-current` with 2px outline; scrolled into view with `scroll-margin`.
- Evidence highlighting: the exact verified quote span inside the segment gets a 2px underline `--highlight-evidence-underline` (RED verdict only) plus a small marker chip "E1" at the segment's right edge linking back to the evidence card (clicking focuses the card).
- Action-item highlighting: the supporting quote span for an action item gets a 2px dotted underline in `--color-primary` and a marker chip "A1" at the segment's right edge (secondary style), linking to the action item card.
- If a segment is both evidence and action-item support, both markers show.
- Long transcripts: virtualized list is permitted, but all text must remain searchable; the segment list is `role="list"`.
- Footer inside the panel: caption "Transcript generated automatically and may contain errors." (`--color-text-tertiary`).

**States:**
| State | Spec |
|---|---|
| Loaded | As above |
| No speaker labels | Segments rendered with "Speaker unknown" label and dashed unknown bar; warning banner in the panel header (6G.6) |
| Search with no results | Inline text under the search: "No matches for "{query}"." (also announced). The list is unchanged |
| Loading | 8 skeleton segments |
| Error | Panel-level error banner with **Try again** |

#### D.5 Action Items Panel
Panel header: title "Action items" with count chip. Subtitle: "Commitments and follow-ups stated in the call. Owners and deadlines appear only when explicitly said."

Body: list of **Action Item Cards** (7.14), ordered by timestamp. Each card:
1. Task text (14px/600): the commitment, as the model summarized it (AI-generated; labeled by the card's AI tag).
2. Meta row with two labeled fields:
   - **Owner:** value text, or "Not specified" (`--color-text-tertiary`, italic not used, with `circle-dashed` icon 16px).
   - **Deadline:** value text exactly as stated (e.g., "by Friday"), or "Not specified" (same style).
3. **From the transcript**: quote block (verbatim) with speaker and timestamp, and "Go to 04:10" link (same interaction as evidence).
4. Footer: the type chip ("Commitment" or "Follow-up", from settings categories).
- No checkboxes, no completion states, no editing (V2 and out of scope).

**States:** populated; empty ("No action items identified in this call." plus secondary "Action items are only listed when a commitment or follow-up is clearly stated. You can adjust what counts in Analysis Settings." with link); loading (3 skeleton cards); error (inline banner with Retry).

#### D.6 Settings Used for This Analysis (M13)
A collapsible panel (`<details>` pattern, collapsed by default) at the bottom of the left column. Title "Settings used for this analysis". Collapsed row shows a summary line: "Sensitivity Medium - 3 tone criteria - Commitments, follow-ups" and a chip "Settings v{n}" when available.
Expanded: read-only definition list of the stored snapshot (criteria enabled/disabled with custom criteria text, sensitivity with its threshold description, action-item definition, owner rule, deadline rule, custom guidance text). Footer: if the snapshot differs from the current saved settings, a gold chip "Differs from current settings" and a link "View current settings". This panel is **read-only** and visually labeled "Read only". No "re-analyze with new settings" action exists in the MVP (V2).

#### D.7 Partial Analysis State
Occurs when transcription succeeded but tone or action-item analysis failed (FR-E5).
- The Tone Overview card is replaced by a neutral card (`--tone-none-bg`): `shield` outline icon, title "Tone analysis unavailable", text "The transcript is ready, but the analysis didn't complete." Actions: **Retry analysis** (primary), and a Banner (error) with the specific reason.
- Evidence panel: neutral empty block "Evidence unavailable until tone analysis completes."
- Action items panel: if action-item extraction failed, same pattern; if only tone failed, action items still display.
- Transcript panel: fully functional.
- Export: available (JSON/Markdown note which sections are missing).

#### D.8 Export Behavior (M14)
- Export dropdown items: "Download JSON" (`file-json`), "Download Markdown" (`file-text`).
- Loading: button shows spinner and "Preparing..." and is disabled until the file begins downloading.
- Success: toast (success) "Export downloaded".
- Error: toast (error) "Export failed. Try again." with **Retry** action.

### 6E. Call History (`/calls`)

**Header:** H1 "Call History". Description: "All uploaded calls and their analysis status." Action: **Upload call** primary button.

**Toolbar (above table, one row on Laptop/Desktop, wraps on smaller):**
| Control | Spec |
|---|---|
| Search | Input 320px, `search` icon, placeholder "Search by call name". Debounced 300ms. Clear button |
| Tone filter | Dropdown (select) label "Tone": All tones, RED, GREEN, Not analyzed |
| Status filter | Dropdown label "Status": All statuses, In progress, Complete, Partial, Failed |
| Sort | Dropdown label "Sort by": Newest first (default), Oldest first |
| Clear filters | Ghost button, visible only when any filter/search is active |
Active filter count is announced; selected filters also appear as removable chips under the toolbar (e.g., "Tone: RED  x").

**Table columns (Laptop/Desktop):**
| Column | Width | Content |
|---|---|---|
| Call name | flexible (min 240px) | File name (14px/500, link style on hover) with secondary line: duration and size (mono 13px, `--color-text-tertiary`) when known |
| Upload date | 160px | "Nov 23, 2026, 1:33 AM" (local time zone) |
| Analysis status | 160px | Status chip (7.5) |
| Tone | 140px | Tone badge (7.4); "Not analyzed" neutral badge when no result |
| Action items | 100px | Count (tabular) or an en dash when unavailable |
| Actions | 168px, right-aligned | **View analysis** (secondary small button; for in-progress calls the label is **View progress**, for failed calls **View details**), overflow `ellipsis` menu: "Delete call" |

Sorting by date only (PRD does not require sorting by other columns). The "Upload date" header shows a sort icon reflecting the dropdown choice and is also clickable to toggle.

Row behavior: hover `--color-surface-sunken`; the whole row is not a link (to preserve text selection); the View button and call name link navigate. Row focus: keyboard focus lands on the call name link and the buttons.

Pagination: 20 rows per page; footer shows "Showing 1-20 of 57" and Previous/Next buttons (and page numbers on Desktop). State (search, filters, sort, page) is reflected in the URL query string.

**States:**
| State | Spec |
|---|---|
| Loading | Toolbar visible; 8 skeleton rows |
| No calls at all | Empty state 6G.1 (replaces table and toolbar) |
| Empty search/filter results | Empty state 6G.10 inside the table area, toolbar remains |
| Error | Banner (error) above an empty table region: "We couldn't load your calls." **Try again** |
| In-progress rows | Status chip with spinner; rows refresh by polling every 5 seconds while any call is in progress |

**Delete flow:** overflow > Delete call > confirm modal (7.8): "Delete this call? This permanently removes the audio, transcript and analysis." Buttons **Cancel**, **Delete call** (destructive). Success toast "Call deleted". (FR-D6)

### 6F. Analysis Settings (`/settings`)

**Purpose:** let managers control analysis without code changes. Covers M12, M13, FR-C1 to FR-C6.

**Header:** H1 "Analysis settings". Description: "Control how tone is evaluated and what counts as an action item."
**Status strip under the header (always visible):** Info banner (neutral): "Saved settings apply to calls you analyze from now on. Past analyses keep the settings they were analyzed with." Right side: "Last saved {relative time, e.g. 'Nov 22, 4:10 PM'}" and a chip "Settings v{n}" (omit if versioning is not available).

**Layout:** single column form, max width 880px on Desktop, left aligned (not centered) with a right column (4 cols) "Fixed safeguards" card on Desktop/Laptop; the safeguards card stacks below on Tablet/Mobile. The form has two sections, each a standard card with a title and description.

**Section 1: Tone evaluation**

*1.1 Negative tone criteria*
- Description: "Select the behaviors that count as negative tone for the sales rep. Customer behavior is never evaluated."
- List of 3 default criteria, each a row with a Switch (7.2), a label, and a one-line description:
  | Criterion | Description | Default |
  |---|---|---|
  | Rude communication | "Insults, sarcasm aimed at the customer, mocking, or disrespectful wording." | On |
  | Hostile communication | "Aggressive, threatening, or confrontational language; raised-voice wording such as shouting in capitals when present in the transcript." | On |
  | Dismissive communication | "Brushing off concerns, interrupting to shut down a topic, or refusing to engage with the customer's questions." | On |
- **Custom criteria:** "Add your own" input (single line, max 140 characters, placeholder "e.g., Pressures the customer to decide immediately") with **Add** button. Added criteria appear as rows with a Switch and a **Remove** icon button. Maximum 5 custom criteria. Duplicate or empty text shows inline validation.
- Validation: at least one criterion must be enabled to save. Message: "Turn on at least one criterion so tone can be evaluated."

*1.2 Sensitivity*
- Label "Sensitivity" with a 3-option **segmented control**: Low, Medium (default), High.
- Directly beneath, a description updates with selection (this text maps to FR-T5; it is rendered as live text, `aria-live="polite"`):
  | Level | Helper text |
  |---|---|
  | Low | "Flags RED only for a clear, severe instance, such as hostility or insults." |
  | Medium | "Flags RED for one clear instance or repeated milder instances." |
  | High | "Flags RED for any identifiable instance of an enabled criterion." |
- Caption: "Higher sensitivity flags more calls RED, including some that a reviewer may consider acceptable."

*1.3 Custom guidance (optional)*
- Textarea, 4 rows, max 500 characters with live counter ("212 / 500"), label "Additional guidance for tone evaluation (optional)", placeholder "e.g., Brisk, direct language is acceptable on this team." Helper: "This text is added to the instructions used for analysis. Don't include customer data."

**Section 2: Action-item configuration**

*2.1 What counts as an action item* (switches, each with a description)
| Option | Description | Default |
|---|---|---|
| Commitments | "Something a speaker explicitly promises to do. For example, 'I'll send the quote.'" | On |
| Follow-ups | "A next step or follow-up explicitly agreed on or scheduled." | On |
| Information promised | "A promise to share specific information or documents." | On |
| Tasks assigned to the customer | "Something the customer agrees or is asked to do." | Off |
| Include tentative statements | "Count hedged statements such as 'maybe I could...' as action items." | Off |
At least one of the first four must be on (validation message: "Turn on at least one action-item type.").

*2.2 Owner rules*
- Radio group (7.2): 
  - "Explicit only": "Show an owner only when a name or role is stated for the task." 
  - "Explicit or the committing speaker (default)": "Also show the person who said 'I will...', labeled by their role (Sales Rep or Customer)."
- Footnote: "If no owner can be supported by the transcript, the app shows 'Not specified'."

*2.3 Deadline rules*
- Switch: "Capture relative deadlines as stated" (default On). Helper: "Shows phrases like 'by Friday' exactly as said. Dates are never converted or guessed."
- Footnote: "If no deadline is mentioned, the app shows 'Not specified'."

*2.4 Custom guidance (optional)*
- Textarea with the same spec as 1.3, label "Additional guidance for action items (optional)", max 500.

**Fixed safeguards card (read-only, right column):**
- Title "Always on" with `lock` icon.
- Bullets (neutral icons): "Every quote must appear verbatim in the transcript." / "Only the sales rep is evaluated for tone." / "Owners and deadlines are never guessed." / "Failed analyses are never replaced with placeholder results."
- Caption "These safeguards can't be changed."

**Save bar (sticky bottom of the form card area):** appears whenever there are unsaved changes (also visible disabled-but-present otherwise?). Specification: always rendered; sticky at the bottom of the viewport region (`position: sticky; bottom: 0`), `--color-surface`, top border, `--shadow-sm`, 16px padding.
- Left text: "Unsaved changes" (with `circle-dot` in `--warning-fg` and text) when dirty, otherwise "All changes saved" (`circle-check` in `--success-fg`).
- Right: **Reset to defaults** (secondary), **Discard changes** (ghost, only when dirty), **Save settings** (primary; disabled when not dirty or when invalid; loading state while saving).

**Validation feedback:**
- Inline field-level errors on blur and on submit using Input error state (7.2); form-level summary Banner (error) at the top of the form on failed submit listing issues as links to the fields, focus moves to the banner heading (`tabindex=-1`).
- Character-limit overflow blocks input beyond max (counter turns `--error-fg` at the limit).

**Confirmation feedback:**
- On save success: toast (success) "Settings saved. They'll apply to analyses you start from now on." The status strip's "Last saved" updates; the save bar shows "All changes saved".
- On save failure: toast (error) "Couldn't save settings. Your changes are still here. Try again." and the save button returns to enabled.
- **Reset to defaults** opens a confirm modal: title "Reset settings to defaults?", body "This replaces your current settings with the defaults. Past analyses are not affected." Buttons **Cancel**, **Reset settings** (primary, not destructive). After confirmation the form updates and a toast confirms "Settings reset to defaults" (settings are saved immediately on reset; the strip updates).
- Navigating away with unsaved changes: browser `beforeunload` prompt plus an in-app confirm modal for in-app navigation: "Leave without saving?" **Stay** (primary), **Leave** (secondary).

**Saved vs. used-in-past distinction:** (1) the status strip text above; (2) each result shows its own read-only "Settings used for this analysis" panel (6D.6) with the "Differs from current settings" chip; (3) Settings page never edits historical snapshots.

**States:** loading (skeleton form); load error (Banner with Retry; form not shown, to avoid saving defaults over real settings); saving; saved.

### 6G. Empty, Error and Loading States

**Pattern for full-region states (EmptyState component):** centered block, max width 480px, 24px icon in a 72px circle (`--color-secondary-subtle`, icon `--color-secondary`; for error states `--error-bg` and `--error-fg`; for warning states `--warning-bg` and `--warning-fg`), title (`--text-h3`), body (`--text-body`, `--color-text-secondary`, max 2 sentences), primary action, optional secondary action. No illustrations. Inline (within a panel) variants use the same copy in a Banner (7.10).

| # | State | Where shown | Title | Body | Actions |
|---|---|---|---|---|---|
| 6G.1 | No calls uploaded | Dashboard, Call History | "No calls yet" | "Upload a recording to see its transcript, tone result and action items." | **Upload call** (primary) |
| 6G.2 | No analysis available | Results page when call exists but never analyzed (e.g., status Uploaded) | "No analysis yet" | "This call hasn't been analyzed. Check its progress or start again." | **View progress** (primary), **Back to Call History** |
| 6G.3 | Invalid file format | Upload screen (file card), Processing stage 1 if server detects a mismatch | "This isn't a valid .m4a file" | "The file extension or contents don't match the .m4a format. Convert the recording to .m4a and try again." | **Choose another file** (primary), **How to prepare a recording** (link to `/help#upload`) |
| 6G.4 | Corrupted audio | Processing stage 1 failed | "We couldn't read this audio" | "The file appears to be damaged or incomplete. No transcription was attempted. Re-export the recording and upload it again." | **Upload a different file** (primary), **Back to Call History** |
| 6G.5 | Transcription failure | Processing stage 2 failed; Results (Partial) | "Transcription failed" | "The transcription service couldn't process this recording ({specific reason if provided}). Nothing was generated in its place." | **Retry transcription** (primary), **Back to Call History** |
| 6G.6 | Speaker identification unavailable | Processing stage 3 (warning), Results banner, Transcript header | "Speaker labels unavailable" | "We couldn't separate the speakers in this call, so the transcript has no speaker labels. Tone is not evaluated unless you identify which lines are the sales rep's." | **Assign sales rep lines** (primary; opens the Swap/Assign Roles modal in "assign" mode, where the user marks which speaker is the rep, available only if diarization produced >= 2 speakers), **Continue without tone result** (secondary; completes analysis with Tone "Not analyzed", action items still extracted). If diarization produced a single undifferentiated speaker, the primary action is not available and the tone card shows "Tone analysis unavailable: speaker attribution is required." |
| 6G.7 | AI service unavailable | Processing stages 4-6; Results (Partial) | "Analysis service unavailable" | "We couldn't reach the AI analysis service. The transcript is saved. No tone result or action items were generated." | **Retry analysis** (primary), **View transcript** (secondary) |
| 6G.8 | Partial analysis | Results page | "Part of the analysis didn't complete" | "{Tone analysis | Action items} couldn't be completed. Everything else on this page is accurate." | **Retry {section}** (primary), **Dismiss** (ghost, hides the banner only, the section keeps its unavailable state) |
| 6G.9 | Network failure | Any page with failed fetch; Upload | "You appear to be offline" / "We couldn't reach the server" | "Check your connection. Your settings and calls are safe." (Upload: "Your file wasn't uploaded.") | **Try again** (primary) |
| 6G.10 | Empty search results | Call History; Transcript search | History: "No calls match your search" / Transcript: inline "No matches for "{query}"." | History body: "Try a different name or clear your filters." | **Clear filters** (secondary) |
| 6G.11 | Successful upload | Toast + navigation to Processing | Toast: "Upload complete" | Description: "{filename} is being processed." | Toast action: none (page navigates) |
| 6G.12 | Successful analysis | Toast + Processing completion banner | "Analysis complete" | "{filename}: tone result, evidence and action items are ready." | **View analysis** (primary in banner; toast action link "View") |

**Loading states (global):**
| Context | Pattern |
|---|---|
| Page/region load | Skeleton matching layout; `aria-busy="true"`; no spinner |
| Button action | Button loading state (spinner replaces icon, label stays, button disabled) |
| Processing | Stepper (6C) |
| Table refresh/poll | No visual flicker; update rows in place; spinner only in in-progress status chips |
| Long action (>400ms) | Show loading; actions under 400ms do not show a spinner (avoid flashing) |

---

## 7. Component Specifications

Every interactive component has these states: **Default, Hover, Focus (focus-visible), Active (pressed), Disabled, Loading, Error** (where applicable; "n/a" noted). Focus is always the 2px `--color-focus-ring` ring with 2px offset (outer shadow), never removed. Disabled elements use `--color-text-disabled`, 50% opacity on fills, `cursor: not-allowed`, `aria-disabled`/`disabled`. Hit targets >= 24x24 (WCAG 2.5.8), buttons and controls 40px high by default (32px small, 48px large).

### 7.1 Buttons
Sizes: Small 32px (padding 0 12px, 13px text), Medium 40px (padding 0 16px, 14px text, default), Large 48px (padding 0 20px, 16px). Radius `--radius-sm`. Font weight 600. Icon 20px (16px in small), 8px gap to label. Icon-only buttons are square (same height) with required `aria-label`.

| Variant | Default | Hover | Active | Disabled | Loading | Error |
|---|---|---|---|---|---|---|
| **Primary** | bg `--color-primary`, text `--color-on-primary` | bg `--color-primary-hover` | bg `--color-primary-active` | bg `--color-border`, text `--color-text-disabled` | Spinner (16px, `currentColor`) replaces leading icon, label stays, `aria-busy`, pointer events off | n/a (errors shown by Banner/Toast) |
| **Secondary** | bg `--color-surface`, 1px border `--color-border-strong`, text `--color-text-primary`, `--shadow-sm` | bg `--color-secondary-subtle` | bg `--color-border` | text `--color-text-disabled`, border `--color-border`, no shadow | As primary | n/a |
| **Ghost** | transparent, text `--color-primary` (or `--color-text-secondary` for icon buttons) | bg `--color-secondary-subtle` | bg `--color-border` | text `--color-text-disabled` | As primary | n/a |
| **Destructive** | bg `--error-solid`, text `--error-on-solid` | 8% darker (light) / lighter (dark): use `color-mix(in srgb, var(--error-solid) 88%, black)` in light and `color-mix(in srgb, var(--error-solid) 88%, white)` in dark | 16% shift | As primary disabled | As primary | n/a |
| **Link button** | text `--color-primary`, underline on hover, no padding | underline | text `--color-primary-active` | disabled text | n/a | n/a |

Rules: one Primary per view region. Never use the tone colors for buttons. Destructive buttons only inside confirmation modals or Delete menu items.

### 7.2 Inputs and Form Controls

**Text input and textarea**
| State | Spec |
|---|---|
| Default | Height 40px (textarea min 96px), padding 0 12px (textarea 8px 12px), bg `--color-surface`, 1px border `--color-border-strong`, `--radius-sm`, 14px text, placeholder `--color-text-tertiary` |
| Hover | Border `--color-text-tertiary` |
| Focus | Border `--color-primary`, ring 2px `--color-focus-ring` with 0 offset (plus 1px inner) |
| Active (typing) | Same as focus |
| Disabled | bg `--color-surface-sunken`, text `--color-text-disabled`, border `--color-border` |
| Loading | Trailing 16px spinner (e.g., debounced search); input stays enabled |
| Error | Border `--error-fg`, trailing `octagon-x` 16px, helper text below in `--error-fg` (12px/500) with `role="alert"` on submit; `aria-invalid="true"`, `aria-describedby` points to the message |
Label above (14px/500, `--color-text-primary`), helper text below (12px, `--color-text-tertiary`). Required fields are marked in the label text "(required)" not just an asterisk.

**Dropdown / Select** (used for filters, sort, theme menu)
| State | Spec |
|---|---|
| Default | Same as input; trailing `chevron-down` 16px. Placeholder or value text 14px |
| Hover | As input hover |
| Focus | As input focus. Opening: Enter/Space/Arrow Down |
| Active (open) | Menu popover `--color-surface-elevated`, 1px border, `--shadow-md`, `--radius-md`, 4px padding, max height 320px scroll. Option rows 36px, hover `--color-secondary-subtle`, selected row has `check` icon (16px, `--color-primary`) and weight 600; keyboard: arrows/Home/End/type-ahead/Escape |
| Disabled | As input disabled |
| Loading | Menu shows a single "Loading..." row with spinner |
| Error | As input error |
Use the native `<select>` or an ARIA listbox pattern; behavior must be keyboard-complete either way.

**Switch (toggle)**
| State | Spec |
|---|---|
| Default Off | Track 40x24, `--color-border-strong`, thumb 18px white (dark: `--color-text-secondary`) |
| Default On | Track `--color-primary`, thumb `--color-on-primary`; a `check` glyph (12px) inside the thumb so state is not color-only |
| Hover | Track one step darker |
| Focus | 2px ring on the track |
| Active | Thumb widens to 22px |
| Disabled | 50% opacity |
| Loading | n/a |
| Error | n/a (validation error shown at group level) |
Always paired with a visible label; `role="switch"`, `aria-checked`.

**Radio group** and **Checkbox**: 20px control, 1.5px border `--color-border-strong`, selected fill `--color-primary` with white dot/check, same hover/focus/disabled pattern; error: border `--error-fg` and group message.

**Segmented control** (Low/Medium/High; Chart/Table): container `--color-surface-sunken`, 1px border, `--radius-sm`, 4px inner padding; segments 32px high. Default segment transparent text `--color-text-secondary` 500. Hover bg `--color-secondary-subtle`. Selected: bg `--color-surface`, text `--color-primary` 600, 1px `--color-primary-border`, `--shadow-sm`. Focus ring. Disabled 50%. Implemented as `role="radiogroup"` with arrow-key navigation.

**File drop zone**: see 6B (Default/Hover/Drag-over/Focus/Disabled while uploading/Error shows banner below).

**Search input**: Text input with leading `search` icon, trailing clear `x` (when non-empty), same states.

### 7.3 Cards
Standard card: `--color-surface`, 1px `--color-border`, `--radius-md`, no shadow.
| State | Spec |
|---|---|
| Default | As above |
| Hover | Only if clickable (KPI cards, mobile history cards): border `--color-border-strong` |
| Focus | Clickable cards: ring on card |
| Active | Clickable: bg `--color-surface-sunken` |
| Disabled | n/a (use skeleton or hide) |
| Loading | Skeleton: header bar 40% width 16px high, body lines at 100/90/70% width, 12px high, `--color-surface-sunken`, `--radius-xs`, shimmer |
| Error | Replace body with Banner (error) + Retry; card border stays default |

### 7.4 Tone Badges (RED / GREEN / Not analyzed)
Reserved component for tone only. Height 28px (Small 24px), padding 0 12px, `--radius-full`, 13px/600, icon 16px + 6px gap + text.
| Variant | Spec |
|---|---|
| RED (solid, default for tables and headers) | bg `--tone-red-solid`, text/icon `--tone-red-on-solid`, icon `shield-alert`, text "RED" |
| GREEN (solid) | bg `--tone-green-solid`, text/icon `--tone-green-on-solid`, icon `shield-check`, text "GREEN" |
| Not analyzed | bg `--tone-none-bg`, 1px border `--tone-none-border`, text `--color-text-secondary`, icon `shield` (outline), text "Not analyzed" |
| Tinted variant (inside tone-tinted cards) | bg `--tone-*-bg`, 1px `--tone-*-border`, text `--tone-*-fg` (same icon/text) |
States: Default as above. Hover/Active: none when static (not interactive). When used as a filter chip (clickable): Hover darkens/lightens fill 8%; Focus ring; Active as hover; Disabled 50% opacity; Loading: n/a; Error: n/a.
Accessibility: text is always present, `aria-label` "Tone: RED, negative sales rep tone detected" (tables use the shorter label "Tone: RED").

### 7.5 Status Indicators (processing status chips)
Chip: height 24px, padding 0 10px, `--radius-full`, 12px/600, 14px icon + 6px gap. Not interactive.
| Status | Colors | Icon |
|---|---|---|
| Uploaded | `--color-secondary-subtle` bg, `--color-text-secondary` text | `circle-dashed` |
| Validating / Transcribing / Analyzing (In progress) | `--color-primary-subtle` bg, `--color-primary` text, 1px `--color-primary-border` | Spinner 14px (static `loader` under reduced motion). The text names the specific stage ("Transcribing") |
| Complete | `--success-bg`, `--success-fg`, 1px `--success-border` | `circle-check` |
| Partial | `--warning-bg`, `--warning-fg`, border | `triangle-alert` |
| Failed | `--error-bg`, `--error-fg`, border | `octagon-x` |
Note: "Complete" is a processing status in cyan; it is unrelated to GREEN tone. They never appear styled alike.
Loading state: spinner shown only for In progress. Disabled/Hover/Focus/Active: not applicable (static). Error: the Failed variant.

### 7.6 Progress Indicators
| Type | Spec |
|---|---|
| Determinate bar (upload only) | Track 8px high `--color-border`, fill `--color-primary`, `--radius-full`, width = real bytes percent; label right "42%"; `role="progressbar"` with `aria-valuenow/min/max` and `aria-label="Upload progress"`. Error: fill `--error-fg`, stops. Disabled: n/a |
| Spinner | 20px (16px in buttons, 14px in chips), 2px stroke, 800ms linear rotation, `currentColor`, `role="status"` with visually hidden text when standalone |
| Stage stepper | See 6C |
| Skeleton | See 7.3 |
There is no indeterminate "fake" progress bar anywhere.

### 7.7 Tables
- Container card with horizontal scroll fallback (`overflow-x: auto`) and sticky header.
- Header row: 44px, `--color-surface-sunken`, 12px/600 `--color-text-secondary` uppercase letter-spacing 0.04em, bottom border `--color-border`. Sortable header: button with `arrow-up-down` 14px (`arrow-up` / `arrow-down` when sorted), `aria-sort`.
- Body rows: 56px (comfortable) / 44px (compact, used on Dashboard), 1px `--color-divider` separators, 14px text, vertical-align middle.
- Row states: Default; **Hover** bg `--color-surface-sunken`; **Focus-within** row gets a 2px inset ring on the focused control only; **Selected/Active** (not used in MVP); **Disabled** n/a; **Loading** skeleton rows; **Error** table body replaced by Banner row spanning columns.
- Numeric columns right-aligned with tabular numerals. Text truncates with ellipsis and `title` tooltip.
- Footer: pagination (Previous, Next, "Showing x-y of n").
- Semantics: real `<table>` with `<caption>` (visually hidden), `scope="col"`.
- Mobile < 640px: transforms to a stacked card list (see 8).

### 7.8 Modals (and Drawer)
- Overlay `--color-scrim`. Dialog `--color-surface-elevated`, `--radius-lg`, `--shadow-lg`, 1px border. Width 480px (confirm) / 560px (form); max width calc(100vw - 32px). Padding 24px; title `--text-h4`; body `--text-body`; footer right-aligned buttons with 12px gap (Cancel left of primary). On Mobile, the footer buttons are full width stacked with primary on top.
- Behavior: `role="dialog"` (`alertdialog` for destructive), `aria-modal`, labelled by the title; focus moves to the first focusable (for destructive: the safe action **Cancel**), focus is trapped, Escape closes (unless action is in-flight), scrim click closes (not for destructive or in-flight), focus returns to the trigger.
| State | Spec |
|---|---|
| Default | As above |
| Hover/Focus/Active/Disabled | Apply to the inner buttons per 7.1 |
| Loading | The confirming button shows loading; Cancel and close are disabled; modal cannot be dismissed |
| Error | Banner (error) inside the modal body, above the footer, with the failure reason; buttons re-enable |

Defined modals:
1. **Delete call** (destructive): title "Delete this call?", body "This permanently removes the audio, transcript and analysis for {filename}. This can't be undone." Buttons **Cancel**, **Delete call** (destructive).
2. **Reset settings** (non-destructive primary): see 6F.
3. **Leave without saving?**: see 6F.
4. **Review speaker roles / Swap roles**: title "Review speaker roles". Body: two-row radio list: "Speaker A: {first 2 lines preview}", "Speaker B: {first 2 lines preview}" with a select per speaker for role (Sales Rep / Customer). Helper: "Applying this re-runs tone and action-item analysis on the saved transcript using your current settings. The transcript isn't re-transcribed." Buttons **Cancel**, **Apply and re-run** (primary). Success: processing stages 3-7 re-run (the Processing screen shows them), toast "Roles updated. Re-running analysis."
   (Design note DD-06: the PRD (FR-S4) permits re-running after a role swap; this modal states plainly that current settings are used, so the user is never surprised.)
5. **Drawer** (mobile nav): see 5.4.

### 7.9 Toast Notifications
- Container: top-right on Laptop/Desktop (24px from edges), top-center on Tablet, bottom-center above content on Mobile (16px). Max 3 visible stacked with 12px gap; the oldest is dismissed first.
- Toast: width 360px (max calc(100vw - 32px)), `--color-surface-elevated`, 1px border, `--shadow-md`, `--radius-md`, padding 12px 16px; 20px status icon (system icon family), title 14px/600, optional description 13px `--color-text-secondary`, optional single action link, close `x` button (24x24).
- Left 4px accent bar in the variant's `*-fg`. Variants: Success (cyan), Error (vermilion), Warning (gold), Info (primary), Neutral (secondary, no icon accent).
- Behavior: Success/Info/Neutral auto-dismiss after 5s; Warning after 8s; **Error toasts persist until dismissed**. Hover or keyboard focus pauses the timer. `role="status"` (Success/Info/Neutral) or `role="alert"` (Error/Warning) in an `aria-live` container.
| State | Spec |
|---|---|
| Default | As above |
| Hover | Timer paused; close button visible background `--color-secondary-subtle` |
| Focus | Close and action links show ring |
| Active | Pressed states of inner buttons |
| Disabled | n/a |
| Loading | A "loading toast" is not used; use the inline control's loading |
| Error | Error variant |
Never use toasts for tone results. Never use the tone colors for toasts.

### 7.10 Banners (inline alerts)
Full-width within its region, padding 12px 16px, `--radius-md`, 1px border, bg/border/text per variant (`--success-*`, `--warning-*`, `--error-*`, info = primary subtle). Layout: icon 20px left, title (14px/600) and body (14px) in the middle, actions (buttons small) right or below on narrow widths, optional dismiss `x`.
States: Default; Hover/Focus/Active on its inner buttons; Disabled n/a; Loading: action button loading; Error: variant is Error. Errors use `role="alert"`; others `role="status"`. Body text uses `--color-text-primary` (not the variant color) for readability; only the icon and title use the `*-fg` color.

### 7.11 Tabs
- Used in the Results screen on Tablet/Mobile (Evidence, Transcript, Action items) and optionally within About/Help.
- Tab list: 44px high, bottom border `--color-border`, horizontal scroll if needed, `role="tablist"`; tabs `role="tab"` with `aria-selected`, `aria-controls`; panels `role="tabpanel"`.
| State | Spec |
|---|---|
| Default | Text `--color-text-secondary` 500 14px, padding 0 16px, transparent |
| Hover | Text `--color-text-primary`, bg `--color-secondary-subtle` |
| Focus | Ring (inset) |
| Active (selected) | Text `--color-primary` 600, 2px bottom indicator `--color-primary` |
| Disabled | `--color-text-disabled`, not focusable |
| Loading | Count chip shows a 12px spinner |
| Error | A `triangle-alert` 14px in `--warning-fg` after the label when the panel has a section-level failure |
Keyboard: Left/Right arrows move between tabs (automatic activation), Home/End jump.
Count chips on tabs ("Evidence 3") use `--color-secondary-subtle`.

### 7.12 Transcript Segment
Structure: `<li>` containing timestamp, speaker label, text.
Layout (Desktop/Laptop/Tablet): CSS grid `56px 1fr`; column 1 timestamp (mono); column 2: speaker label above text; evidence/action markers at the top-right of column 2.
Layout (Mobile): timestamp and speaker label on one line (timestamp left, label after), text below, full width.

| Variant | Spec |
|---|---|
| Sales Rep | bg `--speaker-rep-bg`, 3px solid left bar `--speaker-rep-bar`, label "Sales Rep" |
| Customer | bg `--speaker-customer-bg`, 3px solid left bar `--speaker-customer-bar`, 16px left inset, label "Customer" |
| Unknown | No bg, 3px **dashed** left bar `--speaker-unknown-bar`, label "Speaker unknown" |
Common: padding 12px 16px, `--radius-md`, gap 8px between segments.

| State | Spec |
|---|---|
| Default | As above |
| Hover | Adds a 1px border `--color-border-strong`; timestamp becomes a link-like control revealing `link` icon is **not** used (no deep links in MVP). Hover has no click action |
| Focus | Segments are not tab stops by default. When focus is moved programmatically (from an evidence/action card) the segment receives `tabindex=-1` focus with the standard ring |
| Active (linked) | bg `--color-primary-subtle` stays for rep; for customer segments bg is `--color-primary-subtle` while linked; 2px outline `--color-focus-ring`, removed after 2.5s unless focused |
| Disabled | n/a |
| Loading | Skeleton segment (timestamp block + 2 text lines) |
| Error | n/a (panel-level) |
| Search match | Matched text wrapped in `<mark>` styled per 2.5 |
| Evidence span | `<mark data-evidence>` with 2px underline `--highlight-evidence-underline`, offset 2px (RED verdict only) |
| Action span | `<mark data-action>` 2px dotted underline `--color-primary` |
Accessibility: each segment's accessible name reads "{speaker} at {m:ss}: {text}". Markers are links with labels "Evidence E1" and "Action item A1".

### 7.13 Evidence Card
Compact card with a distinct **two-block structure** to separate fact from interpretation.
- Container: `--color-surface`, 1px `--color-border`, `--radius-md`, padding 16px; on a RED verdict a 4px left edge `--tone-red-solid`.
- Block 1: **From the transcript.** Overline with `quote` icon; quote text in 15px, in typographic quotes, inside a block with a 3px left border `--color-border-strong`, bg none; attribution line "Sales Rep - 03:42" (13px, mono timestamp).
- Block 2: **AI interpretation.** Overline with `sparkles`; bg `--color-primary-subtle`, 1px `--color-primary-border`, `--radius-sm`, padding 12px; 14px text.
- Header chips: ID (E1) and criterion (neutral chip).
| State | Spec |
|---|---|
| Default | As above |
| Hover | Border `--color-border-strong`; the "Go to {time}" link underlines; `cursor: pointer` on the card |
| Focus | Whole card is focusable (`tabindex=0`, role `button` described as "Show evidence E1 in transcript"); ring |
| Active (selected/linked) | Border `--color-primary`, 2px ring; stays while its transcript segment is linked |
| Disabled | n/a |
| Loading | Skeleton (3 lines) |
| Error | Replaced by inline error row in the list "Couldn't load this evidence item" with Retry (only for per-item fetch errors, rare) |

### 7.14 Action Item Card
- Container as Evidence Card but with a left edge 4px `--color-primary` (for all action items) and no tone colors.
- Header: type chip ("Commitment" / "Follow-up" / "Information promised" / "Customer task"), ID chip (A1), tiny AI tag `sparkles` + "AI summary" (caption) next to the task title to mark that the task wording is AI-written.
- Task title (14px/600).
- Fields grid (2 columns, labels 12px `--color-text-tertiary`, values 14px): **Owner**, **Deadline**. Unspecified value: `circle-dashed` 16px + "Not specified" in `--color-text-tertiary`.
- Quote block identical to the Evidence Card's "From the transcript" block (verbatim) with "Go to {time}".
- Compact variant (Dashboard "Recent action items"): task title, owner/deadline chips inline, call name link, no quote block (quote reachable by opening the call).
| State | Spec |
|---|---|
| Default / Hover / Focus / Active / Disabled / Loading / Error | Same as Evidence Card (7.13). Active = linked segment highlighted |

### 7.15 Charts
Only one chart exists in MVP: the **tone distribution stacked bar** (6A). Spec:
| State | Spec |
|---|---|
| Default | Bar 32px high, segments with required patterns (2.6), 2px `--color-surface` gaps between segments, `--radius-sm` on the outer ends, direct labels on segments >= 48px wide ("RED 3"), legend always shown below |
| Hover | Hovered segment: 2px outline `--color-text-primary` inside, tooltip (7.16) |
| Focus | Segments focusable; focus ring on the segment; tooltip shows on focus |
| Active | Click navigates to Call History filtered by that tone (RED/GREEN/Not analyzed) |
| Disabled | n/a |
| Loading | Skeleton bar + 3 legend lines |
| Error | Inline error banner "Couldn't load tone distribution" with Retry |
| Empty | Text-only empty state (6A) |
| Accessible alternative | "Chart / Table" toggle showing a real data table; the chart wrapper has `role="img"` and a computed `aria-label` |

### 7.16 Tooltip and Popover (supporting)
Tooltip: `--color-text-primary` inverted (bg `--color-text-primary`, text `--color-surface`), 12px/500, 6px 10px padding, `--radius-sm`, max width 240px, 300ms delay; appears on hover **and** keyboard focus; dismissible with Escape; never the only carrier of essential info. Popover (confidence "Why?"): `--color-surface-elevated`, `--shadow-md`, `--radius-md`, 16px padding, max width 320px, opens on click/Enter, closes on Escape/outside click, focus returns to trigger.

### 7.17 Chips and Tags (supporting)
Height 24px, padding 0 8px, `--radius-xs`, 12px/500, bg `--color-secondary-subtle`, text `--color-text-secondary`. Removable chips have a trailing `x` icon button (16px). Not tone-colored.

---

## 8. Responsive Design

**Primary target is desktop**: sales managers analyzing calls. Desktop and Laptop get the full side-by-side analytical layout. Tablet and Mobile are fully functional but prioritize reading and review over side-by-side comparison.

### 8.1 Summary
| Aspect | Desktop (>= 1440) | Laptop (1024-1439) | Tablet (640-1023) | Mobile (< 640) |
|---|---|---|---|---|
| Sidebar | Expanded (collapsible) | Expanded (collapsible) | Rail 72px, overlay expand | Drawer |
| Grid | 12 col, 24px gutter, max 1360 | 12 col, 24px gutter | 8 col, 16px gutter | 4 col, 16px gutter |
| Dashboard | KPI 4-up; 5/7 split; action items 2-col | KPI 4-up; 5/7 split; action items 1-col | KPI 2x2; tone chart full width; table full width | KPI 2x2 (compact); chart full width; table as cards |
| Results | Verdict card + 5/7 split (sticky transcript) | Same | Verdict card full-width, then **tabs** (Evidence / Transcript / Action items) | Sticky compact verdict bar + tabs |
| History | Full table | Full table (hide Action items column < 1200) | Table with Name, Status, Tone, Actions (Upload date moves under the name) | Card list |
| Settings | Form + safeguards side column | Form + safeguards side column | Single column | Single column; save bar stays sticky |

### 8.2 Results Screen Responsive Details
- **Tablet:** Tone Overview stacks its 3 parts into 2 columns (verdict | facts) with the explanation spanning below. Below it, **Tabs** (Evidence, Transcript, Action items; each with a count chip). Default tab = **Evidence** for RED, **Transcript** for GREEN. Tapping "Go to {time}" in Evidence or Action items switches to the Transcript tab and scrolls to and highlights the segment; the tab strip has a "Back to {Evidence}" ghost button at the top of the transcript for 8 seconds after such a jump.
- **Mobile:** The Tone Overview condenses to: verdict pill + one-line label, explanation clamped to 3 lines with "Show more" (expands inline), facts as chips (evidence count, confidence label, sensitivity). Below it a **sticky compact verdict bar** (48px: shield icon + "RED" or "GREEN" + confidence label) pins under the top bar once the full card scrolls out of view so the verdict is always visible. Tabs are sticky below the compact bar. Export and Delete collapse into one overflow menu.
- Settings-used panel is placed after the tabs on Tablet/Mobile as a collapsible section.

### 8.3 Long Transcripts on Small Screens
- Segment text 16px/26px; segments full width; timestamp and speaker on one line above the text (see 7.12 Mobile layout).
- Search bar becomes a full-width sticky row at the top of the Transcript tab with prev/next buttons 44x44.
- No horizontal scrolling anywhere in the transcript (long words wrap with `overflow-wrap: anywhere`).
- Evidence/action markers become 24px chips on the same line as the speaker label.
- Smooth scrolling uses `scroll-margin-top` equal to the stacked sticky heights (top bar + compact bar + tabs + search row) so the target segment is never hidden.
- Touch targets >= 44x44 on Mobile for buttons and chips that act.

### 8.4 Tables on Mobile
History table becomes a list of cards: row 1 call name (truncate) and tone badge at right; row 2 status chip and date; row 3 buttons **View analysis** (secondary, full width). Filters collapse behind a **Filters** button (opens a bottom sheet modal with the selects and Apply/Clear). Search remains visible.

### 8.5 Upload on Small Screens
Drop zone becomes a large **Browse files** button area with the text "Tap to choose an .m4a recording" (no drag copy on touch devices); file card actions stack vertically.

---

## 9. Accessibility (WCAG 2.2 AA)

### 9.1 Semantics and Structure
- Landmarks: `<header>` (top bar), `<nav aria-label="Primary">`, `<main id="main">`, `<aside>` for the safeguards card, `<footer>` not used.
- One `<h1>` per page; headings nest without skipping levels.
- Lists use `<ul>/<ol>`; tables use `<table>` with `<caption>` and `<th scope>`; transcript is a `<ol>`/`role="list"` of `<li>`.
- Forms: every control has a visible `<label>`; helper and error text linked via `aria-describedby`; groups use `<fieldset><legend>`.
- Use native elements (`button`, `a`, `input`, `select`) before ARIA roles. Links navigate; buttons act.
- Document `<title>` follows "{Page} - Sales Call Quality Agent"; results page uses the call name.

### 9.2 Keyboard Navigation
- All functionality available by keyboard; tab order matches visual order; no keyboard traps outside modals/drawer.
- Skip link to main content.
- Shortcuts are limited to component-level patterns (arrow keys in tabs, segmented controls, menus; Enter/Shift+Enter in transcript search). No single-character global shortcuts (WCAG 2.1.4).
- Evidence/action "Go to" interaction: moves focus to the transcript segment and Escape returns focus to the origin card.
- Modal and drawer focus management as specified in 7.8 and 5.4.
- The drop zone is operable via keyboard (Enter/Space opens picker).

### 9.3 Focus Visibility (2.4.7, 2.4.11, 2.4.13)
- Focus ring: 2px `--color-focus-ring`, 2px offset, contrast >= 3:1 against adjacent colors, visible in both themes.
- Focus is never obscured by sticky bars: apply `scroll-padding-top` equal to the sum of sticky element heights.

### 9.4 Color and Contrast
- Text contrast >= 4.5:1; large text and UI boundaries >= 3:1 (1.4.3, 1.4.11).
- **RED/GREEN never rely on color alone:** every tone indicator pairs (a) the text "RED"/"GREEN" and (b) a distinct shield icon (`shield-alert` vs `shield-check`), and charts add patterns (striped vs solid vs dotted) and direct labels. Transcript speakers pair label text, bar style and background.
- Rep vs customer: distinguished by text label, bar, background and inset, not hue alone.
- System states pair icon + title text with color.
- Support forced-colors/high-contrast mode: borders, focus rings and icons use `currentColor`/system colors so they remain visible (`@media (forced-colors: active)` keeps borders and 2px outlines).
- Respect `prefers-contrast: more`: raise border tokens to `--color-border-strong` equivalents.

### 9.5 Screen Reader Labels and Live Regions
| Element | Behavior |
|---|---|
| Verdict | `<section aria-labelledby>`: reads "Sales rep tone: RED. Negative tone detected. Confidence: Medium. 3 verified quotes." |
| Tone badge | `aria-label="Tone: RED"` (table) or the long form in full cards |
| Status chips | Text includes status; spinner icon `aria-hidden` |
| Processing stepper | `<ol>`; each stage `aria-label` "Step 2 of 7: Audio transcription, in progress"; polite live region announces changes; failures use `role="alert"` |
| Upload progress | `role="progressbar"` with value; announcements at 25% steps (not every tick) |
| Transcript segments | Accessible names per 7.12; search results counter polite live region; evidence markers as links |
| Toasts | Live regions as in 7.9 |
| Icons | Decorative icons `aria-hidden="true"`; informative icon-only buttons have `aria-label` |
| Form errors | `role="alert"` on submit summary; field errors linked by `aria-describedby`, `aria-invalid` |
| Settings sensitivity helper | `aria-live="polite"` |

### 9.6 Charts and Status Indicators
- Chart has a text summary (`aria-label`) and a **Table view** toggle presenting identical data (1.1.1, 1.3.1).
- Tooltips are available on focus; essential data is also in the legend text.
- Confidence meter has a text label; segments are `aria-hidden`; the "Why?" popover is keyboard operable.
- Status is never conveyed by animation alone; reduced-motion respected (4.5).

### 9.7 Other WCAG 2.2 Specifics
- Target size (2.5.8): minimum 24x24 CSS px for all pointer targets; 40px controls by default.
- Dragging (2.5.7): the drag-and-drop upload always has the Browse button alternative.
- Consistent help (3.2.6): "About / Help" is always in the same sidebar position.
- Redundant entry (3.3.7): retry never requires re-selecting the file when it is still available; settings drafts persist until saved or discarded.
- Accessible authentication (3.3.8): not applicable (no authentication in MVP).
- Reflow (1.4.10): no horizontal scrolling at 320px width except data tables inside their own scroll container; text spacing overrides must not break layouts (1.4.12).
- Zoom 200%: layouts reflow per breakpoints; no fixed heights on text containers.
- Language: `<html lang="en">`.
- Time limits: none, except toasts, which pause on hover/focus and errors persist.

### 9.8 Testing Requirements for Implementers
Run axe or Lighthouse on every screen in light and dark; keyboard-only walkthrough of upload to results to settings; screen-reader smoke test (VoiceOver or NVDA) of the Results screen; verify with a color-blindness simulator (protanopia/deuteranopia) that RED vs GREEN remain distinguishable in the badge and the chart.

---

## 10. Visual Direction and References

### 10.1 Direction
- **Overall feel:** quiet, precise, commercial B2B analytics. Think of the information density and restraint of established enterprise analytics, observability and developer dashboards, adapted to a single focused workflow. No product's branding, layout, iconography or color identity is copied.
- **Hierarchy:** one clear focal point per screen (verdict card; KPI row; the drop zone; the stepper). Secondary content steps down in size/weight and tone.
- **Density:** comfortable by default (56px table rows, 24px card padding); compact only on the Dashboard table.
- **Surfaces:** flat cards with 1px borders on a lightly tinted page background; shadows only on floating layers.
- **Color use:** neutral surfaces + a single indigo accent. Color carries meaning only (primary action, tone, system state). Tone colors appear only where tone is being communicated.
- **Interactions:** subtle, state-driven (hover, focus, press, expand). Nothing moves without a reason.
- **Data presentation:** tabular numerals, right-aligned numbers, direct labels, chart legends with counts.
- **AI transparency:** every AI-authored element carries the sparkle tag; every transcript-derived element carries the quote tag.

### 10.2 Page Template Pattern
All pages: sidebar + top bar + `<main>` with Page Header (title, description, actions) then a grid of cards. No page uses a different shell.

### 10.3 Imagery
No photographs or illustrations. Icons only (Lucide), inside neutral circles for empty states.

---

## 11. Design Rules (binding)
1. **One system.** Every screen uses the tokens and components defined here.
2. **Reuse.** Use Button, Input, Card, Banner, Toast, Modal, Table, Tabs, Tone Badge, Status Chip, Transcript Segment, Evidence Card, Action Item Card, Chart as specified. Do not create variants. If a new need arises, extend a component here and document it in the Decision Log.
3. **No arbitrary values.** No raw hex, no off-scale spacing/radius/font sizes, no new fonts.
4. **Tone color exclusivity.** `--tone-red-*` and `--tone-green-*` are used only for tone. System success/error/warning use the system tokens. The shield icon family is for tone only.
5. **RED/GREEN semantics.** RED = negative rep tone detected with verified evidence. GREEN = no negative tone detected under configured criteria (not "good"). Never imply more.
6. **Evidence is prominent.** Evidence and the tone explanation appear above the fold on Laptop/Desktop next to the verdict, and the transcript is always one click away.
7. **Fact vs AI.** Verbatim transcript content always uses the "From the transcript" treatment; AI-written content always uses the "AI interpretation" treatment. Never mix them in one block.
8. **Honesty in states.** No fake progress, no fabricated completion, no placeholder analysis. Failures are shown with the reason and a recovery action.
9. **Unspecified means unspecified.** Owner and deadline show "Not specified" when absent. Never blank, never "N/A", never inferred.
10. **No features beyond PRD.md.** Specifically excluded from this design (V2 or Later in the PRD): audio playback synchronized to transcript, re-analysis with new settings, PDF export, presets, side-by-side comparison, editing/completing action items, batch upload, manager feedback buttons, trends/team dashboards, authentication/user menus, global search.
11. **Usability over decoration.** If an element does not help the user decide or act, remove it.
12. **Document decisions.** Any deviation or addition is recorded in section 12.

---

## 12. Design Decision Log

| ID | Decision | Rationale | PRD link |
|---|---|---|---|
| DD-01 | Single indigo brand color; RED/GREEN reserved exclusively for tone | Keeps the product's most important signal unambiguous and avoids the brand color competing with it | M5, brief constraint |
| DD-02 | System success = cyan, error = vermilion orange, warning = gold | Different hues from tone RED/GREEN so tone and system state cannot be confused; icons reinforce | Brief constraint |
| DD-03 | Shield icon family for tone; circle/triangle/octagon for system states | Shape-based differentiation for color-blind users and to prevent semantic bleed | WCAG 1.4.1 |
| DD-04 | Confidence shown as a 3-level labeled meter derived from visible rule-based factors, with a method note, never a percentage | PRD M7 requires confidence; the brief says show it only when supported by the method. A rule-based level is supportable; a model-reported number is not | M7, FR-T6 |
| DD-05 | Confidence meter uses neutral color | Prevents confusion between certainty and tone | M7 |
| DD-06 | Swapping speaker roles re-runs analysis using current saved settings, stated in the modal | FR-S4 allows re-run; telling users which settings apply avoids silent snapshot changes | FR-S4, FR-C3 |
| DD-07 | Processing shows a 7-stage stepper with no percentage or ETA | Honest status; avoids fabricated progress | M10, FR-E1 |
| DD-08 | Upload progress is the only determinate bar and uses real bytes | It is the only progress measurable by the client | M1 |
| DD-09 | Evidence cards separate "From the transcript" and "AI interpretation" blocks | Satisfies the requirement to clearly distinguish actual evidence from AI interpretation | PRD constraint, M6 |
| DD-10 | Dropped (unverifiable) evidence is disclosed with a warning banner | Transparency about the verification step | M6, FR-T8 |
| DD-11 | Results transcript is sticky on Laptop/Desktop; tabs on Tablet/Mobile | Desktop-first side-by-side review; practical reading on small screens | Brief priority |
| DD-12 | Tone chart is a stacked bar with patterns plus a table toggle, not a donut | Easier to label directly and compare; accessible alternative and pattern fills solve red/green color-blindness | WCAG 1.4.1 |
| DD-13 | Settings page has an always-visible save bar and a "Fixed safeguards" card | Makes configurability and its limits transparent; keeps always-on integrity rules visible | M12, FR-C |
| DD-14 | Settings used is a read-only panel on each result with a "differs from current" chip | Meets the requirement to distinguish saved settings from past analyses' settings | M13, FR-C3 |
| DD-15 | Theme toggle (System/Light/Dark) in the top bar | The brief requires light and dark palettes; the PRD does not forbid theme choice | Brief |
| DD-16 | No audio player in the Results screen | PRD lists synchronized playback as V2; "Go to {time}" scrolls the transcript only | V2 |
| DD-17 | "Calls awaiting analysis" = Uploaded or in-progress calls; failed calls surface through a separate "need attention" link | Avoids counting failed calls as pending forever | M11 |
| DD-18 | Speaker-unavailable path offers "Assign sales rep lines" or "Continue without tone result" | Honors FR-S5 (no fabricated attribution) while giving the user a way forward | FR-S5 |
| DD-19 | Delete is available from History and the Results page overflow with a confirmation modal | PRD FR-D6 requires delete; destructive action needs confirmation | FR-D6 |
| DD-20 | No authentication UI (no avatar/user menu) | PRD assumes single-user demo | PRD 10.2 |
| DD-21 | Inter and JetBrains Mono | Highly legible at small sizes with tabular numerals; open-licensed | Brief |

---

## 13. Appendix

### 13.1 Token Reference (CSS custom properties, source of truth for implementation)

```css
:root,
:root[data-theme="light"] {
  /* Brand */
  --color-primary: #4338CA;
  --color-primary-hover: #3730A3;
  --color-primary-active: #2E2A8A;
  --color-primary-subtle: #EEF0FF;
  --color-primary-border: #C7CCF8;
  --color-on-primary: #FFFFFF;
  --color-secondary: #475569;
  --color-secondary-subtle: #EEF1F5;

  /* Surfaces */
  --color-bg: #F5F6FA;
  --color-surface: #FFFFFF;
  --color-surface-elevated: #FFFFFF;
  --color-surface-sunken: #EEF0F6;

  /* Text */
  --color-text-primary: #111827;
  --color-text-secondary: #4A5568;
  --color-text-tertiary: #5B6678;
  --color-text-disabled: #9AA3B2;

  /* Lines and focus */
  --color-border: #DDE1EA;
  --color-border-strong: #B9C0CF;
  --color-divider: #E7EAF1;
  --color-focus-ring: #4338CA;
  --color-scrim: rgba(17, 24, 39, 0.48);

  /* Tone (reserved) */
  --tone-red-solid: #B42318;   --tone-red-on-solid: #FFFFFF;
  --tone-red-fg: #B42318;      --tone-red-bg: #FEF3F2;   --tone-red-border: #FDA29B;
  --tone-green-solid: #067647; --tone-green-on-solid: #FFFFFF;
  --tone-green-fg: #067647;    --tone-green-bg: #ECFDF3; --tone-green-border: #75E0A7;
  --tone-none-solid: #5B6678;  --tone-none-bg: #EEF1F5;  --tone-none-border: #C9D0DD;

  /* System states */
  --success-fg: #0E7490; --success-bg: #ECFEFF; --success-border: #A5F3FC;
  --warning-fg: #854D0E; --warning-bg: #FEFCE8; --warning-border: #FDE68A;
  --error-fg: #C2410C;   --error-bg: #FFF7ED;   --error-border: #FDBA74;
  --error-solid: #C2410C; --error-on-solid: #FFFFFF;

  /* Transcript */
  --speaker-rep-bar: #4338CA;       --speaker-rep-bg: #EEF0FF;
  --speaker-customer-bar: #8A94A8;  --speaker-customer-bg: #EEF0F6;
  --speaker-unknown-bar: #8A94A8;
  --highlight-search: #FEF08A;      --highlight-search-current: #FACC15;

  /* Shadows */
  --shadow-sm: 0 1px 2px rgba(16, 24, 40, 0.06);
  --shadow-md: 0 4px 12px rgba(16, 24, 40, 0.10);
  --shadow-lg: 0 12px 32px rgba(16, 24, 40, 0.16);
}

:root[data-theme="dark"] {
  --color-primary: #8E9BFF;
  --color-primary-hover: #A9B4FF;
  --color-primary-active: #C0C8FF;
  --color-primary-subtle: #1C2250;
  --color-primary-border: #3A4590;
  --color-on-primary: #0B0E17;
  --color-secondary: #A3AEC2;
  --color-secondary-subtle: #1D2436;

  --color-bg: #0B0E17;
  --color-surface: #131826;
  --color-surface-elevated: #1B2132;
  --color-surface-sunken: #0F1320;

  --color-text-primary: #EDF0F7;
  --color-text-secondary: #B4BCCF;
  --color-text-tertiary: #8E98AE;
  --color-text-disabled: #5A6480;

  --color-border: #2A3147;
  --color-border-strong: #3D4663;
  --color-divider: #222942;
  --color-focus-ring: #B3BCFF;
  --color-scrim: rgba(0, 0, 0, 0.64);

  --tone-red-solid: #F97066;   --tone-red-on-solid: #1A0705;
  --tone-red-fg: #FDA29B;      --tone-red-bg: #2D1210;   --tone-red-border: #7A2E26;
  --tone-green-solid: #32D583; --tone-green-on-solid: #04170D;
  --tone-green-fg: #6CE9A6;    --tone-green-bg: #0C2417; --tone-green-border: #1C5A3A;
  --tone-none-solid: #8E98AE;  --tone-none-bg: #1D2436;  --tone-none-border: #3D4663;

  --success-fg: #5EC9E0; --success-bg: #0A2630; --success-border: #155E75;
  --warning-fg: #FACC15; --warning-bg: #2A2108; --warning-border: #6B5410;
  --error-fg: #FB923C;   --error-bg: #2E1608;   --error-border: #7C3A12;
  --error-solid: #FB923C; --error-on-solid: #1A0A02;

  --speaker-rep-bar: #8E9BFF;       --speaker-rep-bg: #1C2250;
  --speaker-customer-bar: #6B7694;  --speaker-customer-bg: #0F1320;
  --speaker-unknown-bar: #6B7694;
  --highlight-search: #6B5410;      --highlight-search-current: #A16207;

  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.4);
  --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.5);
  --shadow-lg: 0 12px 32px rgba(0, 0, 0, 0.6);
}

:root {
  /* Spacing */
  --space-0: 0; --space-1: 4px; --space-2: 8px; --space-3: 12px; --space-4: 16px;
  --space-5: 20px; --space-6: 24px; --space-8: 32px; --space-10: 40px;
  --space-12: 48px; --space-16: 64px;

  /* Radius */
  --radius-xs: 4px; --radius-sm: 6px; --radius-md: 8px; --radius-lg: 12px; --radius-full: 9999px;

  /* Layout */
  --sidebar-width: 248px; --sidebar-width-collapsed: 72px;
  --topbar-height: 64px; --topbar-height-mobile: 56px;
  --content-max-width: 1360px;

  /* Motion */
  --motion-fast: 120ms; --motion-base: 200ms; --ease: cubic-bezier(0.2, 0, 0, 1);

  /* Type */
  --font-sans: Inter, ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  --font-mono: "JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;

  /* Z-index */
  --z-sticky: 100; --z-topbar: 200; --z-sidebar: 210; --z-dropdown: 300;
  --z-scrim: 400; --z-modal: 410; --z-toast: 500;
}
```

### 13.2 Status-to-UI Mapping (single reference)
| Backend status | Status chip | Tone badge | Primary row action (History) |
|---|---|---|---|
| uploaded | Uploaded | Not analyzed | View progress |
| validating | In progress: "Validating" | Not analyzed | View progress |
| transcribing | In progress: "Transcribing" | Not analyzed | View progress |
| analyzing | In progress: "Analyzing" | Not analyzed | View progress |
| complete | Complete | RED or GREEN | View analysis |
| partial (transcript ready; tone or action items missing) | Partial | Not analyzed (or RED/GREEN if tone completed) | View analysis |
| failed (validation, transcription, or analysis) | Failed | Not analyzed | View details |

### 13.3 Copy Deck: Voice and Rules
- **Voice:** plain, neutral, specific. Sentence case everywhere (including buttons: "Start analysis", "Save settings").
- **Never** use exclamation marks, celebratory language, or blame ("You did something wrong").
- Errors: say what happened, what was (not) done, and what to do next. Example: "Transcription failed. Nothing was generated in its place. Retry transcription."
- Tone wording is fixed: "RED: Negative tone detected" and "GREEN: No negative tone detected". Do not use "good", "bad", "passed", "failed" for tone.
- Always use "Sales Rep" and "Customer" for roles.
- AI content labeled "AI interpretation" (explanations) or "AI summary" (action-item task wording). Verbatim content labeled "From the transcript".
- Dates: local time zone, format "Nov 23, 2026, 1:33 AM"; durations `m:ss` / `h:mm:ss`; sizes in MB with one decimal.

### 13.4 Implementation Checklist for AI Coding Assistants
1. Load the token CSS (13.1) globally; set `data-theme` from the stored preference or system setting.
2. Build the app shell (sidebar, top bar, skip link, main) once; all pages render inside it.
3. Build base components in this order: Button, Input/Select/Switch/Radio/Segmented, Card, Chip/Status chip, Tone badge, Banner, Toast, Modal, Tabs, Table, Tooltip/Popover, Skeleton, EmptyState.
4. Build domain components: FileCard, DropZone, Stepper, VerdictCard, ConfidenceMeter, EvidenceCard, ActionItemCard, TranscriptSegment, TranscriptPanel (search + markers), SettingsSections, SaveBar, ToneDistributionChart.
5. Build screens in this order: Upload, Processing, Results, Call History, Settings, Dashboard, About/Help.
6. For every screen, implement all states listed in 6A-6G before moving on (loading, empty, error, partial, populated).
7. Verify against section 9.8 before declaring a screen done.

### 13.5 About / Help Screen (`/help`) Content Spec
A single article column (max width 720px) with a sticky in-page table of contents on Laptop/Desktop (right side, 240px) and none on Mobile. Sections (each an `<h2>` with an anchor id): **How it works** (`#how`: the 7 stages in one paragraph), **Reading your results** (`#results`: RED and GREEN definitions in the exact wording of 2.3, how confidence works with the method note, difference between "From the transcript" and "AI interpretation"), **Evidence and verification** (`#evidence`: quotes are checked against the transcript, unverifiable quotes are excluded), **Preparing a recording** (`#upload`: format, size, duration, speakers, audio tips), **Settings** (`#settings`: what each setting does; changes apply to new analyses only), **Privacy and data handling** (`#privacy`: consented or synthetic audio only; audio and transcript are processed by third-party AI services; how to delete a call), **Known limitations** (`#limitations`: analysis is text-based and may miss sarcasm or vocal tone; transcription and speaker separation can be wrong; English only; results are decision support, not a verdict on a person). An accordion FAQ at the end (5-6 items) uses the Accordion pattern: header button 48px with `chevron-down`, `aria-expanded`, panel content 14px. No external marketing content.
