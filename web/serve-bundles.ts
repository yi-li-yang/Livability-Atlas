import { createReadStream, existsSync, statSync } from "node:fs";
import { extname, join, normalize, resolve, sep } from "node:path";
import type { Connect, Plugin } from "vite";

const TYPES: Record<string, string> = {
  ".json": "application/json",
  ".parquet": "application/octet-stream",
};

/**
 * Serves data bundles at `/bundles/` from a folder, in `vite dev` and `vite preview`.
 * A bundle is `<region>/latest.json` and `<region>/<version>/{manifest.json,cells.parquet}`, as
 * `atlas build` writes them into `data/published/`. A release serves them from a CDN instead.
 */
export function serveBundles(folder: string): Plugin {
  const root = resolve(folder);
  const handler: Connect.NextHandleFunction = (req, res, next) => {
    const url = (req.url ?? "").split("?")[0];
    if (!url.startsWith("/bundles/")) return next();
    const file = normalize(
      join(root, decodeURIComponent(url.slice("/bundles/".length))),
    );
    if (
      !file.startsWith(root + sep) ||
      !existsSync(file) ||
      !statSync(file).isFile()
    ) {
      res.statusCode = 404;
      res.end("not found");
      return;
    }
    res.setHeader(
      "Content-Type",
      TYPES[extname(file)] ?? "application/octet-stream",
    );
    res.setHeader("Cache-Control", "no-cache");
    createReadStream(file).pipe(res);
  };
  return {
    name: "serve-bundles",
    configureServer: (server) => void server.middlewares.use(handler),
    configurePreviewServer: (server) => void server.middlewares.use(handler),
  };
}
