import { useNavigate } from "react-router";
import AppHeader from "../components/AppHeader";
import DeviceRequest from "../components/DeviceRequest";

export default function LandingPage() {
  const navigate = useNavigate();
  return (
    <div className="app-shell">
      <AppHeader />
      <main id="main-content">
        <DeviceRequest
          onSubmit={(request) => {
            void navigate("/design", { state: { request } });
          }}
        />
      </main>
    </div>
  );
}
