import LandingPage from "../landing/index";

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
  return <LandingPage />;
}
