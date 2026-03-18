# Design Reference — Sasa/Zamani

> Implementation-enforceable design specs distilled from the Design Brief v1.0 (Jessie, Mar 2026).
> This document is for developers. The full Design Brief is for designers.
> When in doubt, the Design Brief is authoritative.
> Last updated: 2026-03-18

## The Single Test

Does it feel like the diagram of something that can't quite be diagrammed?

If it feels like a dashboard, a wellness app, or a productivity tool — it's wrong.

---

## Color Palette

### Ground layer (backgrounds, surfaces)
| Name | Hex | Usage |
|------|-----|-------|
| VOID | #0e0c09 | Page background. Never pure black. |
| SOIL | #1a1510 | Default dark surface |
| DEEP | #0e1614 | Cards, panels. The single cool-dark tone — creates depth |
| PEAT | #2d2416 | Subtle borders |
| BARK | #4a3520 | Warm accent surface |

### Accent layer (interactive, meaningful)
| Name | Hex | Usage |
|------|-----|-------|
| GOLD | #c49a3a | Mythic accent — nodes, active archetypes. Sparingly. Marks significance, not decoration. |
| VIOLET SLATE | #8a8aaa | Liminal accent — links, secondary nodes. Resists categorization. |
| SLATE | #3d5a6a | Deep water — muted UI elements |
| RIVER | #8ab0be | Water surface — hover, atmospheric |

### Light layer (text, selected states)
| Name | Hex | Usage |
|------|-----|-------|
| BONE | #e4e8e4 | Primary text. Cool, lunar, not cream. |
| FROST | #f2f4f0 | Selected/active state only. The thing in focus right now. |

### Participant colors
| Participant | Hex | CSS var |
|-------------|-----|---------|
| Jessie | #7F77DD | --color-jessie |
| Emma | #D85A30 | --color-emma |
| Steven | #1D9E75 | --color-steven |
| Shared | #BA7517 | --color-shared |

### Rules
- Never pure black (#000000) or pure white (#ffffff)
- Never more than three palette colors in a single UI component
- Body copy: BONE at 60-70% opacity — never warm off-white
- Gold is only for significance. If it's decorative, remove it.
- DEEP (#0e1614) for cards/panels — the cool tone creates underwater depth against the warm VOID/SOIL ground

---

## Typography

### Typefaces
| Typeface | Weights | Role |
|----------|---------|------|
| Cormorant Garamond | 300, 300i, 600 | Mythological register: display headings, myth text, pull quotes, archetype names |
| DM Mono | 300, 400 | Data register: interface elements, labels, metadata, timestamps, tags, confidence scores |

### Scale and spacing
| Element | Typeface | Size | Weight | Tracking | Notes |
|---------|----------|------|--------|----------|-------|
| Display heading | Cormorant Garamond | 48px+ | 300 | 0.02em | Let it breathe |
| Archetype name | Cormorant Garamond | 14-20px | 400 (Cinzel in prototype) | — | Primary landmarks, legible at rest |
| Myth text / body | Cormorant Garamond | — | 300i | — | Italic = register of recall, not statement |
| Interface labels | DM Mono | 9-12px | 300-400 | 0.05-0.1em | Clinical, not cold |
| Event names | — | 9-12px | 200i (in prototype) | — | Secondary to archetype names |

### Rules
- Never bold body copy. Weight comes from scale and typeface choice.
- Type sometimes bleeds off panel edges, overlaps images, ignores boundaries. Intentional.
- Pull quotes: large, low opacity, as background texture — word as layer, not label.
- Hierarchy: one Cormorant display line does atmospheric work. DM Mono handles everything read quickly.
- The two typefaces should feel like they belong to different centuries. That friction is the point.

---

## Visual Grammar

### Linework
- Weight: 0.5px–2px, never uniform
- Opacity encodes depth: distant connections 10-15%, near connections 40-60%
- Lines feel simultaneously hand-drawn and instrumentally exact
- Connection lines pass behind text at intersections — depth through overlap
- Lines describing spirals/radial forms feel still-becoming, not finished

### Nodes
- Size encodes significance (archetype instance count or emotional intensity)
- GOLD nodes: active archetypes, mythic weight
- VIOLET SLATE nodes: liminal, uncertain, secondary
- BONE/FROST nodes: currently selected element
- Node glow: faint radial spread at 10-15% opacity, same color as node

### Spatial elements
- One horizon line: full width, 20-30% opacity. Above = alive (sasa). Below = myth (zamani).
- One spiral: deep background, 5-10% opacity, centered. Present but not dominant.
- Meaning-proximity determines spatial layout, not time-proximity

### Atmosphere and texture
- Film grain overlay on all surfaces: 3-5% opacity
- Blur for figures at edge of legibility — long-exposure quality
- Human presence implied, never explicit: silhouette, shadow, hand almost in frame. Never a face.
- Deep negative space is a material, not emptiness. Darkness has weight.
- Foreground elements cast no shadows — depth through overlap and opacity only
- Panel borders fade or break — content continues beyond the frame

---

## Layering (depth hierarchy)

1. **Deepest:** atmospheric photography, grain, the spiral — felt, not seen
2. **Mid-deep:** the constellation — nodes, connection lines, horizon threshold
3. **Mid:** UI panels and cards — dark surfaces, lifted from background
4. **Near:** text — DM Mono data labels and Cormorant myth text at different scales
5. **Surface:** selected/active element — frost-lit, present, in focus

Text bleeds across panel edges. Large display type at low opacity as background texture. Images layer beneath UI, visible through the surface. The further back, the more atmospheric and less legible.

---

## Archetype Glyphs (v3 prototype)

Six SVG sigils, each drawn in character with the archetype's meaning.

| Archetype | Glyph description | Node color |
|-----------|-------------------|------------|
| The Gate (dream) | Bisected portal arch, threshold base line, dot at apex | GOLD |
| What the Body Keeps (body) | Three stacked tide curves, diminishing opacity | RIVER |
| The Table (food) | Eight radial spokes from center dot, peripheral dots | GOLD |
| The Silence (silence) | Single vertical mark, crossbars top/bottom, circle at midpoint | VIOLET SLATE |
| The Root (memory) | Downward fork branching twice, dot at origin | VIOLET SLATE |
| The Hand (writing) | Diagonal directional line with arrowhead, trailing arc | RIVER |

Three scales: large (72px, archetype panel), medium (52px, event panel), small (18px, neighbor list).

---

## Copy Tone

### Register
Ancestral and exact. Never witchy. Never wellness. Never fantasy. A scholar who has spent years inside a subject, now speaking plainly about it to someone they respect.

### Use these words
scaffold, propose, candidate, resonate, vessel, compost, harvest window, rhyme, constellation, intersubjective, meaning-making, narrative commons

### Never use these words
detect, discover, reveal, collective unconscious, synchronicity, universe, field, activation, signal (mystical), journey, transformation (unless earned), powerful, growth, explore, reflect

### Empty states
Not apologies — invitations. "The pattern is still forming" not "Nothing here yet."

### Error states
The system encountered something genuinely unexpected, not "something broke."

### Tonal test
If it sounds like a wellness app, rewrite. If it sounds like a technical manual, rewrite. If it sounds like marginalia in an old book, keep it.

---

## Hard Prohibitions

Never:
- Purple gradients on dark backgrounds
- Glowing neon accents
- Rounded cards with drop shadows
- Sans-serif only (no Cormorant = no mythological register)
- Warm cream or yellow-white for text
- Illustration (fixes the image too precisely)
- Cute, friendly, or rounded icons
- Bounce/spring/playful animations
- Dashboard layouts
- Stars and crescent moons as decoration
- The word "ancient" as visual cue

Always ask:
- Does this feel found rather than made?
- Is human presence implied rather than shown?
- Does the type feel like two different centuries?
- Is there atmosphere in the negative space?
- Does the grain feel like memory?

---

## Reference Points (for implementation mood)

**Visual identity:** Vaughan Oliver / 4AD Records · Fotografiska · Stripe Press · 032c magazine
**Photography:** Francesca Woodman · Hiroshi Sugimoto seascapes · Sally Mann What Remains · La Jetée
**Data viz:** Giorgia Lupi / Accurat · Ramón y Cajal neuron drawings · W.E.B. Du Bois data portraits · Nadieh Bremer
**Ancestral:** Harmonia Macrocosmica · Marshall Islands stick charts · Kongo cosmogram · Lukasa memory board
