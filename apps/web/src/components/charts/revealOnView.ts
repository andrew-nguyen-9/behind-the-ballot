// Pure logic behind <RevealOnView> [E-3 Tier 1.3]. The island animates content from an
// initial hidden state to its final state the first time it scrolls into view
// (IntersectionObserver), reduced-motion → final state instantly, no-JS → final state rendered
// directly (the pre-reveal state is only ever applied by the script). These helpers decide
// *whether* to arm and compute the per-item stagger; the .astro script wires the observer.

/** True when the user has not asked to reduce motion (i.e. it is safe to animate). */
export function prefersReducedMotion(mql: { matches: boolean } | null): boolean {
  return mql?.matches === true;
}

/**
 * Arm the reveal animation only when both are true: motion is allowed and the environment can
 * detect entering the viewport. Otherwise the caller must leave content in its final state.
 */
export function shouldArm(opts: {
  reducedMotion: boolean;
  supportsObserver: boolean;
}): boolean {
  return !opts.reducedMotion && opts.supportsObserver;
}

/**
 * Staggered delay (ms) for the i-th revealed item: `i * step`, capped at `max` so long lists
 * never crawl. Negative/NaN indices floor to 0.
 */
export function staggerDelay(index: number, step = 60, max = 360): number {
  const i = Number.isFinite(index) ? Math.max(0, Math.floor(index)) : 0;
  return Math.min(i * step, max);
}
