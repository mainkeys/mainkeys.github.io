'use strict';

// Aurora 2.5.3 uses a local month but a UTC day/year in its three article
// models. Keep all three fields in the browser's local timezone. Patch only
// generated output; leave source timestamps and the installed theme intact.
hexo.extend.filter.register('after_generate', async () => {
  if (hexo.config.theme !== 'aurora') return;

  const route = 'static/js/120aa8f8.js';
  const before = 'day:s.getUTCDate(),year:s.getUTCFullYear()';
  const after = 'day:s.getDate(),year:s.getFullYear()';
  const stream = hexo.route.get(route);
  if (!stream) throw new Error('Aurora date compatibility: expected theme bundle is missing.');

  let source = '';
  stream.setEncoding('utf8');
  for await (const chunk of stream) source += chunk;

  const count = source.split(before).length - 1;
  if (count === 0 && source.split(after).length - 1 === 3) return;
  if (count !== 3) {
    throw new Error('Aurora date compatibility: expected three date models; review the theme bundle after upgrading.');
  }

  // Keep the entry URL stable: lazy chunks import it. Browsers with a cached
  // copy pick up the fix on revalidation (or a forced refresh).
  hexo.route.set(route, source.split(before).join(after));
});
