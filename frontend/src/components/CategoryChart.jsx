import { useRef, useEffect, useCallback } from 'react';
import { formatDecimalAmount } from '../utils.js';

// Layout constants (logical pixels)
const ROW_HEIGHT = 40;
const PADDING_TOP = 16;
const PADDING_BOTTOM = 16;
const LABEL_WIDTH = 120;
const VALUE_LABEL_PAD = 8;
const BAR_VERTICAL_PAD = 8;
const EMPTY_HEIGHT = 80;
// Estimated max width consumed by value label text (e.g. "–$5000.00")
const VALUE_LABEL_EST_WIDTH = 80;

/**
 * CategoryChart — F6.
 *
 * Draws a horizontal bar chart on a <canvas> element using the Canvas 2D API
 * (no chart library). One bar per category, coloured green (income) or red
 * (expense). Redraws on every prop change and on every container resize.
 * Supports HiDPI / Retina displays via devicePixelRatio scaling.
 *
 * @prop {Array<{category: string, total: string}>} categoryTotals
 *   Pre-sorted array from GET /summary/categories (descending by total).
 */
export default function CategoryChart({ categoryTotals }) {
  const canvasRef = useRef(null);
  // Keep a ref to the latest totals so the ResizeObserver closure always
  // reads current data, not the stale value captured on first render.
  const totalsRef = useRef(categoryTotals);
  useEffect(() => {
    totalsRef.current = categoryTotals;
  });

  /** Read a CSS variable from the canvas element, falling back to a hex literal. */
  function cssVar(canvas, name, fallback) {
    const val = getComputedStyle(canvas).getPropertyValue(name).trim();
    return val || fallback;
  }

  /** Draw the chart onto the canvas. */
  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const currentTotals = totalsRef.current;
    const dpr = window.devicePixelRatio || 1;
    const logicalWidth = Math.max(canvas.parentElement ? canvas.parentElement.offsetWidth : 300, 300);

    if (currentTotals.length === 0) {
      // Empty state
      const logicalHeight = EMPTY_HEIGHT;
      canvas.width = logicalWidth * dpr;
      canvas.height = logicalHeight * dpr;
      canvas.style.width = `${logicalWidth}px`;
      canvas.style.height = `${logicalHeight}px`;

      const ctx = canvas.getContext('2d');
      ctx.scale(dpr, dpr);
      ctx.clearRect(0, 0, logicalWidth, logicalHeight);
      ctx.fillStyle = cssVar(canvas, '--color-muted', '#64748b');
      ctx.font = '14px system-ui, sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText('No transactions yet', logicalWidth / 2, logicalHeight / 2);
      return;
    }

    const n = currentTotals.length;
    const logicalHeight = ROW_HEIGHT * n + PADDING_TOP + PADDING_BOTTOM;
    canvas.width = logicalWidth * dpr;
    canvas.height = logicalHeight * dpr;
    canvas.style.width = `${logicalWidth}px`;
    canvas.style.height = `${logicalHeight}px`;

    const ctx = canvas.getContext('2d');
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, logicalWidth, logicalHeight);

    const colorIncome = cssVar(canvas, '--color-income', '#16a34a');
    const colorExpense = cssVar(canvas, '--color-expense', '#dc2626');
    const colorText = cssVar(canvas, '--color-text', '#1e293b');
    const colorMuted = cssVar(canvas, '--color-muted', '#64748b');
    const colorBorder = cssVar(canvas, '--color-border', '#e2e8f0');

    // Bar area x-origin and available width
    const barAreaX = LABEL_WIDTH;
    const barAreaWidth = logicalWidth - LABEL_WIDTH - VALUE_LABEL_PAD - VALUE_LABEL_EST_WIDTH;

    /** Convert a Decimal string (e.g. "-150.50") to its absolute value in integer cents. */
    function absCents(s) {
      const abs = s.startsWith('-') ? s.slice(1) : s;
      const [ip, fp = ''] = abs.split('.');
      return parseInt(ip, 10) * 100 + parseInt(fp.padEnd(2, '0').slice(0, 2), 10);
    }

    // Max absolute total for proportional scaling (integer cents, no float)
    const maxAbsTotal = Math.max(...currentTotals.map((d) => absCents(d.total)));

    for (let i = 0; i < n; i++) {
      const { category, total } = currentTotals[i];
      const isExpense = total.startsWith('-');
      const valueCents = absCents(total);

      const rowY = PADDING_TOP + i * ROW_HEIGHT;
      const barY = rowY + BAR_VERTICAL_PAD;
      const barHeight = ROW_HEIGHT - 2 * BAR_VERTICAL_PAD;
      const barWidth = maxAbsTotal > 0 ? barAreaWidth * (valueCents / maxAbsTotal) : 0;

      // Background track
      ctx.fillStyle = colorBorder;
      ctx.fillRect(barAreaX, barY, barAreaWidth, barHeight);

      // Coloured bar
      ctx.fillStyle = isExpense ? colorExpense : colorIncome;
      ctx.fillRect(barAreaX, barY, barWidth, barHeight);

      // Category label (left, vertically centred in row)
      ctx.fillStyle = colorText;
      ctx.font = '14px system-ui, sans-serif';
      ctx.textAlign = 'left';
      ctx.textBaseline = 'middle';
      // Clip label to LABEL_WIDTH - small margin
      ctx.save();
      ctx.beginPath();
      ctx.rect(0, rowY, LABEL_WIDTH - 4, ROW_HEIGHT);
      ctx.clip();
      ctx.fillText(category, 4, rowY + ROW_HEIGHT / 2);
      ctx.restore();

      // Value label (right of bar)
      ctx.fillStyle = colorMuted;
      ctx.font = '12px system-ui, sans-serif';
      ctx.textAlign = 'left';
      ctx.textBaseline = 'middle';
      ctx.fillText(formatDecimalAmount(total), barAreaX + barWidth + VALUE_LABEL_PAD, rowY + ROW_HEIGHT / 2);
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Redraw when data changes
  useEffect(() => {
    draw();
  }, [categoryTotals]); // eslint-disable-line react-hooks/exhaustive-deps

  // Attach ResizeObserver once; redraw on resize
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !canvas.parentElement) return;

    const observer = new ResizeObserver(() => {
      draw();
    });
    observer.observe(canvas.parentElement);
    return () => observer.disconnect();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <canvas
      ref={canvasRef}
      role="img"
      aria-label="Category spending breakdown chart"
      style={{ display: 'block', width: '100%' }}
    />
  );
}
