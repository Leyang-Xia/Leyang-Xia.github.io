# 留言系统上线与审核

评论前端默认连接已部署的 Twikoo 后端；可用 `TWIKOO_ENV_ID` 在构建时覆盖公开端点。预览站始终不加载正式评论。**在完成以下检查前，不应宣布留言功能已经开放。**

## 部署

1. 按 [Twikoo 官方 Netlify 部署说明](https://twikoo.js.org/backend.html#netlify-%E9%83%A8%E7%BD%B2)建立 MongoDB Atlas 数据库，将连接串仅设置为 Netlify 环境变量 `MONGODB_URI`。不要把连接串写入此仓库、终端命令历史或生成的 HTML。
2. 官方仓库已 fork 到 `Leyang-Xia/twikoo-netlify` 并部署为 Netlify 项目 `leyang-twikoo`。健康端点为 `https://leyang-twikoo.netlify.app/.netlify/functions/twikoo`。前端与后端均使用 Twikoo 2.0.12。
3. 在评论管理面板设置管理员密码。进入配置管理，启用人工审核，并把昵称设为必填、邮箱设为选填。管理员密码由站长本人设置，不交给网站构建脚本。
4. 构建并发布：运行 `python3 personal-site/build.py`，检查生成文件后提交并推送。默认公开端点已写入构建配置；如需迁移后端，可临时设置 `TWIKOO_ENV_ID` 覆盖。该值只是公开服务 URL；数据库连接串不可注入前端。

## 上线验收记录

| 检查项 | 日期与结果 |
| --- | --- |
| Netlify 函数健康页 | 2026-09-30：公开端点返回 `code: 100`、Twikoo 2.0.12 |
| 管理员登录与审核开关 | 待实际验证 |
| 留言板匿名提交，审核前不可见，批准后可见 | 待实际验证 |
| 文章回复审核前不可见，批准后可见 | 待实际验证 |
| Sites 预览不请求正式评论后端 | 待实际验证 |
| 后端断开时正文和导航仍可用 | 待实际验证 |
| MongoDB Atlas 备份或导出办法 | 待实际验证 |

测试留言与回复应清楚注明“测试”，完成后从后台移除。不要在验收记录里写密码、连接串或其他私密数据。
