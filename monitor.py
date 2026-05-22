"""
内蒙古人事考试信息网 - 高校/大专教师招聘监控脚本
推送方式：Server酱 (微信通知)
"""

import os
import re
import json
import hashlib
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin

# ─── 配置区 ────────────────────────────────────────────────
SERVERCHAN_KEY = os.environ.get("SERVERCHAN_KEY", "")  # 从环境变量读取

# 内蒙古人事考试信息网公告栏目（用户提供，已通过页面源码核实）
# ttt=31 → 事业单位招聘，公告链接路径形如 /shiyedanwei/2026xxx.asp
# ttt=8  → 新闻快讯（含高校招聘），公告链接路径形如 /xinwenkuaixue/2026xxx.asp
TARGET_URLS = [
    {
        "name": "内蒙古人事考试信息网-事业单位招聘",
        "url": "http://www.impta.com.cn/more.asp?ttt=31",
    },
    {
        "name": "内蒙古人事考试信息网-新闻快讯",
        "url": "http://www.impta.com.cn/more.asp?ttt=8",
    },
]

# 仅识别这两个目录下的链接为"真实公告"，过滤掉导航/页脚
ANNOUNCEMENT_PATH_RE = re.compile(r"/(shiyedanwei|xinwenkuaixue)/\d+\.asp$", re.IGNORECASE)

# 关键词（命中任意一个即推送）
KEYWORDS = [
    # 高校/大专
    "大学", "学院", "高校", "高等学校", "高职", "大专",
    # 职业院校（独立关键词，便于覆盖"XX职业技术学校"这类不带"学院"的写法）
    "职业",
    # 教师岗位
    "辅导员", "专任教师", "教师", "教研",
]

# 排除词（命中任意一个即跳过；用于剔除医院、中小学、其他非高校招聘）
EXCLUDE_KEYWORDS = [
    # 中小学幼儿园（中文"小学"会同时匹配"小学校"等，已是想要的行为）
    "中学", "小学", "幼儿园", "中小学", "义务教育",
    # 医院（医科大学的附属医院招聘不属于教学岗）
    "医院",
    # 非高校招聘类
    "公务员", "遴选", "选调", "警务", "税务", "海关", "残疾人专场",
]

# 本地缓存文件（记录已推送过的公告，避免重复推送）
CACHE_FILE = "seen_posts.json"
# ─────────────────────────────────────────────────────────


def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return None  # None 表示首次运行（区别于空 dict）


def save_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def make_id(title, url):
    return hashlib.md5(f"{title}{url}".encode()).hexdigest()


def is_relevant(title):
    """判断标题是否与高校教师招聘相关"""
    for ex in EXCLUDE_KEYWORDS:
        if ex in title:
            return False
    for kw in KEYWORDS:
        if kw in title:
            return True
    return False


def parse_announcements(html, base_url):
    """从 HTML 中解析出真实公告（按 URL 路径正则锁定，排除导航/页脚）"""
    soup = BeautifulSoup(html, "lxml")
    posts = []
    seen_urls = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        title = a.get_text(strip=True)
        if not title or len(title) < 5:
            continue
        full_url = urljoin(base_url, href)
        if not ANNOUNCEMENT_PATH_RE.search(full_url):
            continue
        if full_url in seen_urls:
            continue
        seen_urls.add(full_url)
        posts.append({"title": title, "url": full_url})
    return posts


def fetch_posts(url):
    """抓取页面上的公告列表"""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Referer": "http://www.impta.com.cn/",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.encoding = resp.apparent_encoding  # 站点为 GBK，自适应解码
        resp.raise_for_status()
    except Exception as e:
        print(f"[ERROR] 请求失败 {url}: {e}")
        return []
    return parse_announcements(resp.text, url)


def send_wechat(title, content):
    """通过 Server酱 推送微信通知。返回 True 表示推送成功。"""
    if not SERVERCHAN_KEY:
        print("[WARN] 未设置 SERVERCHAN_KEY，跳过推送")
        print(f"[模拟推送]\n标题: {title}\n内容:\n{content}")
        return False

    api_url = f"https://sctapi.ftqq.com/{SERVERCHAN_KEY}.send"
    data = {"title": title, "desp": content}
    try:
        resp = requests.post(api_url, data=data, timeout=10)
        result = resp.json()
        if result.get("code") == 0:
            print(f"[OK] 微信推送成功: {title}")
            return True
        print(f"[WARN] 推送返回: {result}")
        return False
    except Exception as e:
        print(f"[ERROR] 推送失败: {e}")
        return False


def run():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始监控...")
    cache = load_cache()
    first_run = cache is None
    if first_run:
        print("[INFO] 检测到首次运行（无 seen_posts.json），进入种子模式：仅记录不推送")
        cache = {}

    new_posts = []

    for target in TARGET_URLS:
        print(f"  抓取: {target['name']}")
        posts = fetch_posts(target["url"])
        print(f"  共找到 {len(posts)} 条链接")

        for post in posts:
            title = post["title"]
            url = post["url"]

            if not is_relevant(title):
                continue

            pid = make_id(title, url)
            if pid in cache:
                continue

            new_posts.append({
                "title": title,
                "url": url,
                "source": target["name"],
                "id": pid,
            })

    if first_run:
        # 首次运行：把当前所有命中的公告写进 cache，但不发推送
        for p in new_posts:
            cache[p["id"]] = {
                "title": p["title"],
                "url": p["url"],
                "found_at": datetime.now().isoformat(),
            }
        save_cache(cache)
        print(f"[OK] 种子模式完成，已记录 {len(new_posts)} 条历史公告（未推送）")
        print("监控完成。")
        return

    if new_posts:
        print(f"\n发现 {len(new_posts)} 条新公告，准备推送...")

        lines = [f"发现 **{len(new_posts)}** 条高校/大专教师招聘新公告\n"]
        for i, p in enumerate(new_posts, 1):
            lines.append(f"**{i}. {p['title']}**")
            lines.append(f"来源：{p['source']}")
            lines.append(f"链接：{p['url']}\n")

        content = "\n".join(lines)
        push_title = f"【招聘提醒】{len(new_posts)}条新公告 - 内蒙古高校教师招聘"

        if send_wechat(push_title, content):
            # 推送成功后才把这批 id 写入 cache
            for p in new_posts:
                cache[p["id"]] = {
                    "title": p["title"],
                    "url": p["url"],
                    "found_at": datetime.now().isoformat(),
                }
            save_cache(cache)
            print("[OK] 缓存已更新")
        else:
            print("[WARN] 推送未成功，缓存保持不变，下次运行会重试")
    else:
        print("[OK] 暂无新公告")

    print("监控完成。")


if __name__ == "__main__":
    run()
