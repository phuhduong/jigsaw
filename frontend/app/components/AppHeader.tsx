import { Link } from "react-router";
import { Plus } from "lucide-react";

export default function AppHeader({
  workspace = false,
}: {
  workspace?: boolean;
}) {
  return (
    <header className="app-header">
      <Link to="/" className="app-name" aria-label="Jigsaw home">
        Jigsaw
      </Link>
      {workspace && (
        <Link to="/" className="button button-small">
          <Plus size={15} aria-hidden="true" /> New device
        </Link>
      )}
    </header>
  );
}
