# 内蒙古高校/大专教师招聘监控工具

自动监控内蒙古人事考试网，发现高校、大专、职业院校的教师/辅导员招聘公告后，**立即推送到你的微信**。

---

## 🚀 5分钟部署教程

### 第一步：获取 Server酱 SendKey（1分钟）

1. 打开 [https://sct.ftqq.com](https://sct.ftqq.com)
2. 用微信扫码登录
3. 点击左侧 **「SendKey」**，复制你的 Key（格式类似 `SCT123456xxxxxx`）
4. 手机微信关注 **「方糖」** 公众号（推送消息会发到这里）

---

### 第二步：上传代码到 GitHub（2分钟）

1. 登录 [github.com](https://github.com)，点右上角 **「+」→「New repository」**
2. 仓库名随意（如 `nmg-job-monitor`），选 **Private（私有）**，点 Create
3. 把本项目三个文件上传上去：
   - `monitor.py`
   - `requirements.txt`
   - `.github/workflows/monitor.yml`

   > 上传方法：在仓库页面点「Add file」→「Upload files」，或者用 git 推送。

---

### 第三步：配置 SendKey（1分钟）

1. 在 GitHub 仓库页面，点 **Settings → Secrets and variables → Actions**
2. 点 **「New repository secret」**
3. Name 填：`SERVERCHAN_KEY`
4. Secret 填：你第一步复制的 Key
5. 点 Save

---

### 第四步：启用并测试（1分钟）

1. 点仓库顶部的 **Actions** 标签
2. 如果提示"Workflows aren't being run"，点击启用按钮
3. 点左侧的 **「内蒙古高校招聘监控」**
4. 点右侧 **「Run workflow」→「Run workflow」** 手动触发一次
5. 等待约30秒，查看运行日志；如有新公告，微信立刻收到通知 ✅

---

## ⏰ 运行频率

默认每 **2小时** 自动检查一次（北京时间 00:00, 02:00, 04:00 ... 22:00）。

如需调整，修改 `.github/workflows/monitor.yml` 中的 cron 表达式：

```yaml
- cron: '0 */2 * * *'   # 每2小时
- cron: '0 */4 * * *'   # 每4小时
- cron: '0 8,12,18 * * *'  # 每天8点、12点、18点
```

---

## 🎯 监控关键词

**匹配关键词**（命中任意一个就推送）：
> 大专、高职、职业技术、职业学院、职业大学、高校、学院、大学、教师、辅导员、教研、专任教师、教学

**排除关键词**（包含这些则跳过）：
> 中学、小学、幼儿园、中小学、义务教育

如需修改，编辑 `monitor.py` 顶部的 `KEYWORDS` 和 `EXCLUDE_KEYWORDS` 列表。

---

## 📱 推送效果

微信收到的消息示例：

```
【招聘提醒】2条新公告 - 内蒙古高校教师招聘

1. 呼和浩特职业技术大学2026年第三批引进人才公告
来源：内蒙古人事考试网-事业单位招聘
链接：https://www.nm.zsks.cn/...

2. 内蒙古机电职业技术学院招聘专任教师公告
来源：内蒙古人事考试网-高校招聘
链接：https://www.nm.zsks.cn/...
```

---

## 🔧 本地运行（可选）

```bash
pip install -r requirements.txt
export SERVERCHAN_KEY="你的Key"
python monitor.py
```

---

## 常见问题

**Q: GitHub Actions 免费吗？**
A: 公开仓库完全免费；私有仓库每月有 2000 分钟免费额度，本工具每次运行约 30 秒，2小时跑一次每月约 360 分钟，完全够用。

**Q: 会不会漏掉公告？**
A: 脚本会把已推送的公告 ID 存到 `seen_posts.json` 并提交到仓库，不会重复推送也不会遗漏。

**Q: 内蒙古人事考试网改版怎么办？**
A: 修改 `monitor.py` 中的 `TARGET_URLS` 或 `fetch_posts` 函数的解析逻辑即可。
