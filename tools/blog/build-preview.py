#!/usr/bin/env python3
"""Build published posts into an external preview directory."""
import pathlib
import subprocess

repository = pathlib.Path(__file__).resolve().parents[2]
workspace = repository.parent / "optee-series-lab"
output = workspace / "preview"
workspace.mkdir(exist_ok=True)
config = workspace / "preview.yml"
# Keep Hexo's normal source directory inside its base directory. Hexo's post
# asset processor derives source paths by removing the base-directory prefix.
config.write_text(f"public_dir: {output.as_posix()}\nurl: http://127.0.0.1:4173\nrender_drafts: false\n", encoding="utf-8")
# Hexo's generated-file cache is shared across public_dir values. Force writes
# so an older preview cannot survive a newer build to the production directory.
subprocess.run(["node", "node_modules/hexo/bin/hexo", "generate", "--force", "--config", f"_config.yml,{config.as_posix()}"], cwd=repository, check=True)
