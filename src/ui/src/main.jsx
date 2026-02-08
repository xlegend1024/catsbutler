import React from "react";
import { createRoot } from "react-dom/client";
import { FluentProvider, webLightTheme } from "@fluentui/react-components";
import App from "./App.jsx";
import "./App.css";

const theme = {
  ...webLightTheme,
  fontFamilyBase: '"Space Grotesk", "Segoe UI", sans-serif',
};

createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <FluentProvider theme={theme}>
      <App />
    </FluentProvider>
  </React.StrictMode>
);
