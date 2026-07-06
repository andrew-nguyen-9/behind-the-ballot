// Pure logic behind <ChartReadout> [E-3 Tier 1.1]. Kept separate from the .astro island
// (mirrors partyBar.ts / skeleton.ts) so the readout-extraction + tooltip-clamp maths are
// unit-tested in the node vitest env, no DOM. The island is a hover/keyboard-focus tooltip
// layered over an already-server-rendered chart; these functions carry the only real logic.

export interface Readout {
  label: string;
  value: string;
}

/**
 * Resolve the readout text for a hovered/focused mark. Precedence:
 *   1. explicit `data-readout-label` + `data-readout-value`
 *   2. a `<title>` string (native SVG tooltip), split on the first en/em dash or hyphen-with-
 *      spaces into "label — value"; if no separator, the whole string is the value.
 * Returns null when there is nothing to show (so the caller keeps the tip hidden).
 */
export function readReadout(
  dataset: { label?: string; value?: string },
  titleText?: string,
): Readout | null {
  const label = dataset.label?.trim();
  const value = dataset.value?.trim();
  if (value) return { label: label ?? "", value };
  if (label) return { label: "", value: label };

  const title = titleText?.trim();
  if (!title) return null;
  const m = title.match(/^(.*?)\s+[—–-]\s+(.+)$/);
  if (m) return { label: m[1].trim(), value: m[2].trim() };
  return { label: "", value: title };
}

/**
 * Clamp a tooltip box so it stays fully inside its container. The tip is placed above-right of
 * the pointer by `gap`; when it would overflow an edge it flips/pins to the opposite side.
 * All inputs are container-relative pixels. Pure — no DOM.
 */
export function clampTooltip(
  container: { w: number; h: number },
  pointer: { x: number; y: number },
  tip: { w: number; h: number },
  gap = 12,
): { x: number; y: number } {
  let x = pointer.x + gap;
  if (x + tip.w > container.w) x = pointer.x - gap - tip.w; // flip left
  x = Math.max(0, Math.min(x, Math.max(0, container.w - tip.w)));

  let y = pointer.y - gap - tip.h; // above the pointer
  if (y < 0) y = pointer.y + gap; // no room above → below
  y = Math.max(0, Math.min(y, Math.max(0, container.h - tip.h)));

  return { x, y };
}
