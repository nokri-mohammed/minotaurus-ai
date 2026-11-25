import { IconStar, IconStarFilled } from "@tabler/icons-react";

import { MAX_STARS, ratingOf } from "../rating";
import { shortId } from "../brainOptions";
import type { BatchResult, BrainInfo } from "../protocol";
import { Panel } from "./Panel";
import { Stat } from "./Stat";

type Props = { brain: BrainInfo | null; batch: BatchResult | null; working: boolean };

function Stars({ count }: { count: number }) {
  const stars = [];
  for (let i = 0; i < MAX_STARS; i += 1) {
    if (i < count) {
      stars.push(<IconStarFilled key={i} className="size-6 text-amber-400" />);
    } else {
      stars.push(<IconStar key={i} className="size-6 text-muted-foreground/40" />);
    }
  }
  return (
    <div className="flex gap-1" role="img" aria-label={`${count} of ${MAX_STARS} stars`}>
      {stars}
    </div>
  );
}

/** The brain's rating: stars for the share of levels finished, with the totals behind them. */
export function RatingPanel({ brain, batch, working }: Props) {
  let note = "Load a brain to rate it.";
  if (brain) note = `${brain.name} (${shortId(brain.id)})`;
  if (!batch) {
    let empty = "Load a brain first.";
    if (working) empty = "Rating the brain on every level...";
    else if (brain) empty = "Press Run all levels to rate this brain.";
    return (
      <Panel title="Brain rating" note={note}>
        <p className="empty">{empty}</p>
      </Panel>
    );
  }
  const rating = ratingOf(batch);
  const failed = [];
  if (rating.timedOut > 0) failed.push(`${rating.timedOut} timed out`);
  if (rating.stuck > 0) failed.push(`${rating.stuck} stuck`);
  if (rating.errors > 0) failed.push(`${rating.errors} failed`);
  let average = "–";
  if (rating.averageSteps !== null) average = rating.averageSteps.toFixed(1);
  return (
    <Panel title="Brain rating" note={note}>
      <div className="flex flex-col gap-4">
        <div className="flex items-center gap-3">
          <Stars count={rating.stars} />
          <span className="text-sm text-muted-foreground">{rating.percent}%</span>
        </div>
        <div className="stats">
          <Stat label="Completed" value={String(rating.finished)} unit={`of ${rating.total} levels`} />
          <Stat label="Total steps" value={String(rating.steps)} unit="steps" note="finished levels" />
          <Stat label="Hand-made" value={`${rating.handMade.finished}/${rating.handMade.total}`} />
          <Stat label="Test mazes" value={`${rating.test.finished}/${rating.test.total}`} />
          <Stat label="Game time" value={rating.seconds.toFixed(1)} unit="s" note="finished levels" />
          <Stat label="Average steps" value={average} unit="per level" />
        </div>
        {failed.length > 0 && <p className="muted">Not finished: {failed.join(", ")}.</p>}
      </div>
    </Panel>
  );
}
