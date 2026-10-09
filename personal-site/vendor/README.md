# 随仓库保存的 Markdown 依赖

普通构建只使用这里的 Python 源码，无需安装包、无需网络。站点使用 Python 3.10+。

| 项目 | 固定版本 | 保存范围 | 许可证 |
| --- | --- | --- | --- |
| [markdown-it-py](https://pypi.org/project/markdown-it-py/4.2.0/) | 4.2.0 | 完整 `markdown_it/` 包 | MIT；包含 markdown-it 上游声明 |
| [mdurl](https://pypi.org/project/mdurl/0.1.2/) | 0.1.2 | 完整 `mdurl/` 包 | MIT |
| [mdit-py-plugins](https://pypi.org/project/mdit-py-plugins/0.6.1/) | 0.6.1 | `__init__.py`、`utils.py`、`py.typed`、`footnote/`、`tasklists/` | MIT；tasklists 源码含 ISC 声明 |

源码保持上游原样，本站配置、章节容器和 URL 限制位于 `../markdown_renderer.py`。未使用的插件、wheel 安装元数据及 CLI 启动器未复制。原始许可证在 `licenses/`；下载 wheel 文件名和 SHA-256 在 `manifest.json`。解析器源码不参与静态发布，也不会发送给浏览器。

升级时明确选定三个兼容版本，从 PyPI 下载对应纯 Python wheel（例如使用 `python3 -m pip download --only-binary=:all: --no-deps --dest <临时目录> markdown-it-py==4.2.0 mdurl==0.1.2 mdit-py-plugins==0.6.1`）。核对 PyPI 公布的 SHA-256，按表中范围原样替换源码并复制各 wheel 的许可证，更新 manifest 和版本表。

升级后运行 README 中的完整测试与构建，并使用 `python3 -S` 验证没有意外依赖本机安装的包；复查表格/图片手机布局、脚注锚点、安全 URL、原始 HTML 转义、搜索文本、生成文件同步与重建一致性。
