import type { DesignSnapshot, Finding } from "../services/api/designRunApi";
import { getComponentTitle } from "./componentPresentation";
import {
  getCompatibilityFailures,
  getSubjectComponentIds,
  isSelectedProduct,
} from "./reportHelpers";
import "./report.css";

type ReportProps = {
  snapshot: DesignSnapshot;
  onSelect?: (id: string) => void;
};

function ComponentLinks({
  snapshot,
  ids,
  onSelect,
}: ReportProps & { ids: string[] }) {
  const components = [...new Set(ids)]
    .map((id) => snapshot.components.find((part) => part.id === id))
    .filter((part) => part !== undefined);
  if (!onSelect || components.length === 0) return null;
  return (
    <div className="report-references">
      {components.map((part) => (
        <button
          className="reference-button"
          key={part.id}
          onClick={() => onSelect(part.id)}
        >
          {getComponentTitle(part)}
        </button>
      ))}
    </div>
  );
}

export function CompatibilityIssue({
  snapshot,
  finding,
  onSelect,
}: ReportProps & { finding: Finding }) {
  // Selection failures carry supplier errors and instructions for the correction
  // model. The useful user-facing fact is the missing part, not those diagnostics.
  const hasMissingSelection =
    finding.id.startsWith("code:selection:") &&
    finding.subject_ids.some((id) => {
      const component = snapshot.components.find((part) => part.id === id);
      return component !== undefined && !isSelectedProduct(component.product);
    });
  return (
    <article className="compatibility-issue">
      <p>
        {hasMissingSelection
          ? "A suitable part has not been selected for this role."
          : finding.explanation}
      </p>
      {!hasMissingSelection && finding.remedy && (
        <p className="issue-remedy">{finding.remedy}</p>
      )}
      <ComponentLinks
        snapshot={snapshot}
        ids={finding.subject_ids.flatMap((id) =>
          getSubjectComponentIds(snapshot, id),
        )}
        onSelect={onSelect}
      />
    </article>
  );
}

export default function ReviewPanel({ snapshot, onSelect }: ReportProps) {
  const failures = getCompatibilityFailures(snapshot);
  const supportIds = [
    ...new Set(
      [...snapshot.source_support_needs, ...snapshot.support_needs].map(
        (need) => need.id,
      ),
    ),
  ];
  if (
    failures.length === 0 &&
    snapshot.assumptions.length === 0 &&
    snapshot.configuration_notes.length === 0 &&
    supportIds.length === 0
  )
    return null;
  return (
    <section className="review-panel" aria-label="Design notes">
      {failures.length > 0 && (
        <section className="design-notes-section design-failures">
          <h2>Compatibility issues</h2>
          <div>
            {failures.map((finding) => (
              <CompatibilityIssue
                key={finding.id}
                snapshot={snapshot}
                finding={finding}
                onSelect={onSelect}
              />
            ))}
          </div>
        </section>
      )}
      {snapshot.assumptions.length > 0 && (
        <section className="design-notes-section">
          <h2>Operating assumptions</h2>
          <ul className="design-note-list">
            {snapshot.assumptions.map((assumption) => (
              <li key={assumption.id}>{assumption.description}</li>
            ))}
          </ul>
        </section>
      )}
      {snapshot.configuration_notes.length > 0 && (
        <section className="design-notes-section">
          <h2>Schematic notes</h2>
          <ul className="design-note-list">
            {[...new Set(snapshot.configuration_notes)].map((note, index) => (
              <li key={index}>{note}</li>
            ))}
          </ul>
        </section>
      )}
      {supportIds.length > 0 && (
        <section className="design-notes-section">
          <h2>Supporting components</h2>
          <div>
            {supportIds.map((id) => {
              const need = snapshot.support_needs.find(
                (item) => item.id === id,
              );
              const source = snapshot.source_support_needs.find(
                (item) => item.id === id,
              );
              const descriptions = [
                ...new Set(
                  [
                    source?.connection_requirement,
                    need?.connections,
                    need?.explanation,
                  ].filter(Boolean),
                ),
              ];
              return (
                <article className="support-note" key={id}>
                  <h3>{need?.purpose || source?.purpose}</h3>
                  {descriptions.map((description, index) => (
                    <p key={index}>{description}</p>
                  ))}
                  <ComponentLinks
                    snapshot={snapshot}
                    ids={need?.component_ids ?? []}
                    onSelect={onSelect}
                  />
                </article>
              );
            })}
          </div>
        </section>
      )}
    </section>
  );
}
