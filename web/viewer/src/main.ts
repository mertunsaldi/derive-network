import cytoscape from "cytoscape";
import "mathjax/es5/tex-chtml-full.js";

type ApiNode = {
  type: string;
  data: Record<string, unknown>;
};

type PathResponse = {
  path: string[];
  nodes: Record<string, ApiNode>;
};

async function fetchPath(exampleId: string): Promise<PathResponse | null> {
  try {
    const response = await fetch(`/api/v1/paths?src=${exampleId}&dst=${exampleId}`);
    if (!response.ok) {
      return null;
    }
    return (await response.json()) as PathResponse;
  } catch (error) {
    console.error(error);
    return null;
  }
}

function renderMath(element: HTMLElement, tex: string) {
  element.innerHTML = tex;
  (window as any).MathJax?.typesetPromise([element]).catch((error: unknown) => console.error(error));
}

async function bootstrap() {
  const container = document.createElement("div");
  container.style.display = "flex";
  container.style.height = "100vh";

  const graphContainer = document.createElement("div");
  graphContainer.id = "cy";
  graphContainer.style.flex = "2";
  const detailContainer = document.createElement("div");
  detailContainer.style.flex = "1";
  detailContainer.style.padding = "1rem";

  container.append(graphContainer, detailContainer);
  document.getElementById("app")?.append(container);

  const cy = cytoscape({
    container: graphContainer,
    layout: { name: "breadthfirst" },
    style: [
      { selector: "node", style: { label: "data(label)", "text-valign": "center" } },
      { selector: "edge", style: { "curve-style": "bezier", "target-arrow-shape": "triangle" } },
    ],
  });

  const path = await fetchPath("seed-energy");
  if (!path) {
    detailContainer.textContent = "No example path available. Seed data should be loaded via API.";
    return;
  }

  cy.add(
    path.path.map((id) => {
      const node = path.nodes[id];
      const label = node?.type === "statement" ? (node.data?.latex_variants?.[0] as string | undefined) ?? id : id;
      return {
        group: "nodes",
        data: { id, label },
      };
    }),
  );

  cy.on("tap", "node", (event) => {
    const node = path.nodes[event.target.id()];
    detailContainer.innerHTML = "";
    if (!node) return;
    const heading = document.createElement("h2");
    heading.textContent = node.type.toUpperCase();
    detailContainer.appendChild(heading);
    if (node.data?.latex_variants?.length) {
      const math = document.createElement("div");
      renderMath(math, node.data.latex_variants[0] as string);
      detailContainer.appendChild(math);
    }
    const pre = document.createElement("pre");
    pre.textContent = JSON.stringify(node.data, null, 2);
    detailContainer.appendChild(pre);
  });
}

bootstrap().catch((error) => console.error("Failed to bootstrap viewer", error));
