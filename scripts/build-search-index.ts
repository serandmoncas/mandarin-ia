import { mkdirSync, writeFileSync } from "node:fs";
import path from "node:path";
import { loadDictionary, resolveDictionaryPath } from "../src/lib/dictionary/load";
import { buildSearchIndex } from "../src/lib/search";

try {
  const file = resolveDictionaryPath();
  const index = buildSearchIndex(loadDictionary(file));
  const out = path.join(process.cwd(), "public/search-index.json");
  mkdirSync(path.dirname(out), { recursive: true });
  writeFileSync(out, JSON.stringify(index));
  console.log(`search-index: ${index.length} entries from ${file} -> ${out}`);
} catch (e) {
  console.error(e instanceof Error ? e.message : e);
  process.exit(1);
}
