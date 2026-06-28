import { describe, expect, it } from "vitest";
import { cn } from "./utils";

// cn() is the shadcn class-merge: clsx for conditionals, tailwind-merge for conflicts.
describe("cn", () => {
  it("joins truthy classes, drops falsy", () => {
    expect(cn("a", false && "b", "c")).toBe("a c");
  });
  it("later tailwind class wins on conflict", () => {
    expect(cn("px-2", "px-4")).toBe("px-4");
  });
});
