type Point = { timestamp: string; price: number };

type Props = {
  points: Point[];
};

export function StockChart({ points }: Props) {
  if (!points.length) {
    return null;
  }

  const width = 360;
  const height = 120;
  const min = Math.min(...points.map((point) => point.price));
  const max = Math.max(...points.map((point) => point.price));
  const range = max - min || 1;

  const path = points
    .map((point, index) => {
      const x = (index / Math.max(points.length - 1, 1)) * width;
      const y = height - ((point.price - min) / range) * (height - 8) - 4;
      return `${index === 0 ? "M" : "L"}${x.toFixed(2)},${y.toFixed(2)}`;
    })
    .join(" ");

  return (
    <svg className="stock-chart" viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Stock line chart">
      <path d={path} fill="none" stroke="#005fb8" strokeWidth={2} />
    </svg>
  );
}
