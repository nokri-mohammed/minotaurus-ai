// The shortest plain explanation of each label the page shows. Used by the info tooltips.
const GLOSSARY: Record<string, string> = {
  // Recipe: mazes
  Sizes: "The maze widths it practised on.",
  Piles: "Mazes in 3 sets: practice to learn, quiz to pick the best version, exam to score it.",
  "Maze seed": "A number that makes the same random mazes every time.",
  Exit: "Where the exit is placed.",
  Levels: "The hand-made levels it trained on.",
  // Recipe: brain
  Method: "How it learns: a table (Q-table) or a neural network (DQN).",
  Network: "The size of each layer of the neural network.",
  Seed: "A number that makes training repeatable.",
  "Wall mask": "Stops it walking into walls it can see.",
  // Recipe: learning
  "Learning rate": "How big each learning step is. Too big makes it unstable.",
  "Batch size": "How many past moves it learns from at once.",
  Discount: "How much later rewards count. Near 1 means it plans ahead.",
  Memory: "How many past moves it keeps to learn from.",
  "Target update": "How often its steady copy of the network is refreshed.",
  // Recipe: exploring, rewards, training
  "Random moves": "How often it tries a random move while learning. It falls over time.",
  Shaping: "Small rewards for getting closer to the exit.",
  "Novelty bonus": "A reward for stepping on a new square.",
  "Revisit penalty": "A penalty for stepping on the same square again.",
  Tries: "How many mazes it played while training.",
  Quiz: "How often it takes the quiz to check its progress.",
  "Early stop": "Training stops when the quiz score stops improving.",
  // Recipe: result
  "Quiz (validation)": "Score on quiz mazes it did not train on. Picks the best version.",
  "Exam (test)": "Score on exam mazes it never saw. The honest score.",
  "Portal levels": "How many hand-made Arena levels it finished.",
  "Route length": "Steps taken divided by the shortest route. 1.00 is perfect.",
  // Brain rating
  Completed: "Levels where it reached the exit.",
  "Total steps": "Steps added up over the levels it finished.",
  "Hand-made": "Finished levels among the hand-made ones.",
  "Test mazes": "Finished levels among the test mazes.",
  "Game time": "Steps times 0.1 s, for finished levels.",
  "Average steps": "Total steps divided by the levels finished.",
  Stars: "Each star is about 20% of the levels finished.",
  // Tables
  Exam: "Score on exam mazes it never saw.",
  "Run all levels": "Levels finished when played one after another.",
  "Exam mazes": "Which exam set the score is from. Compare only equal sets.",
  Steps: "Moves the brain made.",
  Time: "Game time: steps times 0.1 s.",
  Route: "Steps taken divided by the shortest route.",
  Group: "Hand-made levels or generated test mazes.",
};

/** The tooltip text for a label, or null when there is none. */
export function tipFor(label: string): string | null {
  const text = GLOSSARY[label];
  if (text === undefined) return null;
  return text;
}

export function glossaryLabels(): string[] {
  return Object.keys(GLOSSARY);
}
