import { useEffect, useRef } from "react";
import { useQuery } from "@tanstack/react-query";
import * as d3 from "d3";
import styles from "./GraphView.module.css";

interface GraphNode {
  id: string;
  risk_score: number;
  status: string;
  x?: number;
  y?: number;
  fx?: number | null;
  fy?: number | null;
}

interface GraphEdge {
  source: string | GraphNode;
  target: string | GraphNode;
  weight: number;
}

interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

async function fetchGraph(): Promise<GraphData> {
  const res = await fetch("/api/graph");
  if (!res.ok) throw new Error("failed to fetch graph");
  return res.json();
}

function nodeColor(riskScore: number) {
  if (riskScore >= 0.8) return "#ef4444";
  if (riskScore >= 0.5) return "#f59e0b";
  return "#6366f1";
}

export function GraphView() {
  const svgRef = useRef<SVGSVGElement>(null);
  const { data, isLoading } = useQuery({
    queryKey: ["graph"],
    queryFn: fetchGraph,
    refetchInterval: 15000,  // refresh the graph every 15 seconds
  });

  useEffect(() => {
    if (!data || !svgRef.current) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();  // clear before redrawing

    const width = svgRef.current.clientWidth;
    const height = svgRef.current.clientHeight;

    // zoom and pan support
    const g = svg.append("g");
    svg.call(
      d3.zoom<SVGSVGElement, unknown>().on("zoom", (event) => {
        g.attr("transform", event.transform);
      })
    );

    const simulation = d3.forceSimulation<GraphNode>(data.nodes)
      .force("link", d3.forceLink<GraphNode, GraphEdge>(data.edges)
        .id((d) => d.id)
        .distance(60)
      )
      .force("charge", d3.forceManyBody().strength(-80))
      .force("center", d3.forceCenter(width / 2, height / 2));

    // draw edges
    const link = g.append("g")
      .selectAll("line")
      .data(data.edges)
      .join("line")
      .attr("stroke", "#2a2d3a")
      .attr("stroke-width", (d) => Math.min(d.weight, 3));

    // draw nodes
    const node = g.append("g")
      .selectAll<SVGCircleElement, GraphNode>("circle")
      .data(data.nodes)
      .join("circle")
      .attr("r", 6)
      .attr("fill", (d) => nodeColor(d.risk_score))
      .attr("stroke", "#0f1117")
      .attr("stroke-width", 1.5)
      .call(
        d3.drag<SVGCircleElement, GraphNode>()
          .on("start", (event, d) => {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
          })
          .on("drag", (event, d) => {
            d.fx = event.x;
            d.fy = event.y;
          })
          .on("end", (event, d) => {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
          })
      );

    // tooltip on hover
    node.append("title").text((d) => `${d.id}\nrisk: ${d.risk_score.toFixed(2)}\nstatus: ${d.status}`);

    simulation.on("tick", () => {
      link
        .attr("x1", (d) => (d.source as GraphNode).x ?? 0)
        .attr("y1", (d) => (d.source as GraphNode).y ?? 0)
        .attr("x2", (d) => (d.target as GraphNode).x ?? 0)
        .attr("y2", (d) => (d.target as GraphNode).y ?? 0);

      node
        .attr("cx", (d) => d.x ?? 0)
        .attr("cy", (d) => d.y ?? 0);
    });

    return () => {
      simulation.stop();
    };
  }, [data]);

  if (isLoading) return <p className={styles.loading}>loading graph...</p>;

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h2 className={styles.title}>Graph View</h2>
        <div className={styles.legend}>
          <span><span className={styles.dotHigh}>●</span> high risk</span>
          <span><span className={styles.dotMedium}>●</span> medium</span>
          <span><span className={styles.dotNormal}>●</span> normal</span>
        </div>
      </div>

      <svg ref={svgRef} className={styles.canvas} />
    </div>
  );
}