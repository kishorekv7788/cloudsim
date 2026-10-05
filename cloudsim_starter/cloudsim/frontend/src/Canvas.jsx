import { useState } from "react";
import { Stage, Layer, Group, Rect, Text } from "react-konva";
import { completeLab } from "./progressStore.js";

const START = [
  { id: "vnet-prod", kind: "network", x: 30, y: 30, w: 440, h: 220, cidr: "10.0.0.0/16" },
  { id: "web", kind: "subnet", x: 50, y: 80, w: 180, h: 70, cidr: "10.0.1.0/24" },
  { id: "app", kind: "subnet", x: 260, y: 80, w: 180, h: 70, cidr: "10.0.1.128/25" },
];

export default function Canvas({ labId = "az900-lab02" }) {
  const [nodes, setNodes] = useState(START);
  const [result, setResult] = useState(null);

  const onDragEnd = (id, e) =>
    setNodes((ns) => ns.map((n) => (n.id === id ? { ...n, x: e.target.x(), y: e.target.y() } : n)));

  const editCidr = (id) => {
    const cidr = window.prompt("New CIDR for " + id);
    if (cidr) setNodes((ns) => ns.map((n) => (n.id === id ? { ...n, cidr } : n)));
  };

  async function validate() {
    const vnet = nodes.find((n) => n.kind === "network");
    const body = {
      name: vnet.id, provider: "azure", address_space: vnet.cidr,
      subnets: nodes.filter((n) => n.kind === "subnet").map((n) => ({ name: n.id, cidr: n.cidr })),
    };
    const res = await fetch(`/api/labs/${labId}/validate`, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
    });
    const data = await res.json();
    setResult(data);
    if (data.passed) completeLab(labId, body.provider);
  }

  return (
    <div className="p-4">
      <button onClick={validate} className="px-4 py-2 bg-blue-700 text-white rounded">
        Validate
      </button>
      {result && (
        <p className={result.passed ? "text-green-700" : "text-red-700"}>
          {result.passed ? "Lab passed!" : result.issues.join(" | ")}
        </p>
      )}
      <Stage width={520} height={280} className="border mt-2">
        <Layer>
          {nodes.map((n) => (
            <Group key={n.id} x={n.x} y={n.y} draggable={n.kind !== "network"}
                   onDragEnd={(e) => onDragEnd(n.id, e)} onDblClick={() => editCidr(n.id)}>
              <Rect width={n.w} height={n.h} stroke="#12355B"
                    fill={n.kind === "network" ? "#EAF1F7" : "#CDE7EA"} />
              <Text text={`${n.id}\n${n.cidr}`} x={8} y={8} fontSize={13} />
            </Group>
          ))}
        </Layer>
      </Stage>
    </div>
  );
}
