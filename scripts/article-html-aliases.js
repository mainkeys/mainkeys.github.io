'use strict';

// Hexo emits /post/<slug>.html, while Aurora uses the route parameter
// verbatim as the article API key. Preserve both direct HTML links and
// Aurora's extensionless client-side links without modifying the theme.
hexo.extend.filter.register('after_generate', async () => {
  if (!/\.html\/?$/.test(hexo.config.permalink)) return;

  const routes = hexo.route.list().filter((route) =>
    /^api\/articles\/.+\.json$/.test(route) && !route.endsWith('.html.json')
  );
  await Promise.all(routes.map(async (route) => {
    const stream = hexo.route.get(route);
    let content = '';
    if (typeof stream === 'string' || Buffer.isBuffer(stream)) {
      content = stream.toString();
    } else {
      stream.setEncoding('utf8');
      for await (const chunk of stream) content += chunk;
    }
    hexo.route.set(route.slice(0, -5) + '.html.json', content);
  }));
});
