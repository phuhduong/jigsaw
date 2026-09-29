import type { Route } from "./+types/design";
import { useLocation } from "react-router";
import DesignInterface from "../design/index";

export function meta({}: Route.MetaArgs) {
  return [
    { title: "Jigsaw" },
    {
      name: "description",
      content:
        "Describe your device in plain language to get an evidence-backed pre-layout BOM with purchasing links and compatibility findings.",
    },
  ];
}

export default function Design() {
  const location = useLocation();
  const query = (location.state as { query?: string })?.query || "";
  const runId = new URLSearchParams(location.search).get("run");

  return <DesignInterface initialQuery={query} runId={runId} />;
}
