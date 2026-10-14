# Chart & Breakdown Design — CategoryChart.jsx + CategoryBreakdown.jsx

## Overview

This document specifies the design for two companion components:

- **`CategoryChart.jsx`** — a horizontal bar chart drawn entirely with the Canvas 2D API (no library).
- **`CategoryBreakdown.jsx`** — a summary table of aggregated category totals fetched from `GET /summary/categories`.

Both components receive the same `categoryTotals` prop (an array of `{ category: string, total: string }` objects, amounts serialised as Decimal strings) already sorted descending by the backend. Neither component fetches data independently; `App.jsx` owns the fetch and passes data down.

---

## Data Contract

### Prop shape (shared by both components)

```
categoryTotals: Array<{ category: string, total: string }>
```

`total` is a Decimal-serialised string (e.g. `"5000.00"`, `"-150.50"`). Positive values represent net income for that category; negative values represent net expense. The array arrives pre-sorted by `total` descending (highest positive first).

### Backend endpoint

```
GET /api/summary/categories
Authorization: Bearer <token>
→ 200 OK  [{ "category": "Salary", "total": "5000.00" }, ...]
→ 200 OK  []   (empty — no transactions yet)
```

---

## Component: `CategoryChart.jsx`

### Responsibilities

1. Allocate and size a `<canvas>` element that always matches the logical pixel density of the display (HiDPI support).
2. Draw one horizontal bar per category, coloured by sign (income / expense).
3. Label each bar with the category name on the left and the formatted amount on the right.
4. Re-draw on every prop change and every window resize.
5. Render a visible empty-state message when `categoryTotals` is empty or all-zero.

### Props

| Prop | Type | Required | Description |
|---|---|---|---|
| `categoryTotals` | `Array<{category: string, total: string}>` | yes | Pre-sorted array from the API |

JSDoc block required per project standard (Rule 2).

### Canvas sizing and HiDPI

The canvas must always render at the device's physical pixel density to avoid blurry text and bars on Retina / high-DPI displays.

**Algorithm:**

1. Read `window.devicePixelRatio` (DPR), defaulting to `1` if absent.
2. Set `canvas.width = logicalWidth * DPR` and `canvas.height = logicalHeight * DPR`.
3. Set `canvas.style.width = logicalWidth + 'px'` and `canvas.style.height = logicalHeight + 'px'` so CSS layout is unaffected.
4. Call `ctx.scale(DPR, DPR)` once before drawing so all coordinates remain in logical pixels.

**Logical dimensions:**

- `logicalWidth` = the canvas element's `offsetParent` / container width, clamped to a minimum of `300px`. Read this at draw time, not at mount, so resize works correctly.
- `logicalHeight` = `ROW_HEIGHT * n + PADDING_TOP + PADDING_BOTTOM` where `n` is the number of categories.

Suggested constants (values are design-time suggestions; implementation may tune):

| Constant | Value | Purpose |
|---|---|---|
| `ROW_HEIGHT` | 40px | Height allocated per category row |
| `PADDING_TOP` | 16px | Space above the first bar |
| `PADDING_BOTTOM` | 16px | Space below the last bar |
| `LABEL_WIDTH` | 120px | Reserved left column for category name |
| `VALUE_LABEL_PAD` | 8px | Gap between bar end and value text |
| `BAR_VERTICAL_PAD` | 8px | Top/bottom inset within each row to give bars breathing room |

### Layout geometry

For each row `i`:

```
rowY        = PADDING_TOP + i * ROW_HEIGHT
barY        = rowY + BAR_VERTICAL_PAD
barHeight   = ROW_HEIGHT - 2 * BAR_VERTICAL_PAD
barAreaX    = LABEL_WIDTH
barAreaWidth = logicalWidth - LABEL_WIDTH - VALUE_LABEL_PAD - estimated value label width
barWidth    = barAreaWidth * (|total| / maxAbsTotal)
```

The category name is drawn left-aligned at `(4, rowY + ROW_HEIGHT / 2)` (vertically centred in the row). The value label is drawn left-aligned just after the bar end: `(barAreaX + barWidth + VALUE_LABEL_PAD, rowY + ROW_HEIGHT / 2)`.

When `maxAbsTotal === 0` (all totals are zero), all bars have `barWidth = 0`; the empty-state path fires instead.

### Colour scheme

Match the project's existing CSS variables:

| Condition | Colour | Hex |
|---|---|---|
| `total >= 0` (income) | `--color-income` | `#16a34a` |
| `total < 0` (expense) | `--color-expense` | `#dc2626` |

Use `getComputedStyle(canvas).getPropertyValue('--color-income')` to read the CSS variable at draw time, so the colours respond to any future theming changes. Fall back to the hex literals if the variable is not set (e.g. in a test environment where `getComputedStyle` is mocked).

### Text rendering

- Category label: `14px system-ui, sans-serif`, `--color-text` (`#1e293b`), `textBaseline: 'middle'`
- Value label: `12px system-ui, sans-serif`, `--color-muted` (`#64748b`), `textBaseline: 'middle'`
- Bar background track: `--color-border` (`#e2e8f0`) full-width strip behind each bar to indicate the bar area

### Empty state

When `categoryTotals.length === 0`:

1. Draw nothing except a centred message string: `"No transactions yet"`.
2. Set canvas height to a fixed minimum (e.g. `80px` logical) so it does not collapse to zero.
3. Use `--color-muted` text, `14px system-ui`.

### Resize handling

Attach a `ResizeObserver` (preferred) or a `window` `'resize'` event listener inside `useEffect`. On each resize event, call the draw function again. The draw function re-reads `offsetWidth` at draw time so dimensions are always fresh.

Clean up the observer / listener in the `useEffect` cleanup function to prevent memory leaks.

### Amount parsing for chart math

The `total` strings are Decimal values. For the purpose of computing bar proportions only, `parseFloat(total)` is acceptable — the resulting float is used solely for a ratio calculation, not for display. Displayed values must use integer-cent arithmetic (see Value Label Formatting below).

### Value label formatting

Reuse the same integer-cent arithmetic pattern established in `TransactionList.jsx` and `BalanceDisplay.jsx`:

1. Strip any leading `-` to get the absolute string.
2. Split on `.` to get integer part and fractional part.
3. Compute `cents = intPart * 100 + paddedFracPart`.
4. Reconstruct as `$dollars.cents` with `centsRemainder` zero-padded to 2 digits.
5. Prepend `–` (en-dash) for negative totals.

This avoids `parseFloat` / `toFixed` for display and prevents any floating-point representation artefacts in labels.

### React integration

```
useRef  → holds the <canvas> DOM node
useEffect(drawFn, [categoryTotals])  → redraws on prop change
useEffect(setupResizeObserver, [])   → attach / detach resize listener (runs once)
```

The two `useEffect` calls are separate so the resize observer is attached exactly once and does not re-register on every data update.

### Accessibility

Add `role="img"` and `aria-label="Category spending breakdown chart"` to the `<canvas>` element so screen readers can identify the region even though Canvas content is not accessible.

---

## Component: `CategoryBreakdown.jsx`

### Responsibilities

1. Render a two-column HTML table of category → formatted total.
2. Visually distinguish positive (income) rows from negative (expense) rows.
3. Handle the empty state when `categoryTotals` is empty.
4. Accept the same prop as `CategoryChart` so `App.jsx` can pass `categoryTotals` once to both.

### Props

| Prop | Type | Required | Description |
|---|---|---|---|
| `categoryTotals` | `Array<{category: string, total: string}>` | yes | Pre-sorted array from the API |

JSDoc block required per project standard (Rule 2).

### Table structure

```html
<table class="tx-table">
  <thead>
    <tr>
      <th>Category</th>
      <th class="tx-table__amount-col">Total</th>
    </tr>
  </thead>
  <tbody>
    <tr class="tx-row tx-row--income">   <!-- or tx-row--expense -->
      <td><span class="tx-row__category">Salary</span></td>
      <td class="tx-row__amount tx-row__amount--income">$5,000.00</td>
    </tr>
    ...
  </tbody>
</table>
```

Reuse the existing `.tx-table`, `.tx-row`, `.tx-row--income`, `.tx-row--expense`, and `.tx-row__category` CSS classes from `main.css` so the table is visually consistent with `TransactionList.jsx`.

### Row classification

- Row gets class `tx-row--income` when `parseFloat(total) >= 0`.
- Row gets class `tx-row--expense` when `parseFloat(total) < 0`.

`parseFloat` is used here only for the class decision, not for display. Display uses integer-cent arithmetic.

### Amount formatting

Same integer-cent arithmetic as described for the chart value labels. Extract the helper into a shared module or duplicate the function — do not use `parseFloat().toFixed()` for display.

### Empty state

When `categoryTotals.length === 0`, render a single-row table body (or a `<p>`) with the text `"No categories yet"` styled with `color: var(--color-muted)`.

---

## Shared Formatting Utility

Both components need to format Decimal strings as dollar amounts. Rather than duplicating code, a small utility function should be co-located or placed in a shared file:

```
formatDecimalAmount(totalStr: string) → string
```

**Behaviour:**
- Input: `"5000.00"` → Output: `"$5000.00"`
- Input: `"-150.50"` → Output: `"–$150.50"` (en-dash prefix, not minus)
- Uses integer-cent arithmetic — no `parseFloat` / `toFixed` in the result path.

The exact file location (inline in each component, or a new `src/utils.js`) is an implementation decision, but the function must not be duplicated with different logic in each component.

---

## CSS Additions Required

The following new CSS rules are needed to support both components. They extend `main.css` without changing existing rules:

| Selector | Purpose |
|---|---|
| `.chart-panel canvas` | Ensure canvas is `display: block` (removes inline-block gap) and `width: 100%` |
| `.chart-panel__empty` | Centred muted text for the empty state |
| `.tx-table__amount-col` | Right-align the Total column header |
| `.tx-row__amount` | Right-align the amount cell; `font-variant-numeric: tabular-nums` for aligned decimals |
| `.tx-row__amount--income` | `color: var(--color-income)` |
| `.tx-row__amount--expense` | `color: var(--color-expense)` |

---

## Layout Placement in App.jsx

Both components already receive `categoryTotals` as a prop in the existing `App.jsx` design. They are rendered inside the summary panel (row 2, column 1 of the CSS Grid layout). The recommended stacking order within that panel is:

1. `<BalanceDisplay />` (already implemented)
2. `<CategoryChart />` — visual overview
3. `<CategoryBreakdown />` — precise numbers table

This order gives users a visual overview first, then the exact figures below it.

---

## Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Chart type | Horizontal bars | Categories are nominal — horizontal layout gives room for long labels |
| Bar scale | Proportional to absolute value | Negative and positive totals must be comparable in length |
| Colour signal | Green income / red expense | Consistent with existing `--color-income` / `--color-expense` CSS variables |
| HiDPI technique | DPR scale + CSS override | Standard Canvas pattern; keeps all draw coordinates in logical pixels |
| Resize strategy | ResizeObserver on canvas parent | More efficient than window resize; fires only when this element changes |
| Empty state | Inline text on canvas / table row | No external component needed; keeps each component self-contained |
| Amount display | Integer-cent arithmetic | Project-wide standard per BalanceDisplay and TransactionList |
| Shared formatter | Single utility function | Avoids divergent formatting logic between chart labels and table cells |
| Data ownership | App.jsx fetches, passes down | Consistent with existing pattern; avoids duplicate fetch calls |
| Sort order | Delegated to API | Backend already returns descending by total; no client sort needed |
