// Zod-free so client bundles (e.g. the search box) can import it cheaply.

export type Status = "generated" | "auto_checked" | "human_reviewed";

/** Only checked content is shown or indexed by the app. */
export function isVisible(e: { status: Status }): boolean {
  return e.status === "auto_checked" || e.status === "human_reviewed";
}
