import { useEffect, useRef } from "react";
import * as d3 from "d3";

export interface HeatmapDatum {
  hour: number;   // 0..23
  day: string;    // "Mon", "Tue", ...
  count: number;
}

const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

export function TransactionHeatmap({ data }: { data: HeatmapDatum[] }) {
  const ref = useRef<SVGSVGElement | null>(null);

  useEffect(() => {
    if (!ref.current) return;
    const svg = d3.select(ref.current);
    svg.selectAll("*").remove();

    const margin = { top: 40, right: 30, bottom: 50, left: 60 };
    const width = 820 - margin.left - margin.right;
    const height = 360 - margin.top - margin.bottom;
    const g = svg.append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);

    const hours = d3.range(0, 24).map(String);
    const x = d3.scaleBand().domain(hours).range([0, width]).padding(0.05);
    const y = d3.scaleBand().domain(DAYS).range([0, height]).padding(0.05);
    const max = d3.max(data, d => d.count) || 1;
    const color = d3.scaleSequential(d3.interpolateGreens).domain([0, max]);

    g.selectAll("rect")
      .data(data)
      .join("rect")
      .attr("x", d => x(String(d.hour)) || 0)
      .attr("y", d => y(d.day) || 0)
      .attr("width", x.bandwidth())
      .attr("height", y.bandwidth())
      .attr("rx", 3)
      .attr("fill", d => color(d.count))
      .append("title")
      .text(d => `${d.day} ${d.hour}:00 — ${d.count} tx`);

    g.append("g")
      .attr("transform", `translate(0,${height})`)
      .call(d3.axisBottom(x).tickSize(0))
      .selectAll("text").style("font-size", "11px");
    g.append("g").call(d3.axisLeft(y).tickSize(0));

    svg.append("text")
      .attr("x", (width + margin.left + margin.right) / 2)
      .attr("y", 22)
      .attr("text-anchor", "middle")
      .style("font-size", "14px").style("font-weight", 600)
      .style("fill", "#0d7a5f")
      .text("Transaction Heatmap (Hour × Day)");
  }, [data]);

  return <svg ref={ref} width={820} height={360} />;
}
