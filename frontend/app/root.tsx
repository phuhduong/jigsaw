import {
  isRouteErrorResponse,
  Links,
  Meta,
  Outlet,
  Link,
  Scripts,
  ScrollRestoration,
} from "react-router";

import type { Route } from "./+types/root";
import stylesheet from "./app.css?url";

export const links: Route.LinksFunction = () => [
  { rel: "icon", href: "/favicon.ico", sizes: "16x16 32x32 48x48 64x64" },
  { rel: "icon", href: "/favicon.svg", type: "image/svg+xml", sizes: "any" },
  {
    rel: "preload",
    href: "/fonts/space-grotesk-latin.woff2",
    as: "font",
    type: "font/woff2",
    crossOrigin: "anonymous",
  },
  {
    rel: "preload",
    href: "/fonts/ibm-plex-sans-latin.woff2",
    as: "font",
    type: "font/woff2",
    crossOrigin: "anonymous",
  },
  { rel: "stylesheet", href: stylesheet },
];

export function Layout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <Meta />
        <Links />
      </head>
      <body>
        <a href="#main-content" className="skip-link">
          Skip to content
        </a>
        {children}
        <ScrollRestoration />
        <Scripts />
      </body>
    </html>
  );
}

export default function App() {
  return <Outlet />;
}

export function ErrorBoundary({ error }: Route.ErrorBoundaryProps) {
  let message = "This page could not be opened.";
  let details = "An unexpected error occurred.";

  if (isRouteErrorResponse(error)) {
    message =
      error.status === 404
        ? "Page not found"
        : "This page could not be opened.";
    details =
      error.status === 404
        ? "The requested page could not be found."
        : "Try opening the page again.";
  }

  return (
    <main id="main-content" className="error-page">
      <h1>{message}</h1>
      <p>{details}</p>
      <Link to="/" className="button">
        Return to Jigsaw
      </Link>
    </main>
  );
}
