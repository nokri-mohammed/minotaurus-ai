/** Wait for `work`, but never give the result back sooner than `ms` after the start.
 *  Used so a loading animation that would only flash is seen. A failure waits too. */
export async function atLeast<T>(work: Promise<T>, ms: number): Promise<T> {
  const started = Date.now();
  try {
    return await work;
  } finally {
    const left = ms - (Date.now() - started);
    if (left > 0) {
      await new Promise<void>((resolve) => setTimeout(resolve, left));
    }
  }
}
