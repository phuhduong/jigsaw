import type { Route } from "./+types/landing";
import LandingPage from "../landing/index";

export function meta({}: Route.MetaArgs) {
  return [
    { title: "Jigsaw: Make your PCB click" },
    {
      name: "description",
      content:
        "Describe your circuit board in plain language, and our AI finds compatible components and generates a complete buy list.",
    },
  ];
}

export default function Landing() {
  return <LandingPage />;
}
