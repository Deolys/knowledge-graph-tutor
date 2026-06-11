import { useParams } from "react-router-dom";
import { useSession } from "../../hooks/useSession";
import { GraphView } from "./GraphView";

export function GraphPage() {
  const { bookId } = useParams<{ bookId: string }>();
  const sessionId = useSession();

  if (!bookId) return null;
  return <GraphView bookId={bookId} sessionId={sessionId} />;
}
