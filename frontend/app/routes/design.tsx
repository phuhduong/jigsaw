import { useLocation } from "react-router";
import { useMemo } from "react";
import DesignPage from "../design/index";
import type { InitialRequest } from "../services/api/designRunApi";

export function meta() {
  return [
    { title: "Jigsaw" },
    {
      name: "description",
      content:
        "Describe your device in plain language to get an evidence-backed pre-layout BOM with purchasing links and compatibility findings.",
    },
  ];
}

export default function DesignRoute() {
  const location = useLocation();
  const initialRequest = useMemo(() => {
    const state = location.state as {
      request?: InitialRequest;
      query?: string;
    } | null;
    return (
      state?.request ?? (state?.query ? { query: state.query } : undefined)
    );
  }, [location.state]);
  const runId = new URLSearchParams(location.search).get("run");

  return <DesignPage initialRequest={initialRequest} runId={runId} />;
}
