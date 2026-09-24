/**
 * Plain-hex mirror of the CSS custom properties in index.css, for Recharts
 * fill/stroke/tooltip props — those render as raw SVG attributes, where
 * CSS variables aren't reliably resolved across browsers.
 */
export const CHART_COLORS = {
  background: "#0D0D0F",
  surface: "#141417",
  border: "#232326",
  accent: "#38BDF8",
  accentLight: "#7DD3FC",
  positive: "#4ADE80",
  warning: "#F59E0B",
  negative: "#F87171",
  muted: "#8B8C90",
  text: "#E7E8EA",
} as const;
