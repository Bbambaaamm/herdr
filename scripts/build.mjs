import { readFile, writeFile } from 'node:fs/promises';
import { build } from 'esbuild';

const output = 'agent_platform_dashboard/static/machine-city.js';

await build({
  entryPoints: ['agent_platform_dashboard/static/machine-city-source.js'],
  bundle: true,
  format: 'iife',
  platform: 'browser',
  target: 'es2022',
  minify: true,
  inject: ['agent_platform_dashboard/static/secure-random.js'],
  define: { 'Math.random': 'secureRandom' },
  outfile: output,
});

// Shader template literals retain upstream indentation after minification. Normalize
// only end-of-line whitespace so the committed deterministic bundle passes Git's
// whitespace gate without changing JavaScript or GLSL tokens.
const bundled = await readFile(output, 'utf8');
const normalized = bundled
  .replace(/[\t ]+$/gm, '')
  .replace(/^ +(?=\t)/gm, '');
await writeFile(output, normalized, 'utf8');
