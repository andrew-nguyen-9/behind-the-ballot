import { describe, expect, it } from "vitest";
import {
  PAGEFIND_CSS,
  PAGEFIND_JS,
  isOpenSearchShortcut,
  pagefindUIOptions,
} from "./search";

describe("pagefind asset paths", () => {
  it("point at the build-emitted /pagefind bundle", () => {
    expect(PAGEFIND_JS).toBe("/pagefind/pagefind-ui.js");
    expect(PAGEFIND_CSS).toBe("/pagefind/pagefind-ui.css");
  });
});

describe("pagefindUIOptions", () => {
  it("returns the shared defaults with the given mount element", () => {
    expect(pagefindUIOptions("#el")).toEqual({
      element: "#el",
      showSubResults: true,
      showImages: false,
      autofocus: true,
    });
  });

  it("lets overrides win over the defaults", () => {
    const out = pagefindUIOptions("#el", { autofocus: false, showImages: true });
    expect(out.autofocus).toBe(false);
    expect(out.showImages).toBe(true);
    expect(out.showSubResults).toBe(true);
  });
});

describe("isOpenSearchShortcut", () => {
  it("matches ⌘K (metaKey)", () => {
    expect(isOpenSearchShortcut({ key: "k", metaKey: true })).toBe(true);
  });

  it("matches Ctrl+K", () => {
    expect(isOpenSearchShortcut({ key: "K", ctrlKey: true })).toBe(true);
  });

  it("ignores a bare 'k' with no modifier", () => {
    expect(isOpenSearchShortcut({ key: "k" })).toBe(false);
  });

  it("ignores other modified keys", () => {
    expect(isOpenSearchShortcut({ key: "j", metaKey: true })).toBe(false);
  });
});
