import os
import json
import yaml
import frontmatter
from markdown import markdown
from pathlib import Path
from datetime import datetime

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
    category_id_counter = 1000 # 为分类设置独立的 ID 计数器

    # 1. 处理博客文章
    for category_name in categories_list:
        category_path = posts_dir / category_name
        category_articles_ids = []

        for md_file in category_path.glob("*.md"):
            with open(md_file, 'r', encoding='utf-8') as f:
                post = frontmatter.load(f)
                html_content = markdown(post.content, extensions=['extra', 'codehilite', 'toc'])
                
                # 生成独立 HTML 文件名
                html_filename = f"post_{article_id_counter}.html"
                html_path = dist_dir / "posts" / html_filename
                
                with open(html_path, 'w', encoding='utf-8') as html_f:
                    html_f.write(html_content)
                
                # 仅在 metadata 中保存路径，不保存内容
                article_meta = {
                    "id": article_id_counter,
                    "title": post.get('title', md_file.stem),
                    "date": str(post.get('date', datetime.now().strftime('%Y-%m-%d'))),
                    "category": category_id_counter, # 使用分类 ID
                    "content_url": f"dist/posts/{html_filename}", 
                    "pinned": post.get('pinned', False),
                    "type": "article"
                }
                
                articles_metadata.append(article_meta)
                category_articles_ids.append(article_id_counter)
                article_id_counter += 1

        final_categories.append({
            "id": category_id_counter, # 为分类添加 ID
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
                    content = markdown(f.read(), extensions=['extra', 'codehilite'])
                    html_filename = f"{page_name}.html"
                    html_path = dist_dir / "pages" / html_filename
                    
                    with open(html_path, 'w', encoding='utf-8') as html_f:
                        html_f.write(content)
                    
                    special_pages[page_name] = f"dist/pages/{html_filename}"

    # 按日期降序排列
    articles_metadata.sort(key=lambda x: x['date'], reverse=True)

    # 3. 整合最终的索引数据
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
