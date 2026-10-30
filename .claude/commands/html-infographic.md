# HTML Infographic Builder

Build a single-screen, animation-rich HTML infographic that explains one technical concept visually. The output is a fully self-contained `.html` file: one viewport, no scrolling, maximum illustration, minimum words. Same tech stack as html-slides (Inter + Anime.js, dark theme).

## Step 1 — Gather input

Use AskUserQuestion to ask:
1. What concept to explain (e.g. "Apache web server", "CSS selector", "DNS lookup", "what a REST API does")
2. Accent color — suggest `#4FC3F7` (tech blue) as the default. Accept any hex or named color.

If the user already described the concept clearly (e.g. "explain what a CSS selector is"), use that directly and only ask for the accent color. Do not ask questions you already have answers to.

---

## Step 2 — Build the infographic

Save as `[concept-slug].html` in the current working directory (e.g. `css-selector.html`, `apache-server.html`).

---

## Technical stack (do not deviate)

```html
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800;900&display=swap" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/animejs/3.2.1/anime.min.js"></script>
```

## Design tokens

```css
:root {
  --bg: #06080C;
  --text: #F2EEE8;
  --muted: rgba(242,238,232,.4);
  --acc: [accent hex];
  --acc-d: [accent at 10% opacity, e.g. rgba(79,195,247,.10)];
  --bdr: rgba(255,255,255,.07);
}
```

---

## Layout — single screen, no scroll

```css
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body {
  height: 100%;
  overflow: hidden;
  background: var(--bg);
  color: var(--text);
  font-family: 'Inter', sans-serif;
}

body {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 24px 48px;
  gap: 0;
}
```

**Three layout zones (all content must fit within 100vh):**

| Zone | Height | Content |
|------|--------|---------|
| Header | ~10% | Concept category label (muted, uppercase, tiny) + concept title (large, bold) |
| Main illustration | ~78% | Central SVG — the entire explanation lives here |
| Footer | ~12% | Optional key/legend strip — only if the SVG genuinely needs it |

If the infographic does not need a legend, the SVG can take 88% height.

---

## Header

```html
<header>
  <span class="pre-label">HOW IT WORKS</span>
  <h1>CSS Selector</h1>
</header>
```

```css
header { text-align: center; margin-bottom: 16px; }
.pre-label { font-size: 10px; font-weight: 600; letter-spacing: .18em; color: var(--muted); text-transform: uppercase; }
h1 { font-size: clamp(22px, 3vw, 36px); font-weight: 800; margin-top: 4px; }
```

---

## Central SVG — the whole point

The SVG must fill the main zone. Use `width="100%"` and `viewBox` — never fixed pixel width. Set `overflow: visible` on the SVG so labels outside the viewBox boundary don't clip.

**What the SVG must do:**
- Visually represent the concept's structure, flow, or mechanism — not just label boxes
- Use lines, arrows, paths, and shapes to show relationships
- Draw component boxes with subtle fills (`var(--acc-d)` background + `var(--bdr)` border)
- Include connector lines or flow paths between components (styled as dashed animated paths)
- Place short labels (1–3 words) directly on or near each component — never below the SVG in prose

**Choose the layout shape that fits the concept — do not default to left-to-right for everything.**

| Layout | When to use | Examples |
|--------|-------------|---------|
| Left-to-right linear | Sequential steps where order is the point | CI/CD pipeline, git workflow, HTTP lifecycle |
| Hub and spoke | One thing coordinates many | Load balancer, API gateway, server + DB/cache/storage |
| Top-down hierarchy | Parent/child or containment | DNS chain, Docker container→pod→cluster, OSI layers |
| Nested boxes | X contains Y contains Z | Browser → tab → iframe, VM → container → process |
| Before/after split | Transformation or mutation | Minification, encryption, database migration |
| Radial/circular | Cycles or event loops | Node.js event loop, cache invalidation, OAuth flow |

**Concept-specific illustration guidance:**

For **server/network concepts** (Apache, nginx, load balancer, CDN, DNS):
- Draw the chain of components left-to-right: Client → [intermediaries] → Server → Storage
- Use box shapes for each component, icons or abbreviations inside
- Animate arrows along the request path (going right) and response path (going left, different color) — use sequential timeline so request arrows fire before response arrows
- Highlight the key component (the concept being explained) with a stronger glow/accent

For **code/syntax concepts** (CSS selector, regex, SQL query, HTML structure):
- Show a realistic code snippet (monospace font, syntax highlighted in the SVG)
- Use bracket/underline/highlight overlays that sweep across the relevant part of the code
- Show what the code targets — e.g., for a CSS selector, show the matching DOM node highlighting in the HTML tree
- Animate the sweep: a colored overlay animates across the selector, then the matching element highlights

For **process/flow concepts** (HTTP request lifecycle, compile/build pipeline, git workflow):
- Draw a horizontal or vertical flow with labeled stages
- Animate a "packet" or dot that travels through the stages sequentially (loop)
- Each stage box pulses when the dot passes through it

For **data structure concepts** (database table, JSON object, file system tree):
- Draw the structure visually (tree, table, nested boxes)
- Animate read/write operations as sweeping highlights or moving values
- Show before/after states if the concept involves mutation

For **hub concepts** (load balancer, server stack, API gateway):
- Place the key component at center
- Arrange dependencies radially or in a right-side cluster
- Arrows fan out from center to services; response arrows return on a parallel offset path
- Use sequential timeline: inbound request → outbound queries → inbound responses → outbound reply

---

## Positioned node groups — avoid the CSS/SVG transform conflict

When nodes are positioned by an SVG `transform="translate(x,y)"` on the same `<g>` that anime.js animates, the entrance animation silently breaks. Anime.js sets a CSS `transform` property (e.g. `translateY(14px)`) which **overrides** the SVG presentation attribute, collapsing every node to the SVG origin (0,0) — all icons pile up in the top-left corner.

**The fix — always use nested groups:**

```svg
<!-- OUTER group: positions the node. No class — anime.js never touches it. -->
<g transform="translate(340, 120)">
  <!-- INNER group: animation target. No SVG transform attribute. -->
  <g class="ic" opacity="0">
    <!-- draw all node content centered at 0,0 -->
  </g>
</g>
```

With this structure, `translateY` on the inner `.ic` group is safe — it slides relative to the outer group's position rather than fighting it:

```js
anime.set('.ic', { opacity: 0, translateY: 14 });
anime({ targets: '.ic', opacity: 1, translateY: 0, delay: anime.stagger(160), easing: 'easeOutExpo', duration: 650 });
```

If a node needs an `id` for a secondary animation (e.g. a pulse), put it on the **outer** group — descendant selectors reach inside automatically:

```js
// id="key-node" is on the outer <g transform="translate(...)">
anime({ targets: '#key-node circle:first-child', r: [40, 48, 40], easing: 'easeInOutSine', duration: 2800, loop: true });
```

---

## Animation requirements — use all three

### 1. Entrance: staggered fade-in on load

**Always use `window.onload`, never `DOMContentLoaded`.** `window.onload` fires after CDN scripts finish loading, ensuring Anime.js is available. Also use `anime.set` to set the initial hidden state — never use CSS `opacity: 0` on `.ic`, which leaves elements invisible if JS fails.

```js
window.onload = () => {
  if (typeof anime === 'undefined') {
    // CDN failed — show everything immediately as fallback
    document.querySelectorAll('.ic').forEach(el => { el.style.opacity = 1; });
    return;
  }

  anime.set('.ic', { opacity: 0, translateY: 14 });

  anime({
    targets: '.ic',
    opacity: 1,
    translateY: 0,
    delay: anime.stagger(160),
    easing: 'easeOutExpo',
    duration: 650
  });
```

### 2. Flow: animated paths

**Choosing a line style:**

| Style | SVG attributes | Use when |
|-------|---------------|----------|
| Solid line | `stroke-width="2"` | Structural edges, non-animated connectors |
| Dotted line | `stroke-width="2.5" stroke-dasharray="0.1 9" stroke-linecap="round"` | Animated data flow — clearly distinguishable from solid lines |
| Dashed line | `stroke-width="2" stroke-dasharray="6 4"` | Alternative flow style |

Mark animated paths with `class="flow-path"`.

> **Critical: `anime.setDashoffset` destroys dotted patterns.**
> Anime.js's `setDashoffset` helper internally calls `el.setAttribute('stroke-dasharray', pathLength)`, which overwrites the `0.1 9` dot pattern with a solid-line-length dash — making the path look solid during animation. **Never use `strokeDashoffset: [anime.setDashoffset, 0]` with dotted paths.** Use `opacity` animation instead for dotted flow arrows; the arrows fade in rather than draw, which still reads well as a sequential reveal.

**For concepts where all arrows are parallel/independent** (no causal ordering), use opacity with a loop. For dashed (not dotted) paths, `strokeDashoffset` is fine:

```js
  // Dotted paths — opacity loop
  anime({
    targets: '.flow-path',
    opacity: [0, 1, 0],
    easing: 'easeInOutSine',
    duration: 2000,
    loop: true
  });

  // Dashed paths — dashoffset draw (only works without stroke-dasharray dot pattern)
  anime({
    targets: '.flow-path',
    strokeDashoffset: [anime.setDashoffset, 0],
    easing: 'linear',
    duration: 1600,
    loop: true
  });
```

**For concepts with causal ordering** (request/response, pipeline stages) — use a sequential timeline. Arrows accumulate: each phase stays visible as the next appears. Once all phases complete, fade all out together, then restart:

```js
  function arrive(ids, marker) {
    (Array.isArray(ids) ? ids : [ids]).forEach(id => {
      const el = document.querySelector(id);
      if (el) el.setAttribute('marker-end', marker);
    });
  }

  function runFlowCycle() {
    document.querySelectorAll('.flow-path').forEach(el => {
      el.style.opacity = 0;
      el.setAttribute('marker-end', 'none');
    });

    const tl = anime.timeline({
      easing: 'easeOutQuad',
      complete: () => {
        // Hold with all arrows visible, then fade all out together
        setTimeout(() => {
          anime({
            targets: '.flow-path',
            opacity: 0,
            duration: 450,
            easing: 'easeOutQuad',
            complete: () => setTimeout(runFlowCycle, 350)
          });
        }, 900);
      }
    });

    // Phase 1: request arrives
    tl.add({
      targets: '#arrow-req', opacity: [0, 1], duration: 550,
      complete: () => arrive('#arrow-req', 'url(#arr-fwd)')
    });

    // Phase 2: server fans out (staggered, Phase 1 stays visible)
    tl.add({
      targets: ['#arrow-db', '#arrow-cache', '#arrow-storage'],
      opacity: [0, 1], duration: 380, delay: anime.stagger(180),
      complete: () => arrive(['#arrow-db', '#arrow-cache', '#arrow-storage'], 'url(#arr-fwd)')
    });

    // Phase 3: responses return (prior phases stay visible)
    tl.add({
      targets: ['#arrow-db-resp', '#arrow-cache-resp', '#arrow-storage-resp'],
      opacity: [0, 1], duration: 380, delay: anime.stagger(180),
      complete: () => arrive(['#arrow-db-resp', '#arrow-cache-resp', '#arrow-storage-resp'], 'url(#arr-resp)')
    });

    // Phase 4: final output (all previous stay)
    tl.add({
      targets: '#arrow-resp', opacity: [0, 1], duration: 550,
      complete: () => arrive('#arrow-resp', 'url(#arr-resp)')
    });
  }

  setTimeout(runFlowCycle, 1200); // start after entrance animation settles
```

**Arrowhead reveal timing:** Set `marker-end="none"` on all `.flow-path` elements in SVG. Use the `complete` callback to set `marker-end` to the correct marker URL — arrowhead appears only after the shaft is fully visible, never during the fade-in.

**For bidirectional concepts** (request + response, send + receive), use two arrow sets with distinct colors and a footer legend. Request arrows: accent color. Response arrows: muted white (`rgba(242,238,232,.42)`). Define a second SVG marker for the response direction and add a legend strip:

```html
<footer class="legend">
  <span class="legend-item"><span class="dot" style="background:var(--acc)"></span>Request</span>
  <span class="legend-item"><span class="dot" style="background:rgba(242,238,232,.5)"></span>Response</span>
</footer>
```

### 3. Pulse: key component draws attention

```js
  anime({
    targets: '.key-node',     // the central/most important component
    scale: [1, 1.035, 1],
    easing: 'easeInOutSine',
    duration: 2200,
    loop: true
  });
};
```

**Additional animations (use when they improve clarity — not for decoration):**

- **Typewriter effect** — for code-syntax concepts, type the selector/keyword character by character on load
- **Highlight sweep** — a `<rect>` overlay with `opacity` animated from 0→0.25→0 sweeps across a code block to show selection
- **Traveling dot** — for pipeline/flow concepts, an `<circle>` moves along a `<path>` using `anime({ targets, translateX, ... })` with `motionPath` or manual keyframes, looping
- **Counter** — if the concept has a number (e.g. "avg 50ms"), count up from 0 on entrance

---

## Visual rules

- **SVG fills the space.** If it looks small, increase the SVG height or reduce padding.
- **Ambient glow.** Place a `position:absolute` radial-gradient div behind the SVG for depth:
  ```css
  .glow { position: absolute; width: 600px; height: 300px; background: radial-gradient(ellipse, var(--acc-d) 0%, transparent 70%); filter: blur(60px); pointer-events: none; z-index: 0; }
  ```
- **All SVG gradient and filter IDs must be unique** — suffix with a slug derived from the concept (e.g. `serverGlow-apache`, `codeHighlight-css-selector`) to prevent collisions when two infographics are open in the same browser session.
- **SVG arrow markers — always use `markerUnits="userSpaceOnUse"`** — the default `markerUnits="strokeWidth"` multiplies the marker dimensions by the path's stroke-width, making arrowheads on thicker lines disproportionately large. With `userSpaceOnUse` the arrowhead is an absolute size regardless of stroke-width, keeping all arrows visually consistent:
  ```svg
  <marker id="arr-fwd" markerWidth="7" markerHeight="5" refX="6" refY="2.5"
          orient="auto" markerUnits="userSpaceOnUse">
    <path d="M0,0 L0,5 L7,2.5 z" fill="rgba(79,195,247,.7)"/>
  </marker>
  ```
- **Component boxes** use `rx="8"` for rounded corners, `fill="var(--acc-d)"`, `stroke="var(--bdr)"`.
- **Labels** are `<text>` elements inside the SVG, `fill="var(--text)"`, `font-family="Inter"`, `font-size="12"` or `"13"`.
- **Muted secondary labels** use `fill="var(--muted)"` and `font-size="10"`.
- **Accent labels** (the concept name or key term) use `fill="var(--acc)"` and `font-weight="700"`.
- **No emoji. Dark backgrounds only. Never use a light theme.**

---

## Optional: legend strip

Only add a footer legend if the SVG uses color coding that would otherwise be ambiguous:

```html
<footer class="legend">
  <span class="legend-item"><span class="dot" style="background:var(--acc)"></span>Request</span>
  <span class="legend-item"><span class="dot" style="background:#C8A96E"></span>Response</span>
</footer>
```

```css
.legend { display: flex; gap: 24px; margin-top: 12px; }
.legend-item { display: flex; align-items: center; gap: 6px; font-size: 11px; color: var(--muted); letter-spacing: .06em; }
.dot { width: 7px; height: 7px; border-radius: 50%; }
```

If the SVG is self-explanatory from its labels alone, omit the legend entirely.

---

## After building

- Open the file in a browser (start a live-server on a free port if one is not already running).
- Confirm the entire infographic fits in one viewport with no scrolling at 1280×800.
- Confirm all three animation types play on load (entrance, flow arrows, pulse).
- Confirm no SVG element bleeds outside its container.
- Report the local URL where it is being served.
