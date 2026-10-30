// Convert a DWG to JSON (header, model-space entities, block definitions) with libredwg-web.
// Usage: bun tools/dwg/dwg_to_json.mjs <in.dwg> <out.json>
// rule60-v3.dwg reports libredwg code 4 (unhandled class, non-fatal); all 2110 entities convert.
import { Dwg_File_Type, LibreDwg } from '@mlightcad/libredwg-web';
import { readFileSync, writeFileSync } from 'node:fs';

const [input, output] = process.argv.slice(2);
if (!input || !output) {
  console.error('usage: bun tools/dwg/dwg_to_json.mjs <in.dwg> <out.json>');
  process.exit(2);
}
const wasmDir = new URL('./node_modules/@mlightcad/libredwg-web/wasm/', import.meta.url).pathname;
const libredwg = await LibreDwg.create(wasmDir);
const dwg = libredwg.dwg_read_data(readFileSync(input), Dwg_File_Type.DWG);
const db = libredwg.convert(dwg);
const out = { header: db.header, blocks: {}, entities: db.entities };
for (const rec of db.tables?.BLOCK_RECORD?.entries ?? []) {
  out.blocks[rec.name] = rec.entities ?? [];
}
writeFileSync(output, JSON.stringify(out, (_, v) => (typeof v === 'bigint' ? Number(v) : v)));
console.log(`${input}: ${db.entities.length} entities -> ${output}`);
libredwg.dwg_free(dwg);
