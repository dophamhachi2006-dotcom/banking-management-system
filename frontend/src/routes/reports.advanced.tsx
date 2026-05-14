import { useMemo } from "react";
import {
  TransactionHeatmap, MoneyFlowSankey, NetworkGraph,
  type HeatmapDatum, type SankeyNode, type SankeyLink,
  type NetNode, type NetLink,
} from "@/components/charts";

const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

function genHeatmap(): HeatmapDatum[] {
  const out: HeatmapDatum[] = [];
  for (const d of DAYS) for (let h = 0; h < 24; h++) {
    const peak = h >= 9 && h <= 17 ? 60 : 15;
    out.push({ day: d, hour: h, count: Math.floor(Math.random() * peak) });
  }
  return out;
}

function genSankey(): { nodes: SankeyNode[]; links: SankeyLink[] } {
  const nodes: SankeyNode[] = [
    { name: "Branch 01" }, { name: "Branch 02" }, { name: "Branch 03" },
    { name: "Savings" }, { name: "Checking" }, { name: "Loans" },
  ];
  const links: SankeyLink[] = [
    { source: 0, target: 3, value: 120 },
    { source: 0, target: 4, value: 80 },
    { source: 1, target: 3, value: 200 },
    { source: 1, target: 5, value: 60 },
    { source: 2, target: 4, value: 150 },
    { source: 2, target: 5, value: 90 },
  ];
  return { nodes, links };
}

function genNetwork(): { nodes: NetNode[]; links: NetLink[] } {
  const nodes: NetNode[] = Array.from({ length: 12 }, (_, i) =>
    ({ id: `C${i + 1}`, group: i % 4 }));
  const links: NetLink[] = [];
  for (let i = 0; i < 18; i++) {
    const a = Math.floor(Math.random() * 12);
    let b = Math.floor(Math.random() * 12);
    if (b === a) b = (b + 1) % 12;
    links.push({ source: `C${a + 1}`, target: `C${b + 1}`, value: 1 + Math.random() * 4 });
  }
  return { nodes, links };
}

export function AdvancedReportsPage() {
  const heatmap = useMemo(genHeatmap, []);
  const sankey = useMemo(genSankey, []);
  const network = useMemo(genNetwork, []);

  return (
    <div className="p-6 space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-emerald-700">Advanced Analytics</h1>
        <p className="text-sm text-muted-foreground">
          D3-powered visualizations: heatmap, money-flow sankey, customer network.
        </p>
      </div>

      <section className="rounded-xl border bg-white p-4 shadow-sm overflow-x-auto">
        <h2 className="font-semibold mb-2">Transaction Heatmap</h2>
        <TransactionHeatmap data={heatmap} />
      </section>

      <section className="rounded-xl border bg-white p-4 shadow-sm overflow-x-auto">
        <h2 className="font-semibold mb-2">Money Flow (Branches → Account Types)</h2>
        <MoneyFlowSankey nodes={sankey.nodes} links={sankey.links} />
      </section>

      <section className="rounded-xl border bg-white p-4 shadow-sm overflow-x-auto">
        <h2 className="font-semibold mb-2">Customer Relationship Network</h2>
        <NetworkGraph nodes={network.nodes} links={network.links} />
      </section>
    </div>
  );
}

export default AdvancedReportsPage;
