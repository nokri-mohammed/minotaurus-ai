import { useState } from "react";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { type MazeDifficulty, MAZE_DIFFICULTIES, defaultSizeFor, parseSeed, sizesFor } from "../randomMaze";
import type { RandomMazeRequest } from "../protocol";
import { Button } from "./Button";
import { InfoTip } from "./InfoTip";
import { Panel } from "./Panel";
import { Select } from "./Select";

type Props = {
  working: boolean;
  disabled: boolean;
  onGenerate: (request: RandomMazeRequest) => void;
};

const DIFFICULTY_OPTIONS = [
  { id: "easy", label: "Easy" },
  { id: "medium", label: "Medium" },
  { id: "hard", label: "Hard" },
];

/** Pick a difficulty and a size, then Generate: a fresh random maze to watch the brain on. */
export function RandomMazePanel({ working, disabled, onGenerate }: Props) {
  const [difficulty, setDifficulty] = useState<MazeDifficulty>("easy");
  const [size, setSize] = useState<number>(defaultSizeFor("easy"));
  const [exitInWall, setExitInWall] = useState(false);
  const [randomStart, setRandomStart] = useState(false);
  const [seedText, setSeedText] = useState("");

  const seed = parseSeed(seedText);
  const sizeOptions = [];
  for (const option of sizesFor(difficulty)) {
    sizeOptions.push({ id: String(option), label: `${option} x ${option}` });
  }

  function pickDifficulty(id: string) {
    for (const known of MAZE_DIFFICULTIES) {
      if (known === id) {
        setDifficulty(known);
        setSize(defaultSizeFor(known));
      }
    }
  }

  function generate() {
    if (seed === null) return;
    const request: RandomMazeRequest = { size, random_start: randomStart, border_exit: exitInWall };
    if (seed !== undefined) request.seed = seed;
    onGenerate(request);
  }

  return (
    <Panel title="Random maze" note="A fresh maze to watch the brain on. It is not scored or saved.">
      <div className="flex flex-col gap-3">
        <div className="actions">
          <Select label="Difficulty" value={difficulty} options={DIFFICULTY_OPTIONS} onChange={pickDifficulty} disabled={working} />
          <Select label="Size" value={String(size)} options={sizeOptions} onChange={(id) => setSize(Number(id))} disabled={working} />
          <div className="field">
            <Label htmlFor="random-seed" className="flex items-center gap-1">
              Seed (optional)
              <InfoTip label="Maze seed" />
            </Label>
            <Input
              id="random-seed"
              inputMode="numeric"
              placeholder="random"
              value={seedText}
              onChange={(event) => setSeedText(event.target.value)}
              aria-invalid={seed === null}
              className="w-28"
              disabled={working}
            />
          </div>
        </div>
        <div className="flex flex-wrap gap-x-6 gap-y-2">
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={exitInWall} onChange={(event) => setExitInWall(event.target.checked)} disabled={working} />
            Exit in the outer wall
            <InfoTip label="Exit in the outer wall" />
          </label>
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={randomStart} onChange={(event) => setRandomStart(event.target.checked)} disabled={working} />
            Random start
            <InfoTip label="Random start" />
          </label>
        </div>
        {seed === null && <p role="alert" className="problem">The seed is a whole number from 0 to 999999, or empty.</p>}
        <div className="actions">
          <Button variant="primary" onClick={generate} disabled={disabled || working || seed === null}>
            {working ? "Generating..." : "Generate"}
          </Button>
        </div>
      </div>
    </Panel>
  );
}
