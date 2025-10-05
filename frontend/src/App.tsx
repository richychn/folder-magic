import { Navigate, Route, Routes } from "react-router-dom";

import AgentChatPage from "./pages/AgentChat";
import DriveExplorerPage from "./pages/DriveExplorer";
import HomePage from "./pages/Home";

const App = () => {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/drive" element={<DriveExplorerPage />} />
      <Route path="/agent" element={<AgentChatPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};

export default App;
