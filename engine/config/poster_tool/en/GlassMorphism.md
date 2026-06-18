# GLASSMORPHISM GRADIENT — Design Style Guide

---

## Intended Use Cases

Conference invitations, event announcements, professional presentations, developer forums, summit materials, business conference name cards, corporate communications.

---

## Signature Color Palette

| Gradient | Color Stops |
|----------|------------|
| **Gradient A** | Orange (`#FF6B4A`) → Pink (`#FF8FB9`) → Light Blue (`#A8D8FF`) → Blue (`#6BA3FF`) |
| **Gradient B** | Pink (`#FFB3E6`) → Purple (`#B794F6`) → Blue (`#7B9BFF`) → Deep Blue (`#4A5FFF`) |
| **Background** | Light gray-white (`#F5F7FA`) with gradient overlay |
| **Primary Text** | Black (`#1A1A1A`) |
| **Secondary Text** | Dark gray (`#4A4A4A`) |
| **Glass Effect** | Semi-transparent white at 15–25% opacity with backdrop blur |

**Defining Characteristics:** Multi-color diagonal gradients · Glassmorphism effects · Soft blur · Solid-fill typography · Minimal and modern

---

## Visual Elements

### Glassmorphism Design

- **Glass Cards:** Semi-transparent frosted glass effect; white at 15–25% opacity
- **Backdrop Blur:** 20–40px Gaussian blur behind each card
- **Border:** 1px semi-transparent white border (30–40% opacity)
- **Shadow:** Soft, subtle shadow — `0 8px 32px rgba(0,0,0,0.08)`
- **Border Radius:** 16–24px rounded corners for a modern feel
- **Layering:** Multiple glass cards may be stacked to add spatial depth

### Typography System

- **Headline Style:** Extra-bold geometric sans-serif; solid color fill
- **Font Family:** Modern geometric sans-serif — Inter, Montserrat, or Poppins
- **Logo / Wordmark:** Extra-bold; large scale (60–80pt); solid color fill
- **Body Copy:** Regular-weight sans-serif (16–20pt)
- **Hierarchy:** Clear size contrast — Primary Heading → Subheading → Body → Footer
- **Alignment:** Left-aligned or centered; clean, consistent spacing
- **Color:** Pure black (`#1A1A1A`) or pure white (`#FFFFFF`); single color only

### Background Gradients

- **Direction:** Diagonal gradient (45° or custom angle)
- **Color Stops:** 4–6 stops; transitions from warm to cool tones
- **Blending:** Smooth transitions between colors; no harsh banding
- **Overlay:** Optional subtle texture or grid pattern at 2–5% opacity
- **Variation:** Each card may use a different gradient direction or color palette

### Card Layout

- **Card Structure:** Rounded glass cards housing event information
- **Padding:** 24–40px internal padding; generous white space
- **Content Blocks (top to bottom):** Logo → Title → Name card → Date/Time → Venue → Sponsors
- **Nested Cards:** Smaller cards within the main card for specific details (e.g., invitee name)
- **Spacing:** 16–24px between content blocks

---

## Effects & Treatment

### Glass Texture

- **Material:** Frosted glass with subtle transparency
- **Blur Intensity:** 20–40px Gaussian blur applied to background
- **Opacity Layer:** 15–25% white overlay for the glass effect
- **Reflection:** Optional subtle light reflection at card edges
- **Depth:** Multiple layered cards create spatial hierarchy

### Gradient Light Effects

- **Soft Glow:** Diffused light radiating into the background
- **Color Blending:** Smooth transitions with no visible banding
- **Luminosity:** Brighter at the gradient center; darker toward edges
- **Atmosphere:** Gradient + blur combination creates a dreamy, ethereal quality
- **Contrast:** Light background paired with dark text ensures readability

### Decorative Details

- **Grid Overlay:** Optional subtle grid pattern (2–3% opacity) for a technology aesthetic
- **Icons:** Minimal monochrome icons for sponsor logos and brand marks
- **Micro-interactions:** Increased brightness on hover states (for digital media)
- **Texture:** Very subtle noise or grain (2–4% opacity) for a premium feel

---

## Composition Strategy

### Card-Based Layout

- **Card Positioning:** Centered or side-by-side comparative layout
- **Proportion:** Cards occupy 70–80% of the frame; ample breathing room remains
- **Alignment:** Precise grid-based alignment throughout
- **Balance:** Symmetric or asymmetric depending on content needs
- **Margins:** 10–15% margin around each card

### Information Hierarchy

| Level | Content | Visual Weight | Area |
|-------|---------|--------------|------|
| **Level 1** | Event title / Logo | Largest; extra-bold; solid fill | 25–30% |
| **Level 2** | Invitee name card | Prominent nested card | 20–25% |
| **Level 3** | Date, time, venue | Clear body text | 15–20% |
| **Level 4** | Sponsor logos | Footer zone; subdued | 10–15% |
| **Negative Space** | Breathing room | — | 20–30% |

### Visual Flow

- **Reading Order:** Top-to-bottom, left-to-right
- **Primary Focus:** Extra-bold weight draws the eye first
- **Secondary Focus:** Name card with contrasting treatment
- **Supporting Info:** Date and venue easily scannable
- **Footer:** Sponsor logos understated but visible

---

## Typography Rules

**Color:** Choose a solid color with high contrast against the glass card or background:
- On light glass cards → Pure black (`#1A1A1A`) or dark gray (`#333333`)
- On dark areas or over gradients → Pure white (`#FFFFFF`)

**Fill Method:** Solid color fill only — single color, no gradients

**Strictly Prohibited Effects:**
- Outlined / stroked text
- Outer glow or inner glow
- Drop shadow or text shadow
- Gradient fill on text
- Opacity effects on text
- Any other text special effects

**Guiding Principle:** Typography must remain clean, legible, and high-contrast. Visual impact is achieved through extra-bold weight and scale hierarchy — consistent with the modern, minimal aesthetic of glassmorphism design.

---

## Mood & Tone

Modern professional · Premium quality · Soft elegance · Futuristic minimalism · Refined · Clean corporate aesthetic · Approachable luxury · Technology-forward · Community-focused · International business style

---

## Design References

Apple iOS design language · Windows Fluent Design · Modern UI/UX trends · Glassmorphism design systems · Gradient backgrounds in technology branding · Dribbble glass card designs · Behance premium invitation design

---

## Technical Specifications

| Property | Specification |
|----------|--------------|
| **Resolution** | Social media: 1080×1350px; Print: 2480×3508px (A4) at 300 DPI |
| **Color Space** | Digital: RGB; Print: CMYK |
| **Design Tools** | Figma or Adobe XD for UI design; Photoshop for final rendering |
| **Glass Effect** | CSS `backdrop-filter` or Photoshop blur + opacity layers |
| **Gradients** | Linear or radial gradient with multiple color stops |
| **Export Format** | PNG for transparency; PDF for print-ready files |

---

## Reference Prompts

### Full Version

Render as flat image, surface graphic design, pattern design. Full bleed to edges; no external borders, no canvas texture, no mockups. Glassmorphism conference invitation design with modern gradient aesthetic; intended for a developer forum and professional event announcement.

Diagonal multi-color gradient background with smooth transitions: left card uses Orange (`#FF6B4A`) → Pink (`#FF8FB9`) → Light Blue (`#A8D8FF`) → Blue (`#6BA3FF`); right card uses Pink (`#FFB3E6`) → Purple (`#B794F6`) → Blue (`#7B9BFF`) → Deep Blue (`#4A5FFF`). 4–6 color stops; smooth blending; soft ambient feel. Light gray-white (`#F5F7FA`) base with gradient overlay. Optional subtle grid texture at 3% opacity for a technology aesthetic.

Centered semi-transparent frosted glass card (70–80% of frame); 20px border radius. Glass effect: 20% white opacity overlay with 30–40px backdrop blur. 1px semi-transparent white border (35% opacity). Soft shadow beneath card: `0 10px 30px rgba(0,0,0,0.08)`. 32px internal padding.

Top zone: "LOGO" label and event title in extra-bold geometric sans-serif (Montserrat Black or equivalent; 64pt). **Pure black (`#1A1A1A`) solid color fill — single color; no outline, no stroke, no glow, no shadow, no gradient, no text effects of any kind.** Event name "crypto 2024" treated identically with solid fill. Below: "Global Development Forum" in regular black text (18pt); **same solid fill, no effects**.

Middle zone: Nested frosted glass card (slightly more opaque — 25% white) with rounded corners; contains the invitee's name. "China Community Manager" label (14pt) above bold black name "JEFFREY" (40pt). Optional "Invite →" button in the corner.

Bottom zone: Bold black date and time (20pt) — "April 24, 2023, at 9:00 AM". Regular text for venue details (16pt). Footer: Monochrome sponsor logos arranged horizontally (12–16px height each).

24px spacing between content blocks. Clear hierarchy; generous negative space (25% of card area). Modern, professional, minimal aesthetic. Very subtle noise texture (3% opacity) for a premium quality feel.

Style references: Apple iOS glassmorphism, Windows Fluent Design, modern UI/UX card design, Dribbble premium invitations, technology conference branding. Technical: Figma/Adobe XD UI design aesthetic, `backdrop-filter` blur effect, 1080×1350px or A4 print dimensions, 300 DPI, RGB color space.

Mood: Modern professional · Premium quality · Soft elegance · Futuristic minimalism · Refined · Clean corporate aesthetic · Approachable luxury · Technology-forward · Community-focused · International business style.

---

### Condensed Version

Render as flat image, surface graphic design, pattern design. Full bleed to edges; no external borders, no canvas texture, no mockups. Glassmorphism invitation card. Diagonal gradient background in orange-pink-blue or pink-purple-blue; smooth 5-stop transitions. Semi-transparent frosted glass card (75% of frame; 20px border radius; 22% white opacity; 35px backdrop blur; 1px white border). Event title in extra-bold geometric sans-serif (64pt); **pure black solid fill — no outline, no stroke, no effects**. Nested card for invitee name. Supporting details in black text. Sponsor logo footer. 28px padding; clean spacing. Modern, minimal, professional aesthetic.

---

### Ultra-Minimal Version

Render as flat image, surface graphic design, pattern design. Full bleed to edges; no external borders, no canvas texture, no mockups. Glass card invitation. Multi-color gradient background. Semi-transparent frosted card. **Extra-bold solid-fill text — no effects**. Black text. Minimal and modern.