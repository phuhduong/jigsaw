import type { Route } from "./+types/landing";
import LandingPage from "../landing/index";

export function meta({}: Route.MetaArgs) {
  return [
    { title: "Jigsaw: Make your PCB click" },
    {
      name: "description",
      content:
        "Describe your device in plain language to get an evidence-backed pre-layout BOM with purchasing links and compatibility findings.",
    },
  ];
}

export default function Landing() {
  return <LandingPage />;
}
