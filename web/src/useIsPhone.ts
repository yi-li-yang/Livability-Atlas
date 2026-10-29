import { useSyncExternalStore } from "react";

/** The widest window, in pixels, that gets the phone layout (docs/specs/2026-10-29-phone-layout.md). */
export const PHONE_MAX_WIDTH = 767;
const QUERY = `(max-width: ${PHONE_MAX_WIDTH}px)`;

function subscribe(notify: () => void): () => void {
  const query = window.matchMedia?.(QUERY);
  query?.addEventListener("change", notify);
  return () => query?.removeEventListener("change", notify);
}

/** Whether the window is narrow enough for the phone layout, and follows it as it is turned or resized. */
export function useIsPhone(): boolean {
  return useSyncExternalStore(
    subscribe,
    () => window.matchMedia?.(QUERY).matches ?? false,
    () => false,
  );
}
