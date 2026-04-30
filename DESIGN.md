---
version: alpha
name: ReconIQ
description: Precision intelligence tool — Vercel-grade minimalism with indigo accent, engineered for clarity over decoration.
colors:
  primary: "#171717"
  secondary: "#5c5f73"
  tertiary: "#5e6ad2"
  neutral: "#fafafa"
  canvas: "#fafafa"
  panel: "#f0f0f5"
  surface: "#ffffff"
  elevated: "#f5f5fa"
  accent: "#5e6ad2"
  accent-hover: "#4d5bc4"
  accent-light: "#eceefa"
  accent-glow: "#d5d9f3"
  ink: "#171717"
  text-primary: "#171717"
  text-secondary: "#5c5f73"
  text-muted: "#8b8fa3"
  border: "#ebebeb"
  border-hover: "#d1d1d8"
  success: "#10b981"
  warning: "#f59e0b"
  error: "#ef4444"
  info: "#5e6ad2"
  success-bg: "#ecfdf5"
  success-text: "#047857"
  warning-bg: "#fffbeb"
  warning-text: "#b45309"
  error-bg: "#fef2f2"
  error-text: "#b91c1c"
  info-bg: "#eef2ff"
  info-text: "#4338ca"
typography:
  display:
    fontFamily: Inter
    fontSize: 2.5rem
    fontWeight: 700
    lineHeight: "1.1"
    letterSpacing: "-0.03em"
  h1:
    fontFamily: Inter
    fontSize: 2rem
    fontWeight: 700
    lineHeight: "1.15"
    letterSpacing: "-0.025em"
  h2:
    fontFamily: Inter
    fontSize: 1.5rem
    fontWeight: 600
    lineHeight: "1.25"
    letterSpacing: "-0.02em"
  h3:
    fontFamily: Inter
    fontSize: 1.125rem
    fontWeight: 600
    lineHeight: "1.35"
    letterSpacing: "-0.01em"
  body-lg:
    fontFamily: Inter
    fontSize: 1.1rem
    fontWeight: 400
    lineHeight: "1.6"
  body:
    fontFamily: Inter
    fontSize: 1rem
    fontWeight: 400
    lineHeight: "1.65"
  body-sm:
    fontFamily: Inter
    fontSize: 0.875rem
    fontWeight: 400
    lineHeight: "1.5"
  label:
    fontFamily: Inter
    fontSize: 0.6875rem
    fontWeight: 600
    lineHeight: "1.4"
    letterSpacing: "0.08em"
    textTransform: uppercase
  mono:
    fontFamily: "JetBrains Mono"
    fontSize: 0.85rem
    fontWeight: 400
    lineHeight: "1.5"
  mono-label:
    fontFamily: "JetBrains Mono"
    fontSize: 0.75rem
    fontWeight: 500
    lineHeight: "1.4"
    letterSpacing: "0.04em"
    textTransform: uppercase
rounded:
  sm: 6px
  md: 8px
  lg: 12px
  xl: 16px
  pill: 9999px
spacing:
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  2xl: 48px
  3xl: 64px
components:
  button-primary:
    backgroundColor: "{colors.accent}"
    textColor: "#ffffff"
    rounded: "{rounded.sm}"
    padding: 12px
  button-primary-hover:
    backgroundColor: "{colors.accent-hover}"
    textColor: "#ffffff"
  button-secondary:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text-secondary}"
    rounded: "{rounded.sm}"
  button-secondary-hover:
    backgroundColor: "{colors.elevated}"
    textColor: "{colors.ink}"
  input:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.md}"
    padding: 12px
  card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text-secondary}"
    rounded: "{rounded.lg}"
    padding: "{spacing.lg}"
  status-success:
    backgroundColor: "{colors.success-bg}"
    textColor: "{colors.success-text}"
  status-warning:
    backgroundColor: "{colors.warning-bg}"
    textColor: "{colors.warning-text}"
  status-error:
    backgroundColor: "{colors.error-bg}"
    textColor: "{colors.error-text}"
  status-info:
    backgroundColor: "{colors.info-bg}"
    textColor: "{colors.info-text}"
  badge:
    backgroundColor: "{colors.accent-light}"
    textColor: "{colors.accent-hover}"
    rounded: "{rounded.pill}"
  section-label:
    textColor: "{colors.text-muted}"
    typography: "{typography.label}"
  hero-title:
    textColor: "{colors.ink}"
    typography: "{typography.display}"
  hero-subtitle:
    textColor: "{colors.text-secondary}"
    typography: "{typography.body-lg}"
---

## Overview

ReconIQ is a marketing intelligence tool that produces competitive analysis reports. The UI must feel like a precision instrument — not a painted dashboard. Clarity, density, and purpose over decoration.

Inspired by Vercel's shadow-as-border depth system and Linear's surface hierarchy, but adapted for Streamlit's widget constraints and light-mode requirement. Indigo (#5e6ad2) is the sole accent color for interactive elements; all other colors are functional (success, warning, error).

## Colors

- **Primary (#171717):** Deep ink for headings and key text. Near-black, not pure black — the micro-warmth prevents harsh slides and is softer on screens.
- **Tertiary/Accent (#5e6ad2):** Indigo for all interactive highlights — buttons, links, focus rings, progress fills. Never used decoratively.
- **Canvas (#fafafa):** Main background. Warm neutral that prevents the sterile feel of pure white.
- **Panel (#f0f0f5):** Sidebar and panel background. Slightly tinted for visual separation.
- **Surface (#ffffff):** Cards, inputs, elevated content. Pure white as deliberate contrast against canvas.
- **Border (#ebebeb):** Vercel-inspired shadow-as-border surface. In CSS, implemented as `rgba(0,0,0,0.08)` box-shadow rather than a traditional border property.

## Typography

Inter is the primary typeface. Use aggressive negative letter-spacing at display sizes (the Vercel pattern) to create compressed, engineered headlines. Body text reads at comfortable 1.6–1.65 line-height.

Section labels use uppercase small-caps styling (0.6875rem, weight 600, 0.08em tracking) — technical and deliberate, like instrument panel markings.

JetBrains Mono for code, inline monospace, and technical labels (model names, provider identifiers).

## Layout

- Max content width: 960px for the main analysis flow (focused, not sprawling)
- Sidebar locked at 300px with panel background
- Generous vertical rhythm between sections — at least 2rem between major areas
- Module toggles in a single row of 5 checkboxes — compact but scannable
- Report card uses a surface card with shadow-as-border depth

## Elevation & Depth

Follow the Vercel shadow-as-border pattern. Use multi-value box-shadow instead of CSS border where Streamlit allows. Cards use the full shadow stack (border ring + subtle elevation). Status messages use tinted backgrounds with colored left-border accents.

## Shapes

- Buttons: 6px radius (snug, not round)
- Inputs: 8px radius (slightly softer than buttons for input affordance)
- Cards: 12px radius (clearly elevated containers)
- Badges/status pills: 9999px for pill indicators

## Components

Primary button (Analyze) is the single high-emphasis action per screen. Secondary actions (Clear, Download) use bordered ghost buttons. The input field is the visual hero of the page — large, prominent, with indigo focus ring. Checkboxes are Streamlit-native but styled with indigo accent fill. Status dot is a 8px circle with glow for connected state.

Report card wraps markdown output in a surface-elevated container with proper padding and border treatment.

## Do's and Don'ts

### Do

- Use shadow-as-border (`0 0 0 1px rgba(0,0,0,0.08)`) for card borders
- Keep negative letter-spacing on display headings (-0.03em to -0.04em)
- Use uppercase labels for section markers (LLM Provider, Research Modules, Output)
- Keep sidebar locked open — the sidebar collapse button is hidden via CSS + JS
- Hide Streamlit default branding (header, footer, hamburger)
- Let the input field breathe with generous padding and clear focus state
- Use `!important` on Streamlit widget overrides (necessary due to specificity)
- Persist sidebar state via MutationObserver (Streamlit re-renders can collapse it)

### Don't

- Don't add decorative icons or emoji outside the brand marker
- Don't use gradients anywhere (not on buttons, not on backgrounds, not on progress bars)
- Don't add dashboard-style stat cards with fake metrics
- Don't use glassmorphism or frosted-glass effects
- Don't add dark mode toggle (light theme is the design system; dark fights Streamlit)
- Don't use more than one accent color for interactive elements
- Don't widen content beyond 960px for the analysis view
- Don't remove the progress bar during analysis — it provides critical feedback