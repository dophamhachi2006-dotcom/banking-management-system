import { useEffect, useRef } from "react";
import * as d3 from "d3";
import { sankey, sankeyLinkHorizontal, SankeyGraph } from "d3-sankey";

export interface SankeyNode { name: string }
export interface SankeyLink { source: number; target: number; value: number }

export function MoneyFlowSankey({
  nodes, links,
}: { nodes: SankeyNode[]; links: SankeyLink[] }) {
  const ref = useRef<SVGSVGElement | null>(null);

  useEffect(() => {
    if (!ref.current || !nodes.length) return;
    const svg = d3.select(ref.current);
    svg.selectAll("*").remove();

    const width = 900, height = 480;
    const sk = sankey<SankeyNode, SankeyLink>()
      .nodeWidth(18).nodePadding(14)
      .extent([[1, 1], [width - 1, height - 5]]);

    const graph: SankeyGraph<SankeyNode, SankeyLink> = sk({
      nodes: nodes.map(n => ({ ...n })),
      links: links.map(l => ({ ...l })),
    });

    svg.append("g").attr("fill", "none").attr("stroke-opacity", 0.4)
      .selectAll("path")
      .data(graph.links)
      .join("path")
      .attr("d", sankeyLinkHorizontal())
      .attr("stroke", "#0d7a5f")
      .attr("stroke-width", d => Math.max(1, d.width || 1));

    svg.append("g")
      .selectAll("rect")
      .data(graph.nodes)
      .join("rect")
      .attr("x", d => d.x0!)
      .attr("y", d => d.y0!)
      .attr("height", d => d.y1! - d.y0!)
      .attr("width", d => d.x1! - d.x0!)
      .attr("fill", "#c9a84c");

    svg.append("g").style("font-size", "11px")
      .selectAll("text")
      .data(graph.nodes)
      .join("text")
      .attr("x", d => (d.x0! < width / 2 ? d.x1! + 6 : d.x0! - 6))
      .attr("y", d => (d.y1! + d.y0!) / 2)
      .attr("dy", "0.35em")
      .attr("text-anchor", d => (d.x0! < width / 2 ? "start" : "end"))
      .text(d => d.name);
  }, [nodes, links]);

  return <svg ref={ref} width={900} height={480} />;
}
