'use strict';

hexo.extend.filter.register('before_generate', () => {
  const sourcePrefix = `${String(hexo.config.source_dir).replace(/\\/g, '/')}/`;
  const postDirectories = hexo
    .model('Post')
    .toArray()
    .map((post) => ({
      post,
      directory: String(post.source)
        .replace(/\\/g, '/')
        .replace(/\.[^/.]+$/, '/')
    }))
    .sort((left, right) => right.directory.length - left.directory.length);

  const updates = hexo.model('PostAsset')
    .toArray()
    .map((asset) => {
      let assetSource = String(asset._id).replace(/\\/g, '/');
      if (assetSource.startsWith(sourcePrefix)) {
        assetSource = assetSource.slice(sourcePrefix.length);
      }

      const owner = postDirectories.find(({ directory }) => assetSource.startsWith(directory));
      if (!owner) return undefined;

      // Asset discovery can assign a draft file to a published post on Windows.
      // Filter using its actual owner before Hexo's asset generator runs.
      if (!hexo._showDrafts() && owner.post.published === false) return asset.remove();

      const slug = assetSource.slice(owner.directory.length);
      const post = owner.post._id;

      if (asset.slug === slug && asset.post === post) return undefined;
      return asset.update({ slug, post });
    });

  return Promise.all(updates);
});
