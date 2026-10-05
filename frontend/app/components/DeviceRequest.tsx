import { useId, useRef, useState } from "react";
import type { FormEvent, KeyboardEvent } from "react";
import { ArrowRight, ArrowUpRight } from "lucide-react";
import { API_CONFIG } from "../services/api/config";
import type { InitialRequest } from "../services/api/designRunApi";
import PartIllustration from "../design/PartIllustration";

const WIRELESS_SENSOR_EXAMPLE =
  "A temperature and humidity sensor with Wi-Fi and Bluetooth, powered by USB-C (5V) for indoor use.";

export default function DeviceRequest({
  onSubmit,
  initialRequest,
}: {
  onSubmit: (request: InitialRequest) => void;
  initialRequest?: InitialRequest;
}) {
  const id = useId();
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const [query, setQuery] = useState(initialRequest?.query ?? "");
  const { generationDisabled } = API_CONFIG;
  const trimmedQuery = query.trim();

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (generationDisabled || !trimmedQuery) return;
    onSubmit({ query: trimmedQuery });
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
      event.preventDefault();
      if (!generationDisabled) event.currentTarget.form?.requestSubmit();
    }
  }

  function handleUseExample() {
    setQuery(WIRELESS_SENSOR_EXAMPLE);
    inputRef.current?.focus();
  }

  return (
    <section className="request-screen">
      <div className="request-heading">
        <h1>Describe your device.</h1>
        <p id={`${id}-hint`}>What should it do, and how will it be powered?</p>
      </div>
      {generationDisabled && (
        <p className="notice notice-info" role="status">
          Generation is disabled in this preview. Saved designs are still
          available.
        </p>
      )}
      <div className="request-layout">
        <form className="request-form" onSubmit={handleSubmit}>
          <label htmlFor={`${id}-query`} className="sr-only">
            Device requirements
          </label>
          <textarea
            id={`${id}-query`}
            ref={inputRef}
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="A small indoor temperature sensor, powered by USB-C, that sends readings over Wi-Fi…"
            maxLength={10000}
            required
            disabled={generationDisabled}
            rows={6}
            aria-describedby={`${id}-hint`}
            onKeyDown={handleKeyDown}
          />
          <div className="request-toolbar">
            <button
              type="submit"
              className="button button-primary"
              disabled={generationDisabled || !trimmedQuery}
            >
              Find components <ArrowRight size={17} aria-hidden="true" />
            </button>
          </div>
        </form>
        <button
          className="request-example"
          type="button"
          disabled={generationDisabled}
          aria-label="Use wireless sensor example"
          onClick={handleUseExample}
        >
          <span className="example-caption">Try an example</span>
          <span className="example-drawing" aria-hidden="true">
            <svg className="example-connections" viewBox="0 0 340 220">
              <path d="M85 63V159H153Q163 159 163 149V73Q163 63 173 63H250" />
              <path d="M250 63V159" />
            </svg>
            <span className="example-part example-part-input">
              <PartIllustration role="connector" usb />
            </span>
            <span className="example-part example-part-controller">
              <PartIllustration role="controller" wireless />
            </span>
            <span className="example-part example-part-power">
              <PartIllustration role="power" />
            </span>
            <span className="example-part example-part-sensor">
              <PartIllustration role="sensor" />
            </span>
          </span>
          <span className="example-footer">
            <span>
              <strong>Wireless sensor</strong>
              <span>Temperature · humidity · USB-C</span>
            </span>
            <ArrowUpRight size={19} aria-hidden="true" />
          </span>
        </button>
      </div>
    </section>
  );
}
