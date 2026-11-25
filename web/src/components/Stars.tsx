import { IconStar, IconStarFilled } from "@tabler/icons-react";

import { MAX_STARS } from "../rating";

type Props = { count: number; size?: "sm" | "lg" };

/** Five stars, `count` of them filled. */
export function Stars({ count, size = "lg" }: Props) {
  let box = "size-6";
  if (size === "sm") box = "size-4";
  const stars = [];
  for (let i = 0; i < MAX_STARS; i += 1) {
    if (i < count) {
      stars.push(<IconStarFilled key={i} className={`${box} text-amber-400`} />);
    } else {
      stars.push(<IconStar key={i} className={`${box} text-muted-foreground/40`} />);
    }
  }
  return (
    <div className="flex gap-0.5" role="img" aria-label={`${count} of ${MAX_STARS} stars`}>
      {stars}
    </div>
  );
}
