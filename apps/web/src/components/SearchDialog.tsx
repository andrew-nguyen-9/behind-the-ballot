import { useEffect, useRef, useState, type MouseEvent } from "react";
import {
  PAGEFIND_CSS,
  PAGEFIND_JS,
  isOpenSearchShortcut,
  pagefindUIOptions,
} from "./search";

// Header search island [E0.3]. The ONE hydrating island on non-search pages (client:idle,
// Q3.3) — it keeps the 0-JS-elsewhere posture: a static-looking trigger renders server-side,
// and the Pagefind bundle only loads on first open. The overlay is a native <dialog>, so we
// inherit focus trap, Esc-to-close, and backdrop for free (a11y over hand-rolled JS).

declare global {
  interface Window {
    PagefindUI?: new (options: Record<string, unknown>) => unknown;
  }
}

// Load the build-emitted Pagefind assets once, on first open. Shared promise so repeated
// opens (and a fast ⌘K before paint) don't inject duplicate <script>/<link> tags.
let assetsPromise: Promise<void> | null = null;
function loadPagefind(): Promise<void> {
  if (assetsPromise) return assetsPromise;
  assetsPromise = new Promise<void>((resolve, reject) => {
    if (!document.querySelector(`link[href="${PAGEFIND_CSS}"]`)) {
      const link = document.createElement("link");
      link.rel = "stylesheet";
      link.href = PAGEFIND_CSS;
      document.head.appendChild(link);
    }
    if (window.PagefindUI) {
      resolve();
      return;
    }
    const script = document.createElement("script");
    script.src = PAGEFIND_JS;
    script.addEventListener("load", () => resolve());
    script.addEventListener("error", () => reject(new Error("Failed to load Pagefind")));
    document.head.appendChild(script);
  });
  return assetsPromise;
}

export default function SearchDialog() {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const mountRef = useRef<HTMLDivElement>(null);
  const initialized = useRef(false);
  const [open, setOpen] = useState(false);

  // Global ⌘K / Ctrl+K opener — keyboard-reachable from any page.
  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (isOpenSearchShortcut(event)) {
        event.preventDefault();
        setOpen(true);
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  // Drive the native dialog + lazy-init Pagefind once the overlay first opens.
  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog || !open || dialog.open) return;
    dialog.showModal();
    void loadPagefind()
      .then(() => {
        if (initialized.current || !mountRef.current || !window.PagefindUI) return;
        initialized.current = true;
        new window.PagefindUI(pagefindUIOptions(mountRef.current, { autofocus: true }));
      })
      .catch(() => {
        // Assets 404 in `dev` (Pagefind only runs after `build`); the /search page has the
        // same constraint. Fail quietly rather than throwing in the UI.
      });
  }, [open]);

  const closeDialog = () => dialogRef.current?.close();

  // Native dialogs fire a click on the element itself when the ::backdrop is hit.
  const onDialogClick = (event: MouseEvent<HTMLDialogElement>) => {
    if (event.target === dialogRef.current) closeDialog();
  };

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        aria-haspopup="dialog"
        aria-keyshortcuts="Meta+K Control+K"
        className="inline-flex items-center gap-2 rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-2.5 py-1.5 text-sm text-[var(--color-muted)] transition-colors hover:border-[var(--color-border-strong)] hover:text-[var(--color-brand)]"
      >
        <svg
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.75"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          <circle cx="11" cy="11" r="7" />
          <path d="m21 21-4.3-4.3" />
        </svg>
        <span>Search</span>
        <kbd className="eyebrow ml-1 hidden rounded-sm border border-[var(--color-border)] px-1.5 py-0.5 text-[0.65rem] text-[var(--color-subtle)] sm:inline">
          ⌘K
        </kbd>
      </button>

      <dialog
        ref={dialogRef}
        onClose={() => setOpen(false)}
        onClick={onDialogClick}
        aria-labelledby="search-dialog-title"
        className="mx-auto mt-[10vh] w-[calc(100vw-2rem)] max-w-xl rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-0 text-[var(--color-text)] shadow-[var(--shadow-elev)] backdrop:bg-black/40 backdrop:backdrop-blur-sm"
      >
        <div className="p-5">
          <div className="mb-3 flex items-center justify-between">
            <h2 id="search-dialog-title" className="font-serif text-xl">
              Search
            </h2>
            <button
              type="button"
              onClick={closeDialog}
              aria-label="Close search"
              className="rounded-sm p-1 text-[var(--color-muted)] transition-colors hover:bg-[var(--color-surface-2)] hover:text-[var(--color-brand)]"
            >
              <svg
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.75"
                strokeLinecap="round"
                strokeLinejoin="round"
                aria-hidden="true"
              >
                <path d="M18 6 6 18M6 6l12 12" />
              </svg>
            </button>
          </div>
          <div ref={mountRef} />
        </div>
      </dialog>
    </>
  );
}
