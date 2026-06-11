import { useNavigate } from "react-router-dom";
import { UploadView } from "./UploadView";

export function UploadPage() {
  const navigate = useNavigate();
  return <UploadView onReady={(bookId) => navigate(`/graphs/${bookId}`)} />;
}
