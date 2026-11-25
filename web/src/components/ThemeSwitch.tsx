import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { ICON_SIZE, iconFor } from "../themeIcons";
import { THEME_CHOICES, isThemeChoice, type ThemeChoice } from "../theme";

type Props = { value: ThemeChoice; onChange: (choice: ThemeChoice) => void };

/** A dot-matrix picture; the dots take the CSS text colour. */
function DotIcon({ choice }: { choice: ThemeChoice }) {
  const rows = iconFor(choice);
  const dots = [];
  for (let y = 0; y < rows.length; y += 1) {
    for (let x = 0; x < rows[y].length; x += 1) {
      if (rows[y][x] === "#") {
        dots.push(<circle key={`${x}-${y}`} cx={x + 0.5} cy={y + 0.5} r={0.38} />);
      }
    }
  }
  return (
    <svg viewBox={`0 0 ${ICON_SIZE} ${ICON_SIZE}`} aria-hidden="true" fill="currentColor">
      {dots}
    </svg>
  );
}

/** Three positions (Dark, System, Light): a knob slides to the chosen one and its name shows below. */
export function ThemeSwitch({ value, onChange }: Props) {
  let index = 0;
  let label = "";
  for (let i = 0; i < THEME_CHOICES.length; i += 1) {
    if (THEME_CHOICES[i].id === value) {
      index = i;
      label = THEME_CHOICES[i].label;
    }
  }
  return (
    <div className="tswitch" data-choice={value}>
      <RadioGroup
        aria-label="Theme"
        orientation="horizontal"
        value={value}
        onValueChange={(id) => {
          if (isThemeChoice(id)) onChange(id);
        }}
        className="tswitch-track"
      >
        <span className="tswitch-knob" style={{ transform: `translateX(${index * 100}%)` }} aria-hidden="true">
          <DotIcon choice={value} />
        </span>
        {THEME_CHOICES.map((choice) => (
          <RadioGroupItem key={choice.id} value={choice.id} aria-label={choice.label} className="tswitch-slot">
            <DotIcon choice={choice.id} />
          </RadioGroupItem>
        ))}
      </RadioGroup>
      <span className="tswitch-label">{label}</span>
    </div>
  );
}
