import { Hono } from "hono";
import { serveStatic } from "@hono/node-server/serve-static";
import { serve } from "@hono/node-server";

const app = new Hono();
const PORT = process.env.PORT || 3001;

app.use(serveStatic({ root: "./public" }));

serve({
  fetch: app.fetch,
  port: 3001,
});

console.log(`
┌────────────────────────────────────────────────┐
│                                                │
│   Experimentation Platform Demo                │
│                                                │
│   Server running at http://localhost:${PORT}      │
│                                                │
│   Available pages:                             │
│   - http://localhost:${PORT}/index.html           │
│   - http://localhost:${PORT}/demo-app.html        │
│   - http://localhost:${PORT}/simulator-ui-complete.html │
│                                                │
└────────────────────────────────────────────────┘
`);
