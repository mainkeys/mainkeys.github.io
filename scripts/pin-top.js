'use strict';

const POSTS_ROUTE = /^api\/posts\/(\d+)\.json$/;
const FEATURES_ROUTE = 'api/features.json';

function readRoute(route) {
  return new Promise((resolve, reject) => {
    const data = hexo.route.get(route);

    if (typeof data === 'string' || Buffer.isBuffer(data)) {
      resolve(data.toString());
      return;
    }

    let output = '';
    data.setEncoding('utf8');
    data.on('data', (chunk) => {
      output += chunk;
    });
    data.on('end', () => resolve(output));
    data.on('error', reject);
  });
}

function pinPosts(posts) {
  return [
    ...posts.filter((post) => post.pinned === true),
    ...posts.filter((post) => post.pinned !== true)
  ];
}

hexo.extend.filter.register('after_generate', async () => {
  const postRoutes = hexo.route
    .list()
    .filter((route) => POSTS_ROUTE.test(route))
    .sort((left, right) => {
      return Number(left.match(POSTS_ROUTE)[1]) - Number(right.match(POSTS_ROUTE)[1]);
    });

  if (postRoutes.length === 0) return;

  const pages = await Promise.all(
    postRoutes.map(async (route) => JSON.parse(await readRoute(route)))
  );
  const posts = pinPosts(pages.flatMap((page) => page.data));

  pages.forEach((page, index) => {
    const start = index * page.pageSize;
    page.data = posts.slice(start, start + page.pageSize);
    hexo.route.set(postRoutes[index], JSON.stringify(page));
  });

  if (hexo.route.list().includes(FEATURES_ROUTE)) {
    const features = JSON.parse(await readRoute(FEATURES_ROUTE));
    hexo.route.set(FEATURES_ROUTE, JSON.stringify(pinPosts(features)));
  }
});
