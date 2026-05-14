import { useEffect, useRef } from "react";
import * as d3 from "d3";

export interface NetNode { id: string; group?: number }
export interface NetLink { source: string; target: string; value?: number }

export function NetworkGraph({
  nodes, links,
}: { nodes: NetNode[]; links: NetLink[] }) {
  const ref = useRef<SVGSVGElement | null>(null);

  useEffect(() => {
    if (!ref.current) return;
    const svg = d3.select(ref.current);
    svg.selectAll("*").remove();

    const width = 800, height = 500;
    const sim = d3.forceSimulation(nodes as any)
      .force("link", d3.forceLink(links as any).id((d: any) => d.id).distance(80))
      .force("charge", d3.forceManyBody().strength(-180))
      .force("center", d3.forceCenter(width / 2, height / 2));

    const link = svg.append("g").attr("stroke", "#999").attr("stroke-opacity", 0.6)
      .selectAll("line").data(links).join("line")
      .attr("stroke-width", (d: any) => Math.sqrt(d.value || 1));

    const color = d3.scaleOrdinal(d3.schemeTableau10);
    const node = svg.append("g").attr("stroke", "#fff").attr("stroke-width", 1.5)
      .selectAll("circle").data(nodes).join("circle")
      .attr("r", 8)
      .attr("fill", (d: any) => color(String(d.group ?? 0)))
      .call(d3.drag<any, any>()
        .on("start", (e: any, d: any) => { if (!e.active) sim.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; })
        .on("drag",  (e: any, d: any) => { d.fx = e.x; d.fy = e.y; })
        .on("end",   (e: any, d: any) => { if (!e.active) sim.alphaTarget(0); d.fx = null; d.fy = null; }));

    node.append("title").text((d: any) => d.id);

    sim.on("tick", () => {
      link.attr("x1", (d: any) => d.source.x).attr("y1", (d: any) => d.source.y)
          .attr("x2", (d: any) => d.target.x).attr("y2", (d: any) => d.target.y);
      node.attr("cx", (d: any) => d.x).attr("cy", (d: any) => d.y);
    });

    return () => { sim.stop(); };
  }, [nodes, links]);

  return <svg ref={ref} width={800} height={500} />;
}
