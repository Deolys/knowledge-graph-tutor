import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "./components/layout/Layout";
import { LandingPage } from "./components/landing/LandingPage";
import { GraphsListPage } from "./components/graph/GraphsListPage";
import { GraphPage } from "./components/graph/GraphPage";
import { UploadPage } from "./components/upload/UploadPage";
import { TestsListPage } from "./components/test/TestsListPage";
import { GraphTestPage } from "./components/test/GraphTestPage";

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<LandingPage />} />
          <Route path="upload" element={<UploadPage />} />
          <Route path="graphs" element={<GraphsListPage />} />
          <Route path="graphs/:bookId" element={<GraphPage />} />
          <Route path="tests" element={<TestsListPage />} />
          <Route path="tests/:testId" element={<GraphTestPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
