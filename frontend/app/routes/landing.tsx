import { useNavigate } from "react-router";
import AppHeader from "../components/AppHeader";
import DeviceRequest from "../components/DeviceRequest";

export function meta() {
  return [
    { title: "Jigsaw · Device bill of materials" },
    {
      name: "description",
      content:
        "Describe your device in plain language to get an evidence-backed pre-layout BOM with purchasing links and compatibility findings.",
    },
  ];
}

export default function LandingRoute() {
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
