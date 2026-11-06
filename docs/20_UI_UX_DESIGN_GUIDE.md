# 20 · UI/UX Design Guide — CineMetrics

> **Document type**: Design specification  
> **Status**: Planning / Pre-implementation  
> **Audience**: Frontend developers, designers, AI agents implementing the UI  
> **Related docs**: [`21_MLOPS_AND_TRAINING_WORKFLOW.md`](./21_MLOPS_AND_TRAINING_WORKFLOW.md) · [`23_TESTING_AND_VALIDATION.md`](./23_TESTING_AND_VALIDATION.md) · [`24_DEPLOYMENT_AND_INFRASTRUCTURE.md`](./24_DEPLOYMENT_AND_INFRASTRUCTURE.md)

---

## Table of Contents

1. [Design Philosophy](#1-design-philosophy)
2. [Visual Inspiration](#2-visual-inspiration)
3. [Design System — Color Palette](#3-design-system--color-palette)
4. [Design System — Typography](#4-design-system--typography)
5. [Design System — Spacing, Radius, Shadows](#5-design-system--spacing-radius-shadows)
6. [Design System — Glass Morphism](#6-design-system--glass-morphism)
7. [Component Library](#7-component-library)
8. [Page Layouts](#8-page-layouts)
9. [Animations and Interactions](#9-animations-and-interactions)
10. [Navigation Design](#10-navigation-design)
11. [Responsive Design](#11-responsive-design)
12. [Accessibility](#12-accessibility)
13. [Loading and Error States](#13-loading-and-error-states)
14. [Implementation Notes for Developers](#14-implementation-notes-for-developers)

---

## 1. Design Philosophy

CineMetrics is a **cinema intelligence platform** — it must feel like the product of an institution that takes film seriously. The design language draws from two worlds: the **darkness and richness of cinema itself** (the experience of sitting in a theatre, immersed in a world lit only by the screen) and the **precision and density of financial analytics tools** (Bloomberg terminal, Robinhood, trading dashboards).

### Core Principles

| Principle | What It Means in Practice |
|-----------|--------------------------|
| **Cinematic Immersion** | Dark, near-black backgrounds. The user should feel they are inside a theatre, not on a spreadsheet. |
| **Information Earns Its Place** | Every UI element that occupies space must carry data or meaning. No decorative clutter. No gratuitous gradients. |
| **Typography First** | Numbers, titles, and classifications must be instantly readable. Data clarity trumps decoration. |
| **Purposeful Color** | Color is a data encoding mechanism. Gold = prediction/value. Green = success. Red = risk. Blue = neutral info. These meanings are consistent across every component. |
| **Alive, Not Animated** | Motion exists to communicate state changes and guide attention — not to show off. Animations are fast (150–600ms), physics-based, and interruptible. |
| **Generous Whitespace Despite Density** | High information density does not mean cramped. Breathing room between sections makes complex data readable. |
| **Progressive Disclosure** | Show the most important number first (expected revenue, success category). Reveal detail on demand (SHAP breakdown, scenario range, raw factors). |

### Anti-patterns to Avoid

- **Never** use white backgrounds — this platform lives in the dark.
- **Never** use more than 3 accent colors on a single card.
- **Never** animate for longer than 800ms (except page intro sequences).
- **Never** show raw model outputs without human-readable labels.
- **Never** use pie charts — use bars and linear scales for financial data.
- **Never** hide the confidence indicator — always show it prominently.

---

## 2. Visual Inspiration

**Primary Reference**: [https://vgarss.vercel.app/](https://vgarss.vercel.app/)

Study and internalize the following principles extracted from this reference:

### Bold, High-Contrast Typography
- Headings are large, heavy (700–800 weight), and high-contrast against dark backgrounds.
- Numbers especially: revenue figures, percentages, and years should be rendered in monospace or tabular-figures font so digits align vertically in lists.
- Section labels are small (12–14px), uppercase, letter-spaced, in muted text color — they orient without competing.

### Dark Backgrounds with Subtle Gradients
- Base background is never pure `#000000`. A very subtle blue-black tint (`#0A0A0F`) makes the page feel premium rather than empty.
- Cards sit one or two steps above the background (`#111118`, `#1A1A26`), creating a sense of layered depth without harsh contrast.
- Gradients are extremely subtle — `135deg` direction, slight hue shift — never obvious rainbow gradients.

### Purposeful Use of Color to Encode Meaning
- The reference uses color sparingly: a single accent against an otherwise monochromatic palette.
- In CineMetrics, gold (`#E8B74A`) is reserved for the prediction output — it draws the eye to the most important number on any screen.
- Status colors (green/amber/red) are only applied to classification badges and risk indicators, never decoratively.

### Smooth, Physics-Based Animations
- Transitions use `ease-in-out` or `spring` easing (Framer Motion `type: "spring"`).
- Elements don't just appear; they arrive with a sense of physical weight.
- Hover effects are instantaneous to show responsiveness (< 100ms), but hover-off returns slowly (200–300ms).

### Generous Whitespace Despite Information Density
- Cards have at minimum `24px` internal padding.
- Sections are separated by `48–64px` of vertical space on desktop.
- Dense data tables use `16px` row padding — never compress rows.

---

## 3. Design System — Color Palette

All colors are defined as CSS custom properties (design tokens) in a `:root` block. Every component must reference tokens, never hardcoded hex values.

```css
:root {
  /* ── Backgrounds ─────────────────────────────────── */
  --color-bg-primary:       #0A0A0F;   /* Page background */
  --color-bg-secondary:     #111118;   /* Card surfaces */
  --color-bg-elevated:      #1A1A26;   /* Modals, drawers, elevated cards */
  --color-bg-input:         #15151E;   /* Input fields */

  /* ── Borders & Dividers ──────────────────────────── */
  --color-border-default:   #2A2A3A;   /* Standard borders */
  --color-border-subtle:    #1E1E2C;   /* Very subtle separation */
  --color-border-focus:     #6C63FF;   /* Focus ring (accessibility) */

  /* ── Accent Colors ───────────────────────────────── */
  --color-accent-gold:      #E8B74A;   /* Cinematic gold — prediction highlights, CTAs */
  --color-accent-gold-dim:  #C49A32;   /* Dimmer gold for hover states */
  --color-accent-purple:    #6C63FF;   /* Electric purple — interactive elements, links */
  --color-accent-purple-dim:#574FCC;   /* Dimmer purple for hover */

  /* ── Semantic Colors ─────────────────────────────── */
  --color-success:          #22C55E;   /* Blockbuster predictions, positive deltas */
  --color-success-dim:      #16A34A;   /* Darker green for backgrounds */
  --color-success-bg:       #064E3B;   /* Success badge background */
  --color-warning:          #F59E0B;   /* Moderate confidence, cautionary */
  --color-warning-bg:       #78350F;   /* Warning badge background */
  --color-danger:           #EF4444;   /* High risk, disaster prediction */
  --color-danger-dim:       #DC2626;   /* Darker red */
  --color-danger-bg:        #450A0A;   /* Danger badge background */
  --color-info:             #3B82F6;   /* Neutral information */
  --color-info-bg:          #1E3A5F;   /* Info badge background */

  /* ── Text ────────────────────────────────────────── */
  --color-text-primary:     #F0F0F8;   /* Main readable text */
  --color-text-secondary:   #9090AA;   /* Supporting text, labels */
  --color-text-muted:       #5A5A72;   /* Timestamps, metadata, placeholders */
  --color-text-inverse:     #0A0A0F;   /* Text on light/gold backgrounds */
  --color-text-link:        #6C63FF;   /* Hyperlinks */
  --color-text-link-hover:  #8B84FF;   /* Hovered hyperlinks */

  /* ── Gradients ───────────────────────────────────── */
  --gradient-cinema:        linear-gradient(135deg, #0A0A0F, #1A1020);
  --gradient-gold:          linear-gradient(90deg, #E8B74A, #C49A32);
  --gradient-success:       linear-gradient(135deg, #064E3B, #022C22);
  --gradient-danger:        linear-gradient(135deg, #450A0A, #2D0707);
  --gradient-card-hover:    linear-gradient(135deg, #1A1A26, #22223A);
}
```

### Color Usage Rules

| Scenario | Token |
|----------|-------|
| Predicted revenue figure | `--color-accent-gold` |
| Primary call-to-action button | `--color-accent-gold` background, `--color-text-inverse` text |
| Navigation active state | `--color-accent-purple` |
| Hyperlinks and interactive text | `--color-accent-purple` |
| Blockbuster badge | `--color-accent-gold` bg |
| Super Hit / Hit badge | `--color-success` bg |
| Average badge | `--color-info` bg |
| Below Average / Flop badge | `--color-warning` bg |
| Disaster badge | `--color-danger` bg |
| Positive SHAP bar | `--color-success` |
| Negative SHAP bar | `--color-danger` |
| Confidence gauge (high) | `--color-success` |
| Confidence gauge (medium) | `--color-warning` |
| Confidence gauge (low) | `--color-danger` |
| Data delta up | `--color-success` with ↑ |
| Data delta down | `--color-danger` with ↓ |

---

## 4. Design System — Typography

### Font Stack

```css
:root {
  /* Display / Hero headings (movie titles, page titles) */
  --font-display: 'Clash Display', 'Cal Sans', 'Inter', system-ui, sans-serif;

  /* Body / UI text */
  --font-body: 'Inter', system-ui, -apple-system, sans-serif;

  /* Numbers, stats, monospaced data */
  --font-mono: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace;
}
```

**Font Loading**: Fonts should be loaded via Google Fonts CDN or Fontsource npm packages. Display fonts (`Clash Display`, `Cal Sans`) are available via their respective CDNs or as npm packages.

```html
<!-- Inter from Google Fonts -->
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">

<!-- JetBrains Mono from Google Fonts -->
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
```

**Clash Display / Cal Sans**: Available as npm packages (`@fontsource/clash-display` — REQUIRES VERIFICATION of exact package name) or via their official CDN links.

### Type Scale

```css
:root {
  /* Size + line-height pairs */
  --text-xs:   12px; --leading-xs:   1.4;   /* Metadata, timestamps, tiny labels */
  --text-sm:   14px; --leading-sm:   1.5;   /* Secondary UI text, table cells */
  --text-base: 16px; --leading-base: 1.6;   /* Body paragraphs, descriptions */
  --text-lg:   18px; --leading-lg:   1.5;   /* Lead text, card summaries */
  --text-xl:   20px; --leading-xl:   1.4;   /* Section subheadings */
  --text-2xl:  24px; --leading-2xl:  1.3;   /* Section headings */
  --text-3xl:  30px; --leading-3xl:  1.2;   /* Page subheadings */
  --text-4xl:  36px; --leading-4xl:  1.1;   /* Page titles */
  --text-5xl:  48px; --leading-5xl:  1.0;   /* Hero subtitles */
  --text-hero: 72px; --leading-hero: 0.95;  /* Hero display text */
}
```

### Font Weight Usage

| Weight | Variable | Usage |
|--------|----------|-------|
| 400 | `font-normal` | Body text, descriptions, table data |
| 500 | `font-medium` | UI labels, secondary headings, button text |
| 600 | `font-semibold` | Card titles, section labels, metadata keys |
| 700 | `font-bold` | Page headings, revenue numbers |
| 800 | `font-extrabold` | Hero text, primary revenue prediction, movie titles |

### Specific Typography Rules

- **Movie titles**: `--font-display`, `700` or `800`, `--color-text-primary`
- **Revenue figures**: `--font-mono`, `700`, `--color-accent-gold`
- **Percentage values**: `--font-mono`, `600`, semantic color based on sign
- **Section labels** (e.g., "UPCOMING THIS WEEK"): `--font-body`, `600`, `10–11px`, `letter-spacing: 0.08em`, uppercase, `--color-text-muted`
- **Classification badges**: `--font-body`, `600`, `11px`, `letter-spacing: 0.05em`, uppercase
- **Body paragraphs**: `--font-body`, `400`, `--text-base`, `--color-text-secondary`

### Number Formatting Rules

```
Rupees (Indian market):
  < 1 Cr:    ₹XX Lakh
  1–999 Cr:  ₹XXX Cr
  ≥ 1000 Cr: ₹X,XXX Cr (with comma separator)

Dollars (Global market):
  < 1M:      $XXX K
  1–999M:    $XXX M
  ≥ 1000M:   $X.X B

Confidence:
  Always shown as percentage: 72%
  
Intervals:
  ₹180 Cr – ₹340 Cr (en dash, spaces around it)
```

---

## 5. Design System — Spacing, Radius, Shadows

### Spacing System

The base unit is **4px**. All spacing values must be multiples of 4px.

```css
:root {
  --space-1:  4px;    /* Tight: icon-to-label gap, badge padding */
  --space-2:  8px;    /* Small: input padding vertical, tight list items */
  --space-3:  12px;   /* Medium-small: input padding horizontal, tag padding */
  --space-4:  16px;   /* Medium: component padding default, list row padding */
  --space-6:  24px;   /* Large: card padding, section gap within card */
  --space-8:  32px;   /* XL: card-to-card gap, header padding */
  --space-12: 48px;   /* 2XL: section-to-section gap */
  --space-16: 64px;   /* 3XL: hero padding, major section breaks */
  --space-24: 96px;   /* 4XL: page-level padding top */
  --space-32: 128px;  /* Max: hero vertical padding */
}
```

### Border Radius

```css
:root {
  --radius-sm:   4px;     /* Small badges, chips, code snippets */
  --radius-md:   8px;     /* Inputs, small cards, dropdowns */
  --radius-lg:   12px;    /* Standard cards, modals inner content */
  --radius-xl:   16px;    /* Large cards, prominent panels */
  --radius-2xl:  24px;    /* Modals, bottom sheets, hero cards */
  --radius-full: 9999px;  /* Pill badges, tags, circular avatars */
}
```

### Shadow System

```css
:root {
  /* Standard card shadow — applied to all card surfaces */
  --shadow-card: 
    0 1px 3px rgba(0, 0, 0, 0.5),
    0 4px 16px rgba(0, 0, 0, 0.3);

  /* Elevated shadow — modals, drawers, tooltips */
  --shadow-elevated: 
    0 8px 32px rgba(0, 0, 0, 0.6),
    0 2px 8px rgba(0, 0, 0, 0.4);

  /* Hover shadow — applied on card :hover */
  --shadow-card-hover: 
    0 4px 24px rgba(0, 0, 0, 0.7),
    0 8px 32px rgba(0, 0, 0, 0.4);

  /* Gold glow — applied to primary prediction numbers and CTAs */
  --shadow-glow-gold: 
    0 0 20px rgba(232, 183, 74, 0.2),
    0 0 40px rgba(232, 183, 74, 0.08);

  /* Purple glow — focused inputs, active nav items */
  --shadow-glow-purple: 
    0 0 16px rgba(108, 99, 255, 0.25);

  /* Success glow — blockbuster predictions */
  --shadow-glow-success: 
    0 0 20px rgba(34, 197, 94, 0.15);
}
```

---

## 6. Design System — Glass Morphism

Glass morphism should be used **sparingly** — reserved for elements that float above the content (tooltips, dropdowns, floating action panels, the prediction overlay on movie cards).

```css
.glass {
  background: rgba(26, 26, 38, 0.80);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: var(--shadow-elevated);
}

/* Lighter glass for tooltips */
.glass-light {
  background: rgba(26, 26, 38, 0.65);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.06);
}
```

**When to use glass**: Movie card hover overlay, floating filters panel, tooltip popovers, the sticky navigation bar on scroll.

**When NOT to use glass**: Primary content cards (use solid `--color-bg-secondary`), data tables, form inputs.

---

## 7. Component Library

This section documents the full specification for every reusable component. Each component description includes: visual structure, props/variants, states, and CSS hints.

---

### 7.1 Movie Card

Used in grids, horizontal scroll rows, and search results.

**Visual Structure (top to bottom)**:
```
┌─────────────────────────────┐
│  [2:3 Poster Image]         │  ← aspect-ratio: 2/3; object-fit: cover
│  [Industry Tag] [Lang Tag]  │  ← top-left overlay badges (glass bg)
├─────────────────────────────┤
│  Movie Title (max 2 lines)  │  ← font-display, semibold, text-primary
│  Release Date               │  ← text-sm, text-muted
│  ──────────────────────     │
│  Predicted Revenue  ₹XXX Cr │  ← font-mono, bold, color-accent-gold
│  [Confidence Bar]           │  ← colored horizontal bar, 4px height
│  [Blockbuster] badge        │  ← pill badge, right-aligned
└─────────────────────────────┘
```

**On Hover (desktop)**:
```
┌─────────────────────────────┐
│  [Poster — slightly scaled] │  ← transform: scale(1.02) on inner image
│  ┌─────────────────────────┐│
│  │  "View Full Analysis"   ││  ← glass overlay slides up from bottom
│  │  → (arrow icon)         ││
│  └─────────────────────────┘│
├─────────────────────────────┤
│  (card body unchanged)      │
└─────────────────────────────┘
```

**CSS Implementation Notes**:
```css
.movie-card {
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border-default);
  border-radius: var(--radius-xl);
  overflow: hidden;
  box-shadow: var(--shadow-card);
  transition: transform 150ms ease, box-shadow 150ms ease, border-color 150ms ease;
  cursor: pointer;
}

.movie-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-card-hover);
  border-color: var(--color-border-focus);
}

.movie-card__poster-wrapper {
  position: relative;
  aspect-ratio: 2 / 3;
  overflow: hidden;
}

.movie-card__poster-wrapper img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 300ms ease;
}

.movie-card:hover .movie-card__poster-wrapper img {
  transform: scale(1.04);
}

.movie-card__overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: var(--space-4);
  background: linear-gradient(to top, rgba(10,10,15,0.95), transparent);
  transform: translateY(100%);
  transition: transform 250ms ease;
}

.movie-card:hover .movie-card__overlay {
  transform: translateY(0);
}

.movie-card__body {
  padding: var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.movie-card__title {
  font-family: var(--font-display);
  font-weight: 600;
  font-size: var(--text-base);
  color: var(--color-text-primary);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.movie-card__revenue {
  font-family: var(--font-mono);
  font-weight: 700;
  font-size: var(--text-lg);
  color: var(--color-accent-gold);
}

.movie-card__confidence-bar {
  height: 4px;
  border-radius: var(--radius-full);
  background: var(--color-border-default);
  overflow: hidden;
}

.movie-card__confidence-fill {
  height: 100%;
  border-radius: var(--radius-full);
  /* Color is set dynamically based on confidence value */
  transition: width 600ms ease-in-out;
}
```

**Props (React component interface)**:
```typescript
interface MovieCardProps {
  tmdbId: number;
  title: string;
  posterPath: string | null;    // TMDB poster path
  releaseDate: string;          // ISO date
  industry: 'Bollywood' | 'Hollywood' | 'Tollywood' | 'Kollywood' | string;
  language: string;
  predictedRevenue: number;     // Expected case, in display currency
  revenueUnit: '₹ Cr' | '$ M';
  confidenceScore: number;      // 0–100
  successCategory: SuccessCategory;
  predictionStage: PredictionStage;
  onClick?: () => void;
}

type SuccessCategory =
  | 'blockbuster' | 'super_hit' | 'hit' | 'average'
  | 'below_average' | 'flop' | 'disaster';

type PredictionStage = 'announcement' | 'pre_production' | 'production'
  | 'post_production' | 'pre_release' | 'opening_week' | 'final';
```

---

### 7.2 Prediction Bar (Revenue Range Visualization)

Displays the full prediction interval: pessimistic estimate, expected case, and optimistic estimate on a single horizontal bar.

**Visual Structure**:
```
  Pessimistic       Expected         Optimistic
  ₹180 Cr          ₹290 Cr          ₹440 Cr
      │                 │                 │
  ────●━━━━━━━━━━━━━━━━━●━━━━━━━━━━━━━━━━●────
  [░░░░░DANGER░░░░][ WARNING ][░░░SUCCESS░░░]
```

**Implementation Notes**:
- The full bar spans from `0` (or minimum reasonable value) to `max(optimistic * 1.1)`
- Left segment (`0` to `pessimistic`): `--color-danger` at 30% opacity
- Middle segment (`pessimistic` to `optimistic`): gradient from `--color-warning` to `--color-success`
- Dots mark the three key values
- The expected-case dot is larger (12px diameter) and has a gold glow
- Animated fill on first render: bar fills left-to-right over 600ms

**Props**:
```typescript
interface PredictionBarProps {
  pessimistic: number;
  expected: number;
  optimistic: number;
  currency: '₹ Cr' | '$ M';
  animateOnMount?: boolean;   // default true
}
```

---

### 7.3 Success Classification Badge

A pill-shaped badge indicating predicted success tier.

**Variants and Styles**:

| Category | Background | Text Color | Border |
|----------|------------|------------|--------|
| `blockbuster` | `#E8B74A` | `#0A0A0F` | none |
| `super_hit` | `#064E3B` | `#22C55E` | `1px solid #22C55E` |
| `hit` | `#052E16` | `#4ADE80` | `1px solid #4ADE80` |
| `average` | `#1E3A5F` | `#60A5FA` | `1px solid #3B82F6` |
| `below_average` | `#1C1917` | `#A8A29E` | `1px solid #57534E` |
| `flop` | `#78350F` | `#FCD34D` | `1px solid #F59E0B` |
| `disaster` | `#450A0A` | `#F87171` | `1px solid #EF4444` |

**CSS**:
```css
.badge {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  padding: 3px var(--space-2);
  border-radius: var(--radius-full);
  font-family: var(--font-body);
  font-weight: 600;
  font-size: 11px;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  white-space: nowrap;
}
```

---

### 7.4 SHAP Waterfall Chart

Displays the contribution of each feature to the final prediction, as a horizontal waterfall/tornado chart.

**Visual Structure**:
```
  Base value: ₹120 Cr

  Budget            ████████████████  +₹89 Cr
  Star Power        ████████          +₹47 Cr
  Franchise         ██████            +₹31 Cr
  Director Track    ████              +₹18 Cr
  Genre (Action)    ██                +₹9 Cr
  ─────────────────────────────────────────────
  Release Timing          ████        -₹22 Cr
  Competition             ██          -₹11 Cr
  OTT Proximity           █           -₹6 Cr
  ─────────────────────────────────────────────
  Final Prediction: ₹275 Cr
```

**Implementation Notes**:
- Positive contributions: bars extend to the right, `--color-success` for large values, `--color-accent-gold` for prediction-related
- Negative contributions: bars extend to the left, `--color-danger`
- Each bar has a text label: feature name on left, value on right
- Base value line and final prediction line are dashed
- Bars animate in sequentially (staggered, 50ms between each bar)
- Maximum bars displayed: 10 (top 5 positive, top 5 negative)
- "Show all features" toggle reveals remaining

**Props**:
```typescript
interface SHAPWaterfallProps {
  baseValue: number;
  finalPrediction: number;
  contributions: Array<{
    featureName: string;       // Human-readable label
    featureValue: string;      // Actual feature value, e.g., "₹200 Cr budget"
    shapValue: number;         // Raw SHAP value in prediction units
    shapFormatted: string;     // e.g., "+₹47 Cr"
  }>;
  currency: '₹ Cr' | '$ M';
  maxVisible?: number;         // default: 10
}
```

---

### 7.5 Prediction Confidence Indicator

A semicircular gauge (speedometer-style) showing the model's confidence in its prediction.

**Visual Structure**:
```
        ⚠ 68%
     ╭────────╮
   ╭─╯        ╰─╮
  ─┤ ·  ·  ·  · ├─
         │
       ╰────╯
     Good Confidence
```

**Gauge Segments**:
- 0–39: `--color-danger` (Low Confidence)
- 40–59: `--color-warning` (Moderate Confidence)
- 60–79: `--color-accent-gold` (Good Confidence)
- 80–100: `--color-success` (High Confidence)

**Implementation**: SVG arc with `stroke-dasharray` animation. The needle rotates from `0°` to `180°` (mapping 0–100 scale). Fill color applied to arc stroke.

**Stage Label below gauge**: Shows human-readable stage, e.g., "Pre-Release Stage" — confidence at this stage is explained in a tooltip.

---

### 7.6 Prediction Timeline

A vertical timeline showing how the revenue prediction has evolved as more information became available.

**Visual Structure**:
```
  ○ Announcement (Jan 15)
  │  ₹180–420 Cr  |  Est: ₹280 Cr  |  Confidence: 32%
  │
  ○ Pre-Production (Mar 02)
  │  ₹200–400 Cr  |  Est: ₹295 Cr  |  Confidence: 45%
  │  ↑ +₹15 Cr vs previous
  │
  ● Pre-Release (Nov 01)  ← CURRENT (highlighted, gold ring)
     ₹240–380 Cr  |  Est: ₹310 Cr  |  Confidence: 68%
     ↑ +₹15 Cr vs previous
```

**Visual Rules**:
- Each node is a circle on the left with a vertical line connecting to the next
- Completed stages: filled circle with stage color
- Current stage: larger circle with gold border glow (`--shadow-glow-gold`)
- Future stages (if predicted): dashed circle, muted text
- Delta indicator: green for increase (↑), red for decrease (↓), gray for no change

---

### 7.7 Additional Components

**Search Bar**:
- Full-width, 48px height, `--radius-lg`
- Icon: magnifying glass on left
- Placeholder: "Search movies, directors, actors..."
- On focus: border changes to `--color-border-focus`, purple glow
- Keyboard shortcut hint: `⌘K` or `Ctrl+K` to open global search

**Filter Chip**:
- Small pill (`--radius-full`)
- Inactive: `--color-bg-elevated` background, `--color-text-secondary` text
- Active: `--color-accent-purple` background, white text
- Used in: genre filter, industry filter, year filter, stage filter

**Metric Summary Card**:
- Used in dashboard header row
- Stat label: `--text-sm`, uppercase, muted
- Stat value: `--text-4xl`, `--font-mono`, bold, `--color-text-primary`
- Delta: small chip below value showing % change vs last period
- Icon: right-aligned, 32px, muted color

**Data Table Row** (for cast/director track records):
- 56px row height
- Alternating row backgrounds: transparent / `rgba(255,255,255,0.02)`
- Hover: `rgba(108,99,255,0.05)` background
- Sortable columns: sort icon appears on hover of column header

---

## 8. Page Layouts

### 8.1 Overview / Dashboard Page

This is the entry point to CineMetrics. It balances discoverability (what's new) with intelligence (what the model predicts will be big).

**Layout Structure** (vertical scroll, desktop):

```
┌──────────────────────────────────────────────────────────┐
│  SIDEBAR  │  Hero Section (animated cinema background)   │
│           │  "CineMetrics — Cinema Intelligence"         │
│           │  Subtitle + Quick Search Bar                 │
├──────────────────────────────────────────────────────────┤
│           │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐       │
│           │  │ 42   │ │  8   │ │ 12   │ │ 1,840│       │
│           │  │Movies│ │Block.│ │Mkts  │ │Analyzed│      │
│           │  └──────┘ └──────┘ └──────┘ └──────┘       │
├──────────────────────────────────────────────────────────┤
│           │  HIGHEST PREDICTED EARNERS  [→ See All]      │
│           │  ◀ [Card] [Card] [Card] [Card] [Card] ▶     │
├──────────────────────────────────────────────────────────┤
│           │  UPCOMING THIS WEEK                          │
│           │  [Card] [Card] [Card]                        │
├──────────────────────────────────────────────────────────┤
│           │  INDIAN CINEMA SPOTLIGHT                     │
│           │  Featured large card  │  3 smaller cards     │
├──────────────────────────────────────────────────────────┤
│           │  MARKET TRENDS        │  RECENTLY UPDATED    │
│           │  [Mini sparkline chart]│  [List of movies]   │
└──────────────────────────────────────────────────────────┘
```

**Hero Section Details**:
- Background: `--gradient-cinema` with optional CSS animated particle/starfield (subtle, not distracting)
- Headline: `--text-hero` or `--text-5xl` on mobile, `--font-display`, `800` weight
- Tagline: `--text-xl`, `400` weight, `--color-text-secondary`
- Search bar: centered, 600px max-width, prominent
- Quick links: "Upcoming Releases", "Top Predicted", "Indian Cinema"

**Metric Summary Cards**: 4 cards in a row, each showing one number with an icon and label. Numbers animate (count-up) on page load using Intersection Observer.

**Highest Predicted Earners**: Horizontal scroll row of MovieCards. Arrow buttons on sides. Snap scrolling. Card width: 200px on desktop.

---

### 8.2 Movie Explorer / Detail Page

The most information-dense page. Every piece of data about a movie and its prediction.

**URL Structure**: `/movies/{tmdb_id}` or `/movies/{slug}`

**Layout (desktop — two column above the fold)**:

```
┌──────────────────────────────────────────────────────────┐
│ SIDEBAR │  ← Breadcrumb: Home / Movies / Pushpa 2        │
│         │                                                │
│         │  ┌────────────┐  ┌──────────────────────────┐  │
│         │  │            │  │ Pushpa 2: The Rule        │  │
│         │  │  POSTER    │  │ 2024 · Telugu · Action   │  │
│         │  │  (2:3)     │  │ ★ 8.2 IMDb | 94% BOM ↑  │  │
│         │  │            │  │                          │  │
│         │  │            │  │ ┌─── PREDICTION CARD ───┐│  │
│         │  │            │  │ │ Expected: ₹590 Cr     ││  │
│         │  │            │  │ │ [Prediction Bar]      ││  │
│         │  │            │  │ │ 🏆 BLOCKBUSTER        ││  │
│         │  │            │  │ │ Confidence: 72%       ││  │
│         │  │            │  │ └───────────────────────┘│  │
│         │  │            │  │                          │  │
│         │  │            │  │ [Scenario Selector Tabs] │  │
│         │  │            │  │ Pessimistic|Expected|Opt │  │
│         │  └────────────┘  └──────────────────────────┘  │
│         │                                                │
│         │  ─────── SHAP EXPLANATION ────────────────     │
│         │  [SHAP Waterfall Chart, full width]            │
│         │                                                │
│         │  ─────── FINANCIAL ANALYSIS ───────────────    │
│         │  Budget │ Break-even │ Expected ROI │ Risk     │
│         │                                                │
│         │  ─────── SIMILAR MOVIES ───────────────────    │
│         │  [Horizontal scroll of similar MovieCards]     │
│         │                                                │
│         │  ─────── CAST PERFORMANCE ─────────────────    │
│         │  [Table: Actor, Role, Avg Box Office, Trend]   │
│         │                                                │
│         │  ─────── DIRECTOR TRACK RECORD ────────────    │
│         │  [Chart: last 8 films, revenue timeline]       │
│         │                                                │
│         │  ─────── PREDICTION HISTORY ───────────────    │
│         │  [Vertical timeline component]                 │
│         │                                                │
│         │  ─────── AUDIENCE SENTIMENT ───────────────    │
│         │  [Sentiment score cards + trend chart]         │
└──────────────────────────────────────────────────────────┘
```

**Scenario Selector**:
- Three tabs: "Pessimistic", "Expected", "Optimistic"
- Switching tabs animates the prediction bar and revenue number
- Each scenario shows: revenue range, ROI, success category
- "Expected" is selected by default

**Financial Risk Analysis Panel**:
```
┌────────────────────────────────────────────────────────┐
│  Production Budget    ₹200 Cr   (reported/estimated)  │
│  P&A Budget (est.)    ₹50 Cr    (~25% of production)  │
│  Total Investment     ₹250 Cr                          │
│  Break-even (1.5×)    ₹375 Cr   (distribut. share)    │
│  Predicted Revenue    ₹590 Cr   ✓ ABOVE BREAK-EVEN    │
│  Predicted ROI        +136%                            │
│  Risk Level           LOW                              │
└────────────────────────────────────────────────────────┘
```

> [!NOTE]
> The "Break-even" figure is an estimate based on industry-standard distribution share ratios (typically 45–50% to producers for major releases). The exact figure depends on actual distribution agreements and territory splits, which are not always public. Always display with a disclaimer.

---

### 8.3 Upcoming Releases Page

**URL**: `/upcoming`

**Layout**:
```
┌──────────────────────────────────────────────────────────┐
│ SIDEBAR │  Upcoming Releases                             │
│         │                                                │
│         │  [Search] [Industry▼] [Genre▼] [Year▼] [Sort▼]│
│         │  ─ sticky filter bar ──────────────────────── │
│         │                                                │
│         │  Tabs: This Week │ This Month │ This Year │ All│
│         │                                                │
│         │  [Card] [Card] [Card]                          │
│         │  [Card] [Card] [Card]                          │
│         │  [Card] [Card] [Card]                          │
│         │  ...                                           │
│         │  [Load More / Pagination]                      │
└──────────────────────────────────────────────────────────┘
```

**Filter Bar Behavior**:
- Sticky on scroll (position: sticky; top: 0)
- Glass morphism background when sticky
- Filters update URL query params (`?industry=Bollywood&genre=Action`)
- Filter chips show active count badge

**Sort Options**:
- Release Date (default for "upcoming")
- Predicted Revenue (highest first)
- Confidence Score (highest first)
- Anticipated (social buzz score)

**Grid Variants**:
- Desktop: 3 columns (`repeat(3, 1fr)`)
- Tablet: 2 columns
- Mobile: 1 column

---

### 8.4 What-If Simulator Page

**URL**: `/simulator` or `/what-if`

**Purpose**: Allow users to modify key movie parameters and see how the prediction changes in real time (or near-real-time).

**Layout (desktop — split view)**:
```
┌──────────────────────────────────────────────────────────┐
│ SIDEBAR │                                                │
│         │  What-If Simulator                             │
│         │  ─────────────────────────────────────────    │
│         │  ⚠ These are model scenarios, not causal      │
│         │  predictions. Changing a parameter shows       │
│         │  the model's output for that input set.        │
│         │  ─────────────────────────────────────────    │
│         │                                                │
│         │  ┌── CONTROLS ──────────┐  ┌── LIVE OUTPUT ─┐│
│         │  │                      │  │                 ││
│         │  │ Movie:               │  │  ₹290 Cr        ││
│         │  │ [Pushpa 2 ▼]         │  │  Expected       ││
│         │  │                      │  │                 ││
│         │  │ Budget (₹ Cr):        │  │  [Prediction   ││
│         │  │ ○────────●──── 200   │  │   Bar]          ││
│         │  │                      │  │                 ││
│         │  │ Genre:               │  │  🏆 BLOCKBUSTER ││
│         │  │ [Action ▼]           │  │  Confidence: 68%││
│         │  │                      │  │                 ││
│         │  │ Lead Actor:          │  │  vs Original:   ││
│         │  │ [Allu Arjun ▼]       │  │  ↑ +₹30 Cr     ││
│         │  │                      │  │                 ││
│         │  │ Director:            │  │                 ││
│         │  │ [Sukumar ▼]          │  │                 ││
│         │  │                      │  │                 ││
│         │  │ Release Season:      │  │                 ││
│         │  │ ○ Summer ● Festival  │  │                 ││
│         │  │                      │  │                 ││
│         │  │ Competition Level:   │  │                 ││
│         │  │ [Low / Med / High]   │  │                 ││
│         │  │                      │  │                 ││
│         │  │ [Reset to Original]  │  │                 ││
│         │  └──────────────────────┘  └─────────────────┘│
└──────────────────────────────────────────────────────────┘
```

**Interaction Model**:
- Controls update state immediately
- Prediction re-calculates via API call with debounce (300ms)
- During calculation: loading indicator replaces revenue number (skeleton)
- After calculation: number animates from old → new value

**Disclaimer Placement**: Prominent yellow-bordered box at the top of the page. Never removable or dismissible. Text: *"Revenue predictions are probabilistic estimates based on historical patterns. Changing parameters in this simulator adjusts model inputs — it does not simulate real-world causal effects. Actual revenues depend on many factors beyond these inputs."*

---

### 8.5 Market Intelligence Page

**URL**: `/market`

Displays aggregate market trends, top performers, genre analysis, and cross-market comparisons.

**Sections**:
1. Market Overview Cards (Bollywood YTD, Hollywood Global, South Indian Combined)
2. Top Earners of the Year (ranked list with bars)
3. Genre Revenue Breakdown (grouped bar chart by industry × genre)
4. Seasonal Revenue Trends (line chart: revenue by month, multi-year overlay)
5. Director Success Rate Table (top 20 directors, sortable)
6. Actor Box Office Power Index (ranked with trend arrow)

---

## 9. Animations and Interactions

### Animation Timing Reference

| Animation | Duration | Easing | Trigger |
|-----------|----------|--------|---------|
| Page transition (fade + translate) | 200ms | `ease-out` | Route change |
| Card hover scale | 150ms | `ease` | `:hover` |
| Card hover shadow | 150ms | `ease` | `:hover` |
| Prediction bar fill | 600ms | `ease-in-out` | On first viewport entry |
| Number counter (count-up) | 1200ms | `ease-out` | On first viewport entry |
| SHAP bar entry (staggered) | 400ms per bar, 50ms stagger | `spring` | On first viewport entry |
| Badge appearance | 200ms | `ease-out` | On mount |
| Scenario tab switch | 300ms | `ease-in-out` | Tab click |
| Tooltip appearance | 100ms | `ease-out` | Hover |
| Modal open | 250ms | `ease-out` (backdrop), `spring` (panel) | Trigger |
| Modal close | 200ms | `ease-in` | Escape / backdrop click |
| Filter chip toggle | 150ms | `ease` | Click |
| Gauge needle | 800ms | `spring` | On mount |

### Implementation with Framer Motion

```typescript
// Recommended Framer Motion variants for page entry
const pageVariants = {
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0 },
  exit:    { opacity: 0, y: -8 },
};

const pageTransition = {
  duration: 0.2,
  ease: 'easeOut',
};

// Card hover (applied via motion.div)
const cardVariants = {
  rest: { scale: 1, y: 0 },
  hover: { scale: 1.02, y: -2 },
};

// Staggered list children
const containerVariants = {
  animate: { transition: { staggerChildren: 0.05 } },
};

const itemVariants = {
  initial: { opacity: 0, y: 16 },
  animate: { opacity: 1, y: 0 },
};

// Count-up animation (use react-countup or custom hook)
// Trigger: useInView() from Framer Motion
```

### Skeleton Loading Pattern

Skeleton screens must **match the exact layout** of the content they replace. Never show a generic spinner where specific content will appear.

```css
.skeleton {
  background: linear-gradient(
    90deg,
    var(--color-bg-secondary) 0%,
    var(--color-bg-elevated) 50%,
    var(--color-bg-secondary) 100%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: var(--radius-md);
}

@keyframes shimmer {
  0%   { background-position: -200% 0; }
  100% { background-position:  200% 0; }
}
```

**Skeleton variants to implement**:
- `SkeletonMovieCard`: poster placeholder (gray rectangle 2:3), text lines
- `SkeletonPredictionBar`: bar placeholder
- `SkeletonSHAPChart`: multiple bar placeholder rows
- `SkeletonMetricCard`: number placeholder + label

### Reduced Motion

All animations must respect `prefers-reduced-motion`:

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

For Framer Motion: use `useReducedMotion()` hook and conditionally apply variants.

---

## 10. Navigation Design

### Desktop Sidebar (≥ 1024px)

**Width**: 240px (expanded), 60px (icon-only on `1024–1280px`)

```
┌─────────────────────┐
│  🎬  CineMetrics    │  ← Logo + wordmark
│                     │
│  ─── DISCOVER ───   │  ← Section label (muted, uppercase, 11px)
│  🎬  Overview       │  ← Active: left border gold, bg elevated
│  📅  Upcoming       │
│  🔍  Movie Explorer │
│                     │
│  ─── ANALYSIS ───   │
│  📊  Market Intel.  │
│  💬  Sentiment      │
│  ⚖️  Compare        │
│                     │
│  ─── TOOLS ──────   │
│  🎲  What-If        │
│  🤖  Model Intel.   │
│                     │
│                     │
│  ─────────────────  │  ← spacer pushes bottom items down
│  ⚙️  Settings       │
│  📖  Documentation  │
└─────────────────────┘
```

**Active State Styling**:
```css
.nav-item--active {
  background: rgba(108, 99, 255, 0.12);
  color: var(--color-text-primary);
  border-left: 3px solid var(--color-accent-purple);
}

.nav-item--active .nav-icon {
  color: var(--color-accent-purple);
}
```

**Collapsed State** (60px):
- Only icons visible (no labels)
- Tooltip on hover shows the label
- Logo shrinks to just the film icon

### Mobile Bottom Navigation (< 640px)

Five primary items in a bottom bar (glass morphism):
1. 🏠 Home
2. 📅 Upcoming
3. 🔍 Search
4. 📊 Market
5. ⚙️ More

```css
.bottom-nav {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 60px;
  background: rgba(17, 17, 24, 0.90);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-top: 1px solid var(--color-border-default);
  display: flex;
  align-items: center;
  justify-content: space-around;
  padding-bottom: env(safe-area-inset-bottom);  /* iOS notch support */
  z-index: 100;
}
```

---

## 11. Responsive Design

### Breakpoints

```css
/* Mobile first approach */
/* xs: 0–639px (default, no media query needed) */
@media (min-width: 640px)  { /* sm — tablet portrait */ }
@media (min-width: 768px)  { /* md — tablet landscape */ }
@media (min-width: 1024px) { /* lg — desktop */ }
@media (min-width: 1280px) { /* xl — wide desktop */ }
@media (min-width: 1440px) { /* 2xl — ultra-wide */ }
```

### Layout Behavior by Breakpoint

| Component | Mobile (< 640px) | Tablet (640–1023px) | Desktop (≥ 1024px) | Wide (≥ 1440px) |
|-----------|-----------------|--------------------|--------------------|-----------------|
| Sidebar | Hidden (bottom nav) | Icon-only (60px) | Full (240px) | Full (280px) |
| Dashboard grid | 1 column | 2 columns | 3 columns | 4 columns |
| Upcoming grid | 1 column | 2 columns | 3 columns | 4 columns |
| Movie detail | Stack (single column) | Stack | Side-by-side (40/60) | Side-by-side (35/65) |
| SHAP chart | Horizontal scroll | Full width | Full width | Full width |
| Hero text | `--text-3xl` | `--text-4xl` | `--text-5xl` | `--text-hero` |
| Summary cards | 2×2 grid | 4 in a row | 4 in a row | 4 in a row |
| Navigation | Bottom bar | Collapsed sidebar | Full sidebar | Full sidebar |

### Mobile-Specific Considerations

- **Touch targets**: Minimum 44×44px for all interactive elements
- **Tap states**: `active:` states with slightly darker background (no hover on touch)
- **Swipe gestures**: Horizontal scroll cards should use native scroll with `scroll-snap`
- **Charts on mobile**: Simplify — prediction bar only, hide SHAP chart behind "Show Details" toggle
- **Font size**: Never below 14px on mobile (accessibility + readability)
- **Input zooming**: Set `font-size: 16px` on inputs to prevent iOS auto-zoom

---

## 12. Accessibility

CineMetrics targets **WCAG 2.1 Level AA** compliance.

### Color Contrast Requirements

| Element | Background | Text Color | Contrast Ratio | Passes AA? |
|---------|------------|------------|---------------|------------|
| Body text | `#0A0A0F` | `#F0F0F8` | ≈ 17.5:1 | ✅ |
| Secondary text | `#0A0A0F` | `#9090AA` | ≈ 5.2:1 | ✅ |
| Muted text (metadata) | `#0A0A0F` | `#5A5A72` | ≈ 3.1:1 | ⚠️ Large text only |
| Gold on dark | `#111118` | `#E8B74A` | ≈ 7.1:1 | ✅ |
| Black on gold CTA | `#E8B74A` | `#0A0A0F` | ≈ 7.1:1 | ✅ |
| White on purple | `#6C63FF` | `#FFFFFF` | ≈ 4.6:1 | ✅ |

> [!WARNING]
> `--color-text-muted` (`#5A5A72`) does NOT meet AA contrast for body text. It must only be used for metadata labels (12px+), never for essential information. Use `--color-text-secondary` for anything that must be read.

### Keyboard Navigation

- All interactive elements reachable via `Tab`
- Logical tab order follows visual reading order
- Focus ring: `outline: 2px solid var(--color-border-focus); outline-offset: 2px;`
- Skip-to-content link at top of page (visually hidden, appears on focus)
- Modal traps focus while open; returns focus to trigger on close
- Dropdown menus navigable with Arrow keys; closed with Escape

### ARIA Labeling

```jsx
// Prediction bar
<div
  role="meter"
  aria-label={`Predicted revenue range: ${pessimistic} to ${optimistic}, expected ${expected}`}
  aria-valuenow={expected}
  aria-valuemin={pessimistic}
  aria-valuemax={optimistic}
>

// Confidence gauge
<div
  role="meter"
  aria-label={`Prediction confidence: ${score}% (${stage})`}
  aria-valuenow={score}
  aria-valuemin={0}
  aria-valuemax={100}
>

// Classification badge
<span aria-label={`Success prediction: ${category}`}>

// SHAP chart (must have text summary for screen readers)
<figure aria-label="Feature importance chart">
  <figcaption className="sr-only">
    The top factors increasing revenue prediction are: {topPositive.join(', ')}.
    The top factors decreasing prediction are: {topNegative.join(', ')}.
  </figcaption>
  {/* chart SVG */}
</figure>
```

### Screen Reader Text Utility

```css
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border-width: 0;
}
```

---

## 13. Loading and Error States

### State Specifications

#### Movie Not Found

**Trigger**: User navigates to `/movies/99999999` or searches for a non-existent title.

```
┌─────────────────────────────────────┐
│                                     │
│           🎬 (film icon, 64px)      │
│                                     │
│    Movie Not Found                  │
│                                     │
│    We couldn't find this movie      │
│    in our database. It may not      │
│    have been ingested yet.          │
│                                     │
│    [Browse Upcoming Releases]       │
│    [Go back to Search]              │
│                                     │
└─────────────────────────────────────┘
```

#### Prediction Unavailable (Insufficient Data)

**Trigger**: Movie exists in database but lacks enough features for a reliable prediction (e.g., only title and release year known).

```
┌─────────────────────────────────────┐
│  ⚠️ Prediction Not Available        │
│                                     │
│  We don't have enough information   │
│  about this movie to generate a     │
│  revenue prediction yet.            │
│                                     │
│  Missing data: budget, cast, genre  │
│                                     │
│  Prediction will be available once  │
│  more details are announced.        │
│                                     │
│  Last checked: 2 days ago           │
└─────────────────────────────────────┘
```

#### API Error (Backend Unreachable)

**Trigger**: Network error or 5xx response from backend.

```
┌─────────────────────────────────────┐
│  ⚠️ Something went wrong            │
│                                     │
│  We couldn't load this content.     │
│  This is likely a temporary issue.  │
│                                     │
│  Error code: 503                    │
│                                     │
│  [Try Again]  [Go to Homepage]      │
└─────────────────────────────────────┘
```

**Implementation**: React Error Boundary + toast notification for transient errors.

#### Loading Movie Details

Display `SkeletonMovieCard` and skeleton placeholders for all data sections. No spinner. Poster area shows gray animated gradient placeholder matching 2:3 ratio.

#### Loading Predictions

Skeleton replaces the prediction card. Revenue number area shows two gray lines (40px height, different widths to mimic "₹XXX Cr" text). Prediction bar shows as a flat gray rectangle.

#### Empty Search Results

```
┌─────────────────────────────────────┐
│           🔍 (search icon, 48px)    │
│                                     │
│    No movies found for              │
│    "Kalki 2898"                     │
│                                     │
│    Try:                             │
│    • Checking the spelling          │
│    • Searching by director name     │
│    • Using a shorter search term    │
│                                     │
│    [Browse All Upcoming Movies]     │
└─────────────────────────────────────┘
```

**Fuzzy match suggestions**: If Levenshtein distance < 3 from a known title, show "Did you mean: [title]?" above the empty state.

#### Rate Limited

```
┌─────────────────────────────────────┐
│  🚦 Too Many Requests               │
│                                     │
│  You've made too many requests.     │
│  Please wait 60 seconds.            │
│                                     │
│  [Countdown timer]                  │
└─────────────────────────────────────┘
```

---

## 14. Implementation Notes for Developers

### Technology Stack (Recommended)

| Layer | Recommended | Alternative |
|-------|-------------|-------------|
| Framework | React 18 (with Vite) | Next.js 14 |
| Styling | Tailwind CSS v3 + CSS custom properties | Vanilla CSS modules |
| Animation | Framer Motion | React Spring |
| Charts | Recharts or Nivo | D3.js (lower-level) |
| State | Zustand | Redux Toolkit |
| Data fetching | React Query (TanStack Query) | SWR |
| Component docs | Storybook | - |
| Testing | Vitest + React Testing Library | Jest |
| E2E | Playwright | Cypress |

### Tailwind Configuration

The design tokens above should be added to `tailwind.config.js`:

```javascript
module.exports = {
  theme: {
    extend: {
      colors: {
        'bg-primary':    '#0A0A0F',
        'bg-secondary':  '#111118',
        'bg-elevated':   '#1A1A26',
        'accent-gold':   '#E8B74A',
        'accent-purple': '#6C63FF',
        // ... all tokens
      },
      fontFamily: {
        display: ['Clash Display', 'Cal Sans', 'Inter', 'sans-serif'],
        body:    ['Inter', 'system-ui', 'sans-serif'],
        mono:    ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
    },
  },
};
```

### Component File Organization

```
src/
├── components/
│   ├── ui/                  # Design system primitives
│   │   ├── Badge.tsx
│   │   ├── Button.tsx
│   │   ├── Card.tsx
│   │   ├── Skeleton.tsx
│   │   └── ...
│   ├── movie/               # Movie-specific components
│   │   ├── MovieCard.tsx
│   │   ├── PredictionBar.tsx
│   │   ├── SHAPWaterfall.tsx
│   │   ├── ConfidenceGauge.tsx
│   │   └── PredictionTimeline.tsx
│   ├── layout/              # Layout components
│   │   ├── Sidebar.tsx
│   │   ├── BottomNav.tsx
│   │   └── PageWrapper.tsx
│   └── charts/              # Data visualization
│       ├── MarketTrendChart.tsx
│       ├── DirectorTrackRecord.tsx
│       └── SeasonalTrend.tsx
├── pages/                   # Page-level components
├── hooks/                   # Custom React hooks
├── store/                   # Zustand state
├── api/                     # API client functions
└── styles/
    ├── globals.css           # CSS custom properties, resets
    └── fonts.css             # Font-face declarations
```

---

*This design guide is the single source of truth for CineMetrics UI/UX. All deviations must be documented and justified. When in doubt: dark, gold, dense but readable.*
