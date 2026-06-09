import { useEffect, useState } from "react";
import type { Concept, GraphNode } from "../../types";
import { getConcept } from "../../api/concepts";
import { TestView } from "../test/TestView";

interface Props {
  node: GraphNode;
  sessionId: string;
  onClose: () => void;
}

/** Боковая панель узла: определение + запуск теста. */
export function NodePanel({ node, sessionId, onClose }: Props) {
  const [concept, setConcept] = useState<Concept | null>(null);
  const [testing, setTesting] = useState(false);

  useEffect(() => {
    setTesting(false);
    setConcept(null);
    getConcept(node.id).then(setConcept);
  }, [node.id]);

  return (
    <aside
      style={{
        width: 360,
        borderLeft: "1px solid #e2e8f0",
        padding: 20,
        overflowY: "auto",
      }}
    >
      <button onClick={onClose} style={{ float: "right" }}>
        ✕
      </button>
      <h3>{node.name}</h3>
      {!concept ? (
        <p>Загрузка…</p>
      ) : testing ? (
        <TestView
          conceptId={concept.id}
          sessionId={sessionId}
          onDone={() => setTesting(false)}
        />
      ) : (
        <>
          <p>{concept.definition}</p>
          {concept.formula && (
            <pre style={{ background: "#f1f5f9", padding: 8 }}>
              {concept.formula}
            </pre>
          )}
          {concept.quote && (
            <blockquote style={{ color: "#64748b", fontStyle: "italic" }}>
              {concept.quote}
            </blockquote>
          )}
          <button onClick={() => setTesting(true)}>Пройти тест</button>
        </>
      )}
    </aside>
  );
}
