import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import { applyThemeChoice, loadThemeChoice } from "./services/theme";
import "./style.css";

applyThemeChoice(loadThemeChoice()); // before the first paint, so there is no flash

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
