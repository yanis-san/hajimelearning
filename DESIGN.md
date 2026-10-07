---
name: Hajime Learning
description: L'e-learning ancré en Algérie — local, fiable, accessible.
colors:
  tangerine: "#f97316"
  tangerine-deep: "#ea580c"
  tangerine-soft: "#fdba74"
  tangerine-wash: "#fff7ed"
  ink: "#111827"
  slate: "#374151"
  smoke: "#6b7280"
  ash: "#9ca3af"
  mist: "#d1d5db"
  bone: "#f3f4f6"
  paper: "#f9fafb"
  white: "#ffffff"
  success: "#22c55e"
  danger: "#ef4444"
  warning: "#eab308"
  info: "#3b82f6"
typography:
  display:
    fontFamily: "Inter, system-ui, sans-serif"
    fontSize: "clamp(1.5rem, 4vw, 2.25rem)"
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: "-0.01em"
  headline:
    fontFamily: "Inter, system-ui, sans-serif"
    fontSize: "1.25rem"
    fontWeight: 700
    lineHeight: 1.3
    letterSpacing: "-0.01em"
  title:
    fontFamily: "Inter, system-ui, sans-serif"
    fontSize: "1rem"
    fontWeight: 600
    lineHeight: 1.4
  body:
    fontFamily: "Inter, system-ui, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 400
    lineHeight: 1.6
  label:
    fontFamily: "Inter, system-ui, sans-serif"
    fontSize: "0.75rem"
    fontWeight: 500
    lineHeight: 1.4
    letterSpacing: "0.01em"
rounded:
  sm: "8px"
  md: "12px"
  lg: "16px"
  full: "9999px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "24px"
  xl: "32px"
  section: "64px"
components:
  button-primary:
    backgroundColor: "{colors.tangerine}"
    textColor: "{colors.white}"
    rounded: "{rounded.md}"
    padding: "10px 16px"
  button-primary-hover:
    backgroundColor: "{colors.tangerine-deep}"
  button-secondary:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.white}"
    rounded: "{rounded.md}"
    padding: "10px 16px"
  button-secondary-hover:
    backgroundColor: "{colors.slate}"
  button-outline:
    backgroundColor: "{colors.white}"
    textColor: "{colors.slate}"
    rounded: "{rounded.md}"
    padding: "10px 16px"
  button-outline-hover:
    backgroundColor: "{colors.bone}"
  button-ghost:
    backgroundColor: "transparent"
    textColor: "{colors.smoke}"
    rounded: "{rounded.md}"
    padding: "10px 16px"
  button-ghost-hover:
    backgroundColor: "{colors.bone}"
  button-danger:
    backgroundColor: "{colors.danger}"
    textColor: "{colors.white}"
    rounded: "{rounded.md}"
    padding: "10px 16px"
  input-default:
    backgroundColor: "{colors.white}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    padding: "10px 16px"
  card-surface:
    backgroundColor: "{colors.white}"
    rounded: "{rounded.lg}"
    padding: "24px 32px"
  badge-default:
    backgroundColor: "{colors.bone}"
    textColor: "{colors.smoke}"
    rounded: "{rounded.full}"
    padding: "2px 10px"
  avatar-fallback:
    backgroundColor: "{colors.tangerine}"
    textColor: "{colors.white}"
    rounded: "{rounded.full}"
---

# Design System: Hajime Learning

## Overview

**Creative North Star: "The Local Classroom"**

Hajime Learning's interface is a familiar, trustworthy learning space that feels like it belongs in Algeria, not imported from a foreign template. The design is calm and clean — restrained enough that course content always leads, spacious enough that dense information (lesson lists, quiz forms, payment flows) never feels cramped. The warmth lives in precise details: a confident tangerine accent, generous white space, and softly rounded surfaces that read as approachable without tipping into playful.

The system serves two audiences with different needs on different screens. Students browse a course catalog, watch lessons, take quizzes, and track progress — tasks that reward clear hierarchy and minimal distraction. Instructors create courses and manage content — tasks that reward density and efficiency. The design language is the same for both; only the layout density shifts.

There is no dramatic motion, no glassmorphism, no dark mode. The interface is a well-lit classroom: white walls, clean board, warm lighting. If a screen feels noisy, remove rather than add.

**Key Characteristics:**
- Content-first: the UI recedes; the course material leads
- One accent: tangerine orange, used sparingly for CTAs and active states
- Softly rounded: consistent `rounded-xl` / `rounded-2xl` corner language
- Light and airy: gray-50 page background, white cards, subtle ambient shadows
- Single typeface: Inter at every weight, no decorative fonts

## Colors

A warm, neutral palette grounded by a single confident accent.

### Primary
- **Tangerine** (#f97316): The only accent color. Used for primary CTAs, active nav states, the logo wordmark, avatar fallbacks, notification badges, focus rings, and progress bars. Its energy is the entry point; its rarity is the discipline.
- **Tangerine Deep** (#ea580c): Hover state for primary buttons and links. Slightly darker and warmer.
- **Tangerine Soft** (#fdba74): Progress bar fills on dark overlays (course card hover state).
- **Tangerine Wash** (#fff7ed / `orange-50`): Tinted background for instructor plan revenue highlights and active sidebar items.

### Neutral
- **Ink** (#111827 / `gray-900`): Primary text, headings, and the secondary button fill. The darkest value in the system.
- **Slate** (#374151 / `gray-700`): Secondary text — labels, nav links, body copy that needs less emphasis than a heading.
- **Smoke** (#6b7280 / `gray-500`): Tertiary text — help text, timestamps, disabled labels, placeholder text.
- **Ash** (#9ca3af / `gray-400`): Quaternary — footer links, dividers, muted icons.
- **Mist** (#d1d5db / `gray-300`): Borders — input strokes, card borders, divider lines.
- **Bone** (#f3f4f6 / `gray-100`): Tinted surfaces — badge backgrounds, hover fills on ghost buttons, module header backgrounds.
- **Paper** (#f9fafb / `gray-50`): Page background — the default canvas behind all content.
- **White** (#ffffff): Card surfaces, input fills, navbar, footer.

### Semantic
- **Success** (#22c55e / `green-500`): Completion checkmarks, enrollment confirmations, success alerts.
- **Danger** (#ef4444 / `red-500`): Error states, destructive actions, required-field asterisks, rejection badges.
- **Warning** (#eab308 / `yellow-500`): Draft indicators, caution alerts.
- **Info** (#3b82f6 / `blue-500`): Informational alerts, default notification tint.

### Named Rules
**The One Accent Rule.** Tangerine is the only chromatic color in the interface outside of semantic states. If something is orange, it is interactive or active. If something is not interactive, it is gray.

## Typography

**Display & Body Font:** Inter (with system-ui, sans-serif fallback)

**Character:** One typeface, many weights. Inter is the Swiss Army knife — legible at 10px labels, confident at 36px display. The system relies entirely on weight and size contrast, never on typeface contrast. This keeps the interface quiet and lets content speak.

### Hierarchy
- **Display** (700, clamp(1.5rem, 4vw, 2.25rem), 1.2): Page titles — "Catalogue", "Mes Cours", "Devenir Instructeur". Tight tracking.
- **Headline** (700, 1.25rem, 1.3): Section headings within pages — module titles, plan names, card titles.
- **Title** (600, 1rem, 1.4): Sub-headings — form group labels, sidebar course title, alert titles.
- **Body** (400, 0.875rem, 1.6): Running text — course descriptions, lesson content, form help text. Max comfortable reading width ~65ch.
- **Label** (500, 0.75rem, 1.4): Metadata — badge text, timestamps, category chips, button text at sm size. Slight positive tracking.

### Named Rules
**The Weight-Not-Face Rule.** Never introduce a second typeface. Hierarchy is conveyed through weight (300–700) and size alone. If distinction is needed, increase weight or decrease size — never switch fonts.

## Layout

The system uses a single-column centered layout with a `max-w-7xl` (80rem / 1280px) container, horizontally padded at `px-4` → `sm:px-6` → `lg:px-8`. There is no CSS grid system; layout is flexbox-driven and stacks vertically on mobile.

### Density
- **Catalog / public pages**: Generous — `py-12` to `py-16` between sections, `gap-6` to `gap-8` between cards.
- **Dashboard / manage pages**: Moderate — `py-8` section spacing, `gap-4` between list items.
- **Lesson view**: Split layout — sidebar (w-72 to w-80, collapsible on mobile) + content area. Sidebar is sticky below the navbar.

### Breakpoints
The system uses Tailwind's defaults: `sm` (640px), `md` (768px), `lg` (1024px), `xl` (1280px). The navbar collapses to a hamburger at `md`. The lesson sidebar collapses at `lg`. Card grids are typically 1-col → 2-col (`sm`) → 3-col (`lg`) → 4-col (`xl`).

### Spacing Rhythm
Spacing follows Tailwind's 4px base scale. Consistent vertical rhythm within components uses `space-y-1` (4px) for tight groups (label → input → error), `space-y-2` (8px) for lists, and `gap-3` (12px) to `gap-4` (16px) between sibling components.

## Elevation & Depth

Subtle and ambient. Surfaces are lightly lifted at rest and gently rise on interaction. Shadows are never dramatic; they provide just enough separation from the gray-50 page background to make white cards feel distinct.

### Shadow Vocabulary
- **Ambient rest** (`shadow-sm` / `0 1px 2px rgba(0,0,0,0.05)`): Cards, navbar, auth container. The default state.
- **Hover lift** (`shadow-md` / `0 4px 6px rgba(0,0,0,0.07)`): Course cards on hover, primary buttons on hover. Adds a sense of interactivity.
- **Featured emphasis** (`shadow-lg` / `0 10px 15px rgba(0,0,0,0.1)`): Featured plan card, price badges. Reserved for the one element that needs to stand out from siblings.

### Named Rules
**The Quiet Surface Rule.** Surfaces are flat-ish at rest. Shadows appear as a response to interaction (hover) or emphasis (featured), never as decoration. Two shadows on the same component is an error.

## Shapes

The system uses a consistent softly-rounded corner language. Corners are never sharp (0px) and never circular on rectangular elements.

- **Components** (`rounded-xl` / 12px): Buttons, inputs, selects, textareas, badges, alerts, nav link hover backgrounds, mobile menu items.
- **Containers** (`rounded-2xl` / 16px): Cards, auth card, course card, plan card, notification dropdown.
- **Chips / Badges** (`rounded-full` / 9999px): Status badges, notification count indicators, avatar.
- **Small accents** (`rounded-md` / 6px, `rounded-lg` / 8px): Category chip on course card, module accordion border.

### Named Rules
**The Soft Edge Rule.** No sharp corners exist in the system. The minimum radius is `rounded-md` (6px). If a new element feels angular, round it to match its nearest sibling.

## Components

### Buttons
Confident and quiet. The button is the system's most disciplined component — five variants, three sizes, one radius.

- **Shape:** Softly rounded edges (12px / `rounded-xl`)
- **Primary:** Tangerine fill, white text (`bg-orange-500 text-white`), light shadow at rest, deeper shadow on hover. The only button that uses color.
- **Hover / Focus:** Darkens to tangerine-deep (`bg-orange-600`), gains `shadow-md`. Focus ring is `ring-2 ring-orange-400 ring-offset-2`.
- **Secondary:** Ink fill, white text (`bg-gray-900 text-white`). For strong non-primary actions.
- **Outline:** White fill, mist border, slate text. For tertiary or paired actions.
- **Ghost:** Transparent fill, smoke text. For inline or contextual actions (e.g. dismiss).
- **Danger:** Red fill, white text. For destructive actions only.
- **Sizes:** `sm` (px-3 py-1.5 text-xs), `md` (px-4 py-2.5 text-sm), `lg` (px-6 py-3 text-base).
- **Disabled:** 50% opacity, `cursor-not-allowed`, `pointer-events-none`.

### Badges
- **Style:** Pill-shaped (`rounded-full`), tinted background + darker text per variant.
- **Variants:** gray (default), green, red, blue, orange, yellow — each using the `-100` background and `-800` (or `-700` for orange) text of its Tailwind color.
- **Size:** Compact — `px-2.5 py-0.5 text-xs font-medium`.

### Cards / Containers
- **Course Card:** PS2-jacket aspect ratio (7:10), `rounded-2xl`, full-bleed image. Overlay appears on hover with gradient-to-t from black/90. Category chip (top-left) and price badge (top-right) float over the image. Hover scales image to 1.03.
- **Auth Card:** `rounded-2xl`, white background, `border border-gray-100`, `shadow-sm`, `px-8 py-10` internal padding. Centered on a gray-50 full-height background.
- **Plan Card:** `rounded-2xl`, white background. Featured variant adds `border-orange-300`, `ring-2 ring-orange-100`, `shadow-lg`, and `scale-[1.03]`.
- **General surface:** White fill, `border border-gray-100` or `border-gray-200`, `shadow-sm`, `rounded-2xl`.

### Inputs / Fields
- **Style:** White fill, mist border (`border-gray-300`), `rounded-xl`, `px-4 py-2.5`.
- **Focus:** `ring-2 ring-orange-400`, border becomes transparent. Clean and obvious.
- **Error:** Border shifts to `border-red-400`, focus ring to `ring-red-400`.
- **File input:** Dashed border, icon + label layout, hover tints border to orange.
- **Select / Textarea:** Same treatment as text input. Textarea allows vertical resize.

### Navigation
- **Navbar:** White background, `border-b border-gray-100`, `shadow-sm`, sticky `top-0 z-50`. Height is `h-16`. Logo is tangerine wordmark with book icon.
- **Desktop links:** `text-sm font-medium text-gray-600`, hover → `text-gray-900 bg-gray-50`, `rounded-lg` hover background.
- **Active admin link:** `text-orange-600 hover:bg-orange-50`.
- **Mobile menu:** Slide-down panel with `x-transition` (150ms ease-out in, 100ms ease-in out). Items are `rounded-xl`, hover → `text-orange-600 bg-orange-50`.
- **Footer:** White background, `border-t border-gray-100`. Logo wordmark in tangerine, copyright in ash, CGV/Contact links in ash → smoke on hover.

### Alerts / Flash Messages
- **Structure:** Icon + text, `rounded-xl`, `border` (alerts) or `border-l-4` (flash messages).
- **Variants:** success (green-50/green-500), warning (yellow-50/yellow-400), error (red-50/red-500), info (blue-50/blue-500).
- **Dismissible:** Close button with `x-transition`, flash messages auto-dismiss after 4 seconds.

### Progress Bar
- **Track:** `bg-gray-100 rounded-full h-2`.
- **Fill:** `bg-orange-500 rounded-full`, animated width transition (`duration-500`).
- **Label:** Optional percentage in `text-xs text-gray-500`.

### Avatar
- **With image:** `rounded-full object-cover border border-gray-200`.
- **Fallback:** Tangerine circle with white initial letter.
- **Sizes:** `sm` (24px), `md` (32px), `lg` (64px), `xl` (96px).

## Do's and Don'ts

### Do:
- **Do** use tangerine (#f97316) exclusively for interactive elements — buttons, links, focus rings, active states, badges that signal action.
- **Do** keep cards white on a gray-50 background. The contrast is subtle but consistent.
- **Do** use `rounded-xl` (12px) for components and `rounded-2xl` (16px) for containers. Match the nearest sibling if unsure.
- **Do** pair every input border state with a matching focus ring color (orange for default, red for error).
- **Do** use Inter at weight 400–700 only. Use size and weight to create hierarchy, never a second font.
- **Do** auto-dismiss flash messages after 4 seconds with a graceful slide-up transition.

### Don't:
- **Don't** introduce a second accent color. The system has one: tangerine. Blue, purple, and teal are reserved for semantic states only.
- **Don't** use sharp corners (radius 0) on any visible element.
- **Don't** stack shadows. One shadow per element, escalating only on hover or emphasis.
- **Don't** use dark backgrounds for content areas. Dark overlays are permitted only on course card hover gradients.
- **Don't** add decorative illustrations, patterns, or background textures. The classroom is clean.
- **Don't** reference the Tailwind config's `primary: '#6750A4'` — it is vestigial and unused. Tangerine is the actual primary.
