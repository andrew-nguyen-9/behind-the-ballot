import { describe, expect, it } from "vitest";
import { nextTheme, resolveInitialTheme, THEME_COLOR } from "./theme";

describe("resolveInitialTheme", () => {
  it("honours a stored dark preference over the system setting", () => {
    expect(resolveInitialTheme("dark", false)).toBe("dark");
  });

  it("honours a stored light preference over the system setting", () => {
    expect(resolveInitialTheme("light", true)).toBe("light");
  });

  it("follows the system when there is no stored preference", () => {
    expect(resolveInitialTheme(null, true)).toBe("dark");
    expect(resolveInitialTheme(null, false)).toBe("light");
  });

  it("ignores a garbage stored value and follows the system", () => {
    expect(resolveInitialTheme("purple", true)).toBe("dark");
    expect(resolveInitialTheme("", false)).toBe("light");
  });
});

describe("nextTheme", () => {
  it("toggles between the two states", () => {
    expect(nextTheme("light")).toBe("dark");
    expect(nextTheme("dark")).toBe("light");
  });
});

describe("THEME_COLOR", () => {
  it("maps each theme to its meta theme-color", () => {
    expect(THEME_COLOR.light).toBe("#0b6e4f");
    expect(THEME_COLOR.dark).toBe("#0a0f14");
  });
});
