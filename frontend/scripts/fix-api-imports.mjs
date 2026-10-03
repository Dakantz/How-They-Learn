// swagger-typescript-api's `--modular` output inconsistently emits plain
// `import { X } from "./data-contracts"` (instead of `import type { X } ...`)
// for some generated route files. Since data-contracts.ts contains only
// `export interface` declarations (no runtime exports), a non-type-only
// import leaves a dangling named import that doesn't exist at runtime —
// Bun's transpiler only erases imports explicitly marked `import type`, so
// the browser fails to load the module ("does not provide an export named
// ..."). Run this after every `generate-api` to normalize those imports.
import { readdirSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const apiDir = new URL("../src/api/", import.meta.url).pathname;
/*
import { ContentType, HttpClient } from "./http-client";
import type { RequestParams } from "./http-client";
*/
let fixedCount = 0;
for (const file of readdirSync(apiDir)) {
  if (!file.endsWith(".ts") || file === "data-contracts.ts") continue;
  const path = join(apiDir, file);
  const imports = ["data-contracts"];
  for (const imp of imports) {
    const src = readFileSync(path, "utf8");
    const rx = `import \{([^}]*)\} from "\.\/${imp}";$`;
    const regexBuild = new RegExp(rx, "gm");
    const fixed = src.replace(
      regexBuild,
      `import type {$1} from "./${imp}";`,
    );
    if (fixed !== src) {
      writeFileSync(path, fixed);
      fixedCount++;
    }
  }
  const replacers = {
    'import { ContentType, HttpClient, RequestParams } from "./http-client";':
  `import \{ ContentType, HttpClient \} from "./http-client";
import type \{ RequestParams \} from "./http-client";`,
    'import { HttpClient, RequestParams } from "./http-client";':
  `import \{ HttpClient \} from "./http-client";
import type \{ RequestParams \} from "./http-client";`
}
  for (const [search, replace] of Object.entries(replacers)) {
    const src = readFileSync(path, "utf8");
    const fixed = src.replace(search, replace);
    if (fixed !== src) {
      console.log("fix-api-imports: fixed http-client import in", path);
      writeFileSync(path, fixed);
      fixedCount++;
    }
  }
}

if (fixedCount > 0) {
  console.log(
    `fix-api-imports: converted data-contracts imports to type-only in ${fixedCount} file(s)`,
  );
}
