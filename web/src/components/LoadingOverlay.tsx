import { BrainLoader } from "./BrainLoader";

/** A dimmed layer over the whole page with the filling brain in the middle. Shown only while a
 *  brain loads. It is a status for screen readers; the page behind it cannot be clicked. */
export function LoadingOverlay({ text }: { text: string }) {
  return (
    <div className="overlay" role="status" aria-live="polite">
      <div className="overlay-card">
        <BrainLoader size={140} />
        <p>{text}</p>
      </div>
    </div>
  );
}
