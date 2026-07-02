// Theme resolution for the manual light/dark toggle [E0.2]. Pure helpers so the logic is
// unit-tested; the no-FOUC <head> script in Layout.astro inlines the same rules (it can't
// import — it must run before first paint), and the toggle island imports from here.
export type Theme = "light" | "dark";

// Which theme to render on load: an explicit stored pref wins, else follow the OS.
export function resolveInitialTheme(
  stored: string | null | undefined,
  prefersDark: boolean,
): Theme {
  if (stored === "light" || stored === "dark") return stored;
  return prefersDark ? "dark" : "light";
}

// 2-state toggle [Q2.2].
export function nextTheme(current: Theme): Theme {
  return current === "dark" ? "light" : "dark";
}

// theme-color meta per active theme: light = brand green, dark = app background,
// matching the pre-toggle prefers-color-scheme metas.
export const THEME_COLOR: Record<Theme, string> = {
  light: "#0b6e4f",
  dark: "#0a0f14",
};
