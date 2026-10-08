# Jigsaw

Turn a device description into a bill of materials for an embedded system. Jigsaw finds
parts on DigiKey, reads manufacturer documents, and checks a proposed operating configuration.
The result includes purchase links, component roles, and notes for schematic design.

Explore the selected parts in a system map or purchasing table, refine a saved design, and
export the parts as CSV or the complete report as JSON.

## Run locally

Requires Python 3.11+, Node.js 22.12+, Yarn 4, a Gemini API key, and DigiKey Product Information
API credentials. Start each service in a separate terminal, beginning at the repository root.

**DigiKey service**

```sh
cd mcp-server
cp .env.template .env
# Set DIGIKEY_CLIENT_ID and DIGIKEY_CLIENT_SECRET in .env.
npm ci
npm run build
npm start
```

**Backend**

```sh
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.template .env
# Set GEMINI_API_KEY in .env.
python app.py
```

**Frontend**

```sh
cd frontend
corepack enable
yarn install --immutable
yarn dev
```

Open [localhost:5173](http://localhost:5173). The backend and DigiKey service listen on
loopback ports 3001 and 8080. See [configuration](docs/development.md#configuration) for
environment settings. Saved designs and cached documents use `$XDG_DATA_HOME/jigsaw`,
defaulting to `~/.local/share/jigsaw`. Set `DATA_DIR` to use another location.

## Development

Run `make check` from the repository root for tests, type checking, and production builds.
Tests use local fixtures and fakes. CI is configured to run the same checks.

See [architecture](docs/architecture.md) for the design and
[development](docs/development.md) for configuration, API, and operation.

## Credits

Built by Charles Muehlberger, Luke Sanborn, and Phu Duong at HackPrinceton Spring 2025.
[Winner, Best Business + Enterprise Hack](https://devpost.com/software/jigsaw-make-your-pcb-board-click).
