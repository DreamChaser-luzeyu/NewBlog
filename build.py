import os
import json
import re
import yaml
import frontmatter
from markdown import markdown
from pathlib import Path
from datetime import datetime


def adjust_relative_urls(html_content, base_dir):
    base_posix = base_dir.as_posix().strip("./")

    def replace_attr(match):
        attr = match.group(1)
        url = match.group(2)

        if re.match(r'^(?:[a-zA-Z][a-zA-Z0-9+.-]*:|/|#)', url):
            return match.group(0)

        normalized_url = Path(base_posix, url).as_posix() if base_posix else url
        return f'{attr}="{normalized_url}"'

    return re.sub(r'(src|href)="([^"]+)"', replace_attr, html_content)


def build_blog_data():
    posts_dir = Path("./posts")
    pages_dir = Path("./pages")
    dist_dir = Path("./dist")
    config_file = Path("config.yaml")
    
    # 创建输出目录
    (dist_dir / "posts").mkdir(parents=True, exist_ok=True)
    (dist_dir / "pages").mkdir(parents=True, exist_ok=True)

    # 加载配置文件
    site_config = {}
    if config_file.exists():
        with open(config_file, 'r', encoding='utf-8') as f:
            site_config = yaml.safe_load(f)
    
    if not posts_dir.exists():
        print("错误: 'posts' 目录不存在。")
        return

    articles_metadata = []
    categories_list = [d.name for d in posts_dir.iterdir() if d.is_dir()]
    
    final_categories = []
    article_id_counter = 1
    category_id_counter = 1000

    # 1. 处理博客文章
    all_md_files = list(posts_dir.rglob("*.md"))
    
    # 按目录分组
    category_map = {}
    for md_file in all_md_files:
        category_name = md_file.parent.name
        if category_name == "posts":
            continue
        if category_name not in category_map:
            category_map[category_name] = []
        category_map[category_name].append(md_file)

    for category_name, md_files in category_map.items():
        category_articles_ids = []

        for md_file in md_files:
            with open(md_file, 'r', encoding='utf-8') as f:
                post = frontmatter.load(f)
                html_content = markdown(post.content, extensions=['extra', 'codehilite', 'toc'])
                html_content = adjust_relative_urls(html_content, md_file.parent)
                
                html_filename = f"post_{article_id_counter}.html"
                html_path = dist_dir / "posts" / html_filename
                
                with open(html_path, 'w', encoding='utf-8') as html_f:
                    html_f.write(html_content)
                
                article_meta = {
                    "id": article_id_counter,
                    "title": post.get('title', md_file.stem),
                    "date": str(post.get('date', datetime.now().strftime('%Y-%m-%d'))),
                    "category": category_id_counter,
                    "content_url": f"dist/posts/{html_filename}",
                    "pinned": post.get('pinned', False),
                    "type": "article"
                }
                
                articles_metadata.append(article_meta)
                category_articles_ids.append(article_id_counter)
                article_id_counter += 1

        final_categories.append({
            "id": category_id_counter,
            "name": category_name,
            "articles": category_articles_ids
        })
        category_id_counter += 1

    # 2. 处理固定页面 (关于、社交)
    special_pages = {}
    if pages_dir.exists():
        for page_name in ["about", "social"]:
            page_file = pages_dir / f"{page_name}.md"
            if page_file.exists():
                with open(page_file, 'r', encoding='utf-8') as f:
                    raw_content = f.read()
                    if page_name == "social":
                        social_config = site_config.get("social", {}) if site_config else {}
                        github = social_config.get("github", "")
                        email = social_config.get("email", "")
                        twitter = social_config.get("twitter", "")

                        social_lines = [
                            "# 社交联系",
                            "",
                            "你可以通过以下方式联系我：",
                            ""
                        ]

                        if github:
                            social_lines.append(f"- **GitHub**: [{github}]({github})")
                        if email:
                            social_lines.append(f"- **Email**: [{email}]({email})")
                        if twitter:
                            social_lines.append(f"- **Twitter**: [{twitter}]({twitter})")

                        if len(social_lines) == 4:
                            social_lines.append("- 暂未提供社交联系方式")

                        raw_content = "\n".join(social_lines)

                    content = markdown(raw_content, extensions=['extra', 'codehilite'])
                    content = adjust_relative_urls(content, page_file.parent)
                    html_filename = f"{page_name}.html"
                    html_path = dist_dir / "pages" / html_filename
                    
                    with open(html_path, 'w', encoding='utf-8') as html_f:
                        html_f.write(content)
                    
                    special_pages[page_name] = f"dist/pages/{html_filename}"

    articles_metadata.sort(key=lambda x: x['date'], reverse=True)

    data = {
        "config": site_config,
        "categories": final_categories,
        "articles": articles_metadata,
        "pages": special_pages
    }

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    
    print(f"成功! 生成了 {len(articles_metadata)} 个独立 HTML 文件，已修复分类 ID 逻辑。")


if __name__ == "__main__":
    build_blog_data()
