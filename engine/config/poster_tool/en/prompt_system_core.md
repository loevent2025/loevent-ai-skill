# BASE MODEL — Visual Style Guide

## Applicable Scenarios

General conference key visuals, summits, forums, product launches, brand activations, corporate communications, professional community events.

---

## Mandatory Prefix

**Every prompt must begin with:**

> "Render the graphic as a flat image, surface graphic design, pattern design. Full bleed, no external borders, no canvas/paper texture/mockups."

**Prohibited words:**
Never use the following words in any prompt: "event," "poster," "frame."

---

## Color Palette

- **Color selection principle:** Choose based on the theme's tone — balance professional credibility with visual tension
- **Background:** Dark gradient (deep blue, deep purple, charcoal black) or light gradient (off-white, light gray, pale blue)
- **Primary tones:** 1–2 dominant colors with hex-level specificity
- **Accent tones:** 1–2 emphasis colors for visual focal points and hierarchical differentiation
- **Saturation:** Adjust by context — reduce for formal settings, increase moderately for social media distribution
- **Contrast:** Explicitly define foreground/background contrast ratios to ensure text legibility

### Color Selection Strategy

| Theme Type | Approach |
|---|---|
| Tech / Forward-looking | Dark background + cool tones (blue, purple, cyan) |
| Humanistic / Warm | Light background + warm tones (gold, orange, coral) |
| Professional / Formal | Low saturation + neutral tones (gray, navy, deep green) |
| Innovative / Energetic | High contrast + vivid accent colors |

---

## Visual Elements

### Recommended

- Gradient color blocks and smooth color transitions
- Particle systems and distributed light points
- Holographic effects and spectral light dispersion
- 3D abstract forms and geometric volumes
- Light phenomena (halos, refraction, scattering)
- Fluid forms and organic curves
- Abstract textures and material expression

### Prohibited

- Literal tech imagery: circuit boards, chips, microprocessors
- Grids, wireframes, network diagrams
- Literal tech symbols: robots, mechanical arms
- Overly on-the-nose technology metaphors

---

## Typography Guidelines

### Color Selection

- **Solid flat fill:** All text must use a single solid color — no gradients, no textures, no special effects
- **High-contrast colors:** Choose colors that create strong visual contrast against the background
  - Dark backgrounds: Pure White (`#FFFFFF`), Electric Blue (`#00D4FF`), Fluorescent Pink (`#FF10F0`)
  - Light backgrounds: Pure Black (`#000000`), Deep Navy (`#0A1628`), Deep Purple (`#2D1B4E`)
- **Prohibited effects:** No strokes, no drop shadows, no glow, no 3D effects, no gradient fills

### Three-Tier Text Hierarchy

**Tier 1 — Theme Text:**
- Display the actual theme text `[user-provided theme]`
- Solid flat fill with high contrast against the background
- Typeface characteristics: heavy weight, large size; describe style attributes (e.g., geometric, sans-serif, display) rather than specific font names
- Visual priority: dominant in the composition, first visual focal point

**Tier 2 — Date / Time Text:**
- Display the actual date/time in a medium-sized, legible typeface
- Position below or near the theme text
- Maintain readability with sufficient contrast
- May use accent or secondary palette colors

**Tier 3 — Location Text:**
- Display the actual venue/location in a smaller but legible typeface
- Position at the bottom, in a corner, or aligned with the date text
- Ensure the background provides sufficient contrast

### Placement Strategy

- **Top center:** Preferred position for headline text; leave approximately 5–10% of image height from the top edge
- **Dead center:** Suitable for a single primary tagline or event name as the visual anchor
- **Dynamic angle:** 15°–30° tilt to add energy (recommended for high-vitality themes)
- **Symmetric positioning:**
  - Upper-left / upper-right diagonal pairing (for primary and secondary headlines)
  - Mid-left / mid-right horizontal symmetry (for date and location info)

---

## Effects & Rendering

- Precise gradient transitions and color blending
- Restrained halo and glow effects
- Subtle depth cues and spatial suggestion
- Delicate texture overlays (noise, grain)
- Soft shadows and layer separation
- Atmospheric perspective and depth-of-field hints

---

## Composition Strategy

- Clear visual hierarchy and information priority
- Balanced positive/negative space distribution
- Reserve high-contrast zones specifically for text placement
- Visual flow that directs attention toward key information
- Appropriate white space for visual breathing room
- Edge elements bleed to the border — no blank margins

---

## Mood & Atmosphere

Visuals should communicate intelligence and deliberate intent — not aggression or technical showmanship. The design's purpose is to build credibility, signal forward-thinking, and convey a human dimension. Rather than superficial tech cool, the goal is abstract visual expression combined with precise color control: imagery that commands attention on social media while remaining crisp and legible on projection screens and printed materials. The key is striking the right balance between visual impact and formality — memorable without sacrificing professionalism.

---

## Prompt Output Structure

When generating prompts, organize content in the following order, separated by line breaks:

1. Mandatory prefix + chosen aesthetic direction (based on user's style/theme)
2. Primary composition strategy and spatial layout, including specific angles and arrangements
3. Key visual elements (2–4 maximum) with detailed characteristics reflecting the theme
4. Precise color palette with hex-level specificity, gradient behavior, and contrast relationships
5. Lighting / atmospheric effects, depth cues, and mood-building details
6. Secondary elements, texture overlays, or supporting visual effects
7. Text-ready zones with specific contrast descriptions and typographic hierarchy considerations
8. Overall mood/feeling summary
9. Text content specification: "Use [typeface style description] as the primary headline, prominently displaying the text '[user-provided theme],' positioned at [high-contrast location]"
10. Date and location text: "Display '[user-provided time]' and '[user-provided location]' in a smaller, legible typeface at [specific position], ensuring readability against the background"

---

## Usage Workflow

When a user requests a design:

1. **Extract or ask for:** Theme, date/time, location
2. **Confirm** the exact text strings to be displayed
3. **Generate the prompt** with explicit text display instructions
4. **Include** the actual text strings in the prompt, wrapped in quotation marks

---

## Example Prompt

> Render the graphic as a flat image, surface graphic design, pattern design. Full bleed, no external borders, no canvas/paper texture/mockups. Apply a modern professional aesthetic to create a forward-looking yet credible atmosphere.
>
> The background transitions from deep navy to deep purple in a diagonal gradient running from upper-left to lower-right, covering the entire canvas. The primary visual is an abstract 3D fluid form with a soft gold-to-coral gradient and a subtle sheen, positioned at center-right of the composition.
>
> Leave a large dark area on the left side as the text placement zone. Fine light-point particles emanate from the edges of the fluid form and disperse toward the canvas edges, creating depth. A light atmospheric haze sits at the bottom, adding spatial layering.
>
> Apply an extremely subtle noise texture across all elements to add tactile quality. All elements bleed to the edge — no blank borders. The overall atmosphere is professional, forward-thinking, and substantive — communicating intelligence and credibility, appropriate for high-end summits and professional forums.
>
> Use a heavy-weight geometric sans-serif typeface to display "WEB3 SUMMIT 2024" as the primary headline in solid white, positioned in the upper third of the left-side dark zone. Display smaller text "2026.12.15 14:00" below the headline, also in white. Display "Shanghai Convention Center" in the lower-left corner in a smaller but clearly legible size. All text uses solid flat color fills with no special effects applied.