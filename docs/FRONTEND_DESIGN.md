# Design System Document: The Cybernetic Interface

## 1. Overview & Creative North Star: "The Neon Terminal"
This design system rejects the "friendly" corporate web. Our Creative North Star is **The Neon Terminal**—a high-intensity, high-contrast digital environment that feels like a redacted military OS or a black-market hacking deck.

To achieve this, we move beyond standard grids. We embrace **Intentional Asymmetry** and **Aggressive Technicality**. The layout should feel like a heads-up display (HUD), where data is prioritized over decoration. We break the "template" look by using extreme typography scales—pairing massive, condensed display headers with microscopic, hyper-legible data labels. Elements should feel "slotted" into the interface, using hard edges and glowing light-leak effects to simulate a high-end sci-fi screen.

## 2. Colors & Atmospheric Depth
Our palette is rooted in the void. We use deep charcoals and blacks to create a sense of infinite depth, allowing our neon accents to "pierce" the UI.

### The Color Logic
- **Background (`#131315`):** The absolute foundation. Everything emerges from this darkness.
- **Primary / Cyan (`#00f3ff`):** Used for "System Critical" information, active states, and primary data streams.
- **Secondary / Magenta (`#fe00fe`):** Used for "Override" actions, secondary data, and high-energy alerts.
- **Tertiary (`#e4d5ff`):** A muted violet used for background technical data and low-priority system pings.

### Rules of Engagement
- **The "No-Line" Rule:** 1px solid borders are strictly forbidden for sectioning. We define space through background shifts. A `surface-container-low` section sitting on a `surface` background provides all the separation needed.
- **Surface Hierarchy:** To create a "stacked hardware" feel, nest containers using the tiers. A `surface-container-lowest` (`#0e0e10`) panel should host `surface-container-high` (`#2a2a2c`) cards to create a sense of physical modules plugged into a rack.
- **Signature Textures:** Use linear gradients for all primary CTAs, transitioning from `primary` (`#e3fdff`) to `primary_container` (`#00f3ff`). This adds a "charged" energy to interactive elements that flat hex codes cannot replicate.

## 3. Typography: Technical Contrast
The system uses a "Dual-Core" typography strategy to balance editorial sleekness with "hacker-tool" utility.

- **The Display Engine (Space Grotesk):** Our high-tech sans-serif. Used for `display`, `headline`, and `label` roles. It provides a sleek, futuristic geometric feel.
- **The Data Engine (Inter / Mono-styled):** While Inter is our `body` and `title` font, it should be tracked tightly and used in uppercase for titles to mimic a sophisticated terminal.

**Typographic Hierarchy:**
- **Display LG (3.5rem):** Use for hero numbers or section identifiers. Set with -2% letter spacing.
- **Label SM (0.6875rem):** Used for "metadata"—timestamps, coordinates, or system status codes. This is the "fine print" of the machine.

## 4. Elevation & Depth: Tonal Layering
In a world of light and shadow, we do not use traditional drop shadows. We use **Photonic Glow**.

- **The Layering Principle:** Depth is achieved by "stacking" surface-container tiers. For instance, a navigation sidebar should be `surface_container_lowest`, while the main content area is `surface`.
- **Glow Effects:** Instead of shadows, use `primary` and `secondary` colors with a high-spread, low-opacity CSS `box-shadow` or `filter: drop-shadow` to simulate light emitting from the screen.
- **The "Ghost Border":** If a boundary is required for a tight input field, use `outline_variant` (`#3a494b`) at 20% opacity. It should look like a faint etching on a glass screen, never a solid line.
- **Glassmorphism:** Floating modals must use `surface_container_highest` at 60% opacity with a `20px` backdrop-blur. This ensures the "gritty" background data is still visible but diffused behind the active task.

## 5. Components: The Modular Deck

### Buttons
- **Primary:** Gradient fill (`primary` to `primary_container`), `0px` border-radius. Text is `on_primary` (`#00373a`) in all-caps Space Grotesk.
- **Secondary:** Transparent background with a `primary` glow on hover. No border.
- **Tertiary:** `surface_container_highest` background with `secondary` text.

### Progress Bars & Status
- **The "Pulse":** Progress bars use the `primary_fixed` color with a CSS animation that creates a "scanning" light moving across the fill.
- **Indicators:** Status lights (e.g., Online/Offline) must have a 4px blur radius "glow" to simulate a physical LED.

### Input Fields
- **Styling:** Underline-only style using `outline`. On focus, the underline transitions to `primary` with a faint glow.
- **Data Labels:** Labels sit above the input in `label-sm`, using `on_surface_variant` (`#b9cacb`).

### Cards & Lists
- **The Divider Ban:** Never use lines to separate list items. Use a `2.5` (0.5rem) spacing gap or alternate between `surface_container` and `surface_container_low` background colors to create a striped "data-grid" effect.

## 6. Do’s and Don'ts

### Do
- **Do** use `0px` border radius everywhere. Sharp edges represent precision and hardware.
- **Do** lean into monochromatic sections with single-color accents (e.g., an entirely Magenta-themed sub-menu).
- **Do** use `primary_fixed_dim` for non-interactive data to keep the "glow" from becoming overwhelming.

### Don't
- **Don't** use rounded corners. It breaks the "gritty hardware" immersion.
- **Don't** use soft grays. If it’s not a shade of the void (`#131315`) or a glowing neon, it doesn’t belong.
- **Don't** use standard transitions. Use "Step" timing functions or immediate state changes to mimic digital hardware flickers.
