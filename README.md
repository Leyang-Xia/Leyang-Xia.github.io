# Leyang Xia 的个人网站

正式地址：[leyang-xia.github.io](https://leyang-xia.github.io/)。GitHub Pages 从 `main` 分支的仓库根目录发布。

## 编辑文章

文章内容集中在 [`personal-site/build.py`](personal-site/build.py) 的 `POSTS` 列表。每篇文章需要 `slug`、`title`、`summary`、`tags`、`status`、`published_at`、`cover` 和 `sections`。

- 草稿展示使用 `status: "sample"`、`published_at: None`，会进入文库的“版式预览”区，并标注“示例稿”。
- 正式发布改为 `status: "published"`，填入 `published_at: "YYYY-MM-DD"`，会按年份和日期自动排列。发布前请将示例文字换成自己的内容。
- `tags` 是文章主题名称，如“实时音频”或“随笔”；点击标签可分享对应的文库链接。`cover` 可为 `None`，或填写相对 `personal-site/dist/` 的本地图片路径（例如 `assets/cover.png`）。
- 不要随意改动已发布文章的 `slug`，它决定文章 URL 和评论线程。

## 构建与发布

在仓库根目录运行：

```sh
PYTHONPATH=personal-site python3 -m unittest discover -s personal-site/tests -v
node personal-site/tests/test_archive_client.js
node personal-site/tests/test_comments_client.js
python3 personal-site/build.py
```

生成器把页面写入 `personal-site/dist/`，再同步到仓库根目录。样式和脚本源文件位于 `personal-site/dist/assets/`。确认变更后提交并推送 `main`；GitHub Pages 发布根目录文件。评论后端的部署与审核检查见 [`docs/comment-operations.md`](docs/comment-operations.md)。

Sites 预览与 GitHub Pages 独立，预览站不加载正式评论。
