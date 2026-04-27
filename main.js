const { createApp, ref, onMounted, computed } = Vue;

createApp({
    setup() {
        const categories = ref([]);
        const articles = ref([]);
        const specialPages = ref({});
        const config = ref({
            site: { title: '加载中...', copyright: '', beian: '', beian_url: '#' }
        });
        
        const openFolders = ref([]);
        const openArticles = ref([]);
        const activeWindowId = ref(null);
        const currentTime = ref('');
        const zIndexCounter = ref(100);

        // 计算属性
        const pinnedArticles = computed(() => articles.value.filter(a => a.pinned));
        const recentArticles = computed(() => {
            return [...articles.value].sort((a, b) => new Date(b.date) - new Date(a.date)).slice(0, 3);
        });

        // 获取索引数据
        const fetchData = async () => {
            try {
                const response = await fetch('data.json');
                const data = await response.json();
                categories.value = data.categories;
                articles.value = data.articles;
                specialPages.value = data.pages;
                config.value = data.config;
                
                // 更新浏览器标题
                if (config.value.site && config.value.site.title) {
                    document.title = config.value.site.title;
                }
            } catch (error) {
                console.error('Failed to fetch data:', error);
            }
        };

        // 时钟
        const updateTime = () => {
            const now = new Date();
            currentTime.value = now.toLocaleString('zh-CN', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
        };

        // 窗口管理
        const openFolder = (category) => {
            const existing = openFolders.value.find(f => f.id === category.id);
            if (existing) {
                existing.minimized = false;
                bringToFront(category.id, 'folder');
                return;
            }
            const folder = {
                ...category,
                viewMode: 'list',
                minimized: false,
                maximized: false,
                style: {
                    top: '100px',
                    left: '200px',
                    width: '400px',
                    height: '300px',
                    zIndex: ++zIndexCounter.value
                }
            };
            openFolders.value.push(folder);
            activeWindowId.value = category.id;
        };

        const closeFolder = (id) => {
            openFolders.value = openFolders.value.filter(f => f.id !== id);
            if (activeWindowId.value === id) activeWindowId.value = null;
        };

        const prepareArticleContent = (rawContent) => {
            if (!rawContent) {
                return {
                    content: '',
                    toc: []
                };
            }

            const parser = new DOMParser();
            const doc = parser.parseFromString(rawContent, 'text/html');
            const headings = Array.from(doc.body.querySelectorAll('h1, h2, h3'));
            const usedIds = new Set();
            const toc = headings.map((heading, index) => {
                const text = heading.textContent.trim();
                const level = Number.parseInt(heading.tagName.slice(1), 10);
                let id = heading.id || text
                    .toLowerCase()
                    .replace(/[^\w\u4e00-\u9fa5\s-]/g, '')
                    .trim()
                    .replace(/\s+/g, '-');

                if (!id) {
                    id = `heading-${index + 1}`;
                }

                const baseId = id;
                let suffix = 2;
                while (usedIds.has(id)) {
                    id = `${baseId}-${suffix++}`;
                }
                usedIds.add(id);
                heading.id = id;

                return {
                    id,
                    text,
                    level
                };
            });

            return {
                content: doc.body.innerHTML,
                toc
            };
        };

        const scrollToHeading = (articleId, headingId) => {
            const articleBody = document.querySelector(`.article-body[data-article-id="${articleId}"]`);
            const heading = articleBody?.querySelector(`#${CSS.escape(headingId)}`);
            if (!articleBody || !heading) {
                return;
            }

            articleBody.scrollTo({
                top: heading.offsetTop - 16,
                behavior: 'smooth'
            });
            bringToFront(articleId, 'article');
        };

        const renderMath = async (root = document) => {
            if (!window.MathJax || !window.MathJax.typesetPromise) {
                return;
            }
            try {
                const targets = root instanceof Element ? [root] : undefined;
                await window.MathJax.typesetPromise(targets);
            } catch (error) {
                console.error('MathJax render failed:', error);
            }
        };

        const parseWindowWidth = (widthValue) => {
            if (typeof widthValue === 'number' && Number.isFinite(widthValue)) {
                return widthValue;
            }
            if (typeof widthValue !== 'string') {
                return null;
            }
            const normalized = widthValue.trim();
            if (normalized.endsWith('px')) {
                const parsed = Number.parseFloat(normalized);
                return Number.isFinite(parsed) ? parsed : null;
            }
            if (normalized.endsWith('%')) {
                const parsed = Number.parseFloat(normalized);
                return Number.isFinite(parsed) ? window.innerWidth * parsed / 100 : null;
            }
            if (normalized.startsWith('calc(100%')) {
                return window.innerWidth;
            }
            const fallback = Number.parseFloat(normalized);
            return Number.isFinite(fallback) ? fallback : null;
        };

        const measureTitleWidth = (() => {
            const canvas = document.createElement('canvas');
            const context = canvas.getContext('2d');
            return (value) => {
                if (!context) {
                    return value.length * 14;
                }
                context.font = '500 14px "Noto Sans SC", sans-serif';
                return context.measureText(value).width;
            };
        })();

        const getWindowTitle = (title, widthValue) => {
            if (!title) {
                return '';
            }
            const normalized = String(title).trim();
            const windowWidth = parseWindowWidth(widthValue);
            if (!windowWidth) {
                return normalized;
            }

            const availableWidth = Math.max(80, windowWidth - 120);
            if (measureTitleWidth(normalized) <= availableWidth) {
                return normalized;
            }

            const chars = Array.from(normalized);
            let head = '';
            let tail = '';
            let left = 0;
            let right = chars.length - 1;
            const ellipsis = '...';

            while (left <= right) {
                const nextHead = head + chars[left];
                const nextTail = chars[right] + tail;
                const headCandidate = measureTitleWidth(nextHead + ellipsis + tail);
                const tailCandidate = measureTitleWidth(head + ellipsis + nextTail);

                if (headCandidate <= availableWidth && (headCandidate <= tailCandidate || tail === '')) {
                    head = nextHead;
                    left += 1;
                    continue;
                }
                if (tailCandidate <= availableWidth) {
                    tail = nextTail;
                    right -= 1;
                    continue;
                }
                break;
            }

            if (!head && !tail) {
                return normalized;
            }

            while (tail && measureTitleWidth(head + ellipsis + tail) > availableWidth) {
                tail = tail.slice(1);
            }
            while (head && measureTitleWidth(head + ellipsis + tail) > availableWidth) {
                head = head.slice(0, -1);
            }

            return `${head}${ellipsis}${tail}`;
        };

        const openArticle = async (article) => {
            const existing = openArticles.value.find(a => a.id === article.id);
            if (existing) {
                existing.minimized = false;
                bringToFront(article.id, 'article');
                return;
            }

            let content = article.content || '';
            if (!content && article.content_url) {
                try {
                    const response = await fetch(article.content_url);
                    content = await response.text();
                } catch (e) {
                    content = '<p style="color:red">内容加载失败</p>';
                }
            }

            const preparedArticle = prepareArticleContent(content);
            const win = {
                ...article,
                content: preparedArticle.content,
                toc: preparedArticle.toc,
                minimized: false,
                maximized: false,
                style: {
                    top: '150px',
                    left: '250px',
                    width: '600px',
                    height: '400px',
                    zIndex: ++zIndexCounter.value
                }
            };
            openArticles.value.push(win);
            activeWindowId.value = article.id;
            requestAnimationFrame(() => {
                const articleBody = document.querySelector(`.article-body[data-article-id="${article.id}"] .article-render-content`);
                renderMath(articleBody || document);
            });
        };

        const closeArticle = (id) => {
            openArticles.value = openArticles.value.filter(a => a.id !== id);
            if (activeWindowId.value === id) activeWindowId.value = null;
        };

        const bringToFront = (id, type) => {
            const list = type === 'folder' ? openFolders.value : openArticles.value;
            const item = list.find(i => i.id === id);
            if (item) {
                item.style.zIndex = ++zIndexCounter.value;
                activeWindowId.value = id;
            }
        };

        const minimizeWindow = (item, type) => {
            item.minimized = true;
            activeWindowId.value = null;
        };

        const maximizeWindow = (item, type) => {
            if (item.maximized) {
                item.maximized = false;
                item.style.top = item.oldPos.top;
                item.style.left = item.oldPos.left;
                item.style.width = item.oldPos.width;
                item.style.height = item.oldPos.height;
            } else {
                item.oldPos = {
                    top: item.style.top,
                    left: item.style.left,
                    width: item.style.width,
                    height: item.style.height
                };
                item.maximized = true;
                item.style.top = '28px'; // topbar height
                item.style.left = '0px';
                item.style.width = '100%';
                item.style.height = 'calc(100% - 28px)';
            }
        };

        const getArticlesByCategory = (categoryId) => {
            return articles.value.filter(a => a.category === categoryId);
        };

        const setFolderViewMode = (folderId, mode) => {
            const folder = openFolders.value.find(f => f.id === folderId);
            if (folder) {
                folder.viewMode = mode;
                bringToFront(folderId, 'folder');
            }
        };

        const openAbout = () => {
            openArticle({
                id: 'about',
                title: '关于我',
                content_url: specialPages.value.about
            });
        };

        const openSocial = () => {
            openArticle({
                id: 'social',
                title: '社交联系',
                content_url: specialPages.value.social
            });
        };

        // 窗口拖拽逻辑
        const handleDrag = (e, item, type) => {
            // 只要点击窗口（无论哪里），首先触发置顶和激活
            bringToFront(item.id, type);
            
            if (item.maximized) return;
            
            // 只有点击标题栏且不是控制按钮时，才允许拖拽
            const titleBar = e.target.closest('.webde-window-titlebar');
            const ctrlBtn = e.target.closest('.window-ctrl-btn');
            if (!titleBar || ctrlBtn) return;
            
            // 获取当前窗口元素并添加拖拽类
            const winEl = e.currentTarget;
            winEl.classList.add('dragging');

            const startX = e.clientX;
            const startY = e.clientY;
            const startLeft = parseInt(item.style.left);
            const startTop = parseInt(item.style.top);

            const onMouseMove = (moveEvent) => {
                const deltaX = moveEvent.clientX - startX;
                const deltaY = moveEvent.clientY - startY;
                item.style.left = `${startLeft + deltaX}px`;
                item.style.top = `${startTop + deltaY}px`;
            };

            const onMouseUp = () => {
                document.removeEventListener('mousemove', onMouseMove);
                document.removeEventListener('mouseup', onMouseUp);
                winEl.classList.remove('dragging');
            };

            document.addEventListener('mousemove', onMouseMove);
            document.addEventListener('mouseup', onMouseUp);
        };

        // 窗口缩放逻辑
        const handleResize = (e, item, type, direction) => {
            if (item.maximized) return;
            bringToFront(item.id, type);

            // 获取当前窗口元素并添加缩放类
            const winEl = e.target.closest('.webde-window');
            winEl.classList.add('resizing');

            const startX = e.clientX;
            const startY = e.clientY;
            const startWidth = parseInt(item.style.width);
            const startHeight = parseInt(item.style.height);
            const startLeft = parseInt(item.style.left);
            const startTop = parseInt(item.style.top);

            const onMouseMove = (moveEvent) => {
                const deltaX = moveEvent.clientX - startX;
                const deltaY = moveEvent.clientY - startY;
                
                let newWidth = startWidth;
                let newHeight = startHeight;
                let newLeft = startLeft;
                let newTop = startTop;

                // 处理宽度和水平位置
                if (direction.includes('e')) {
                    newWidth = Math.max(200, startWidth + deltaX);
                } else if (direction.includes('w')) {
                    const possibleWidth = startWidth - deltaX;
                    if (possibleWidth > 200) {
                        newWidth = possibleWidth;
                        newLeft = startLeft + deltaX;
                    } else {
                        newWidth = 200;
                        newLeft = startLeft + (startWidth - 200);
                    }
                }

                // 处理高度和垂直位置
                if (direction.includes('s')) {
                    newHeight = Math.max(150, startHeight + deltaY);
                } else if (direction.includes('n')) {
                    const possibleHeight = startHeight - deltaY;
                    if (possibleHeight > 150) {
                        newHeight = possibleHeight;
                        newTop = startTop + deltaY;
                    } else {
                        newHeight = 150;
                        newTop = startTop + (startHeight - 150);
                    }
                }

                item.style.width = `${newWidth}px`;
                item.style.height = `${newHeight}px`;
                item.style.left = `${newLeft}px`;
                item.style.top = `${newTop}px`;
            };

            const onMouseUp = () => {
                document.removeEventListener('mousemove', onMouseMove);
                document.removeEventListener('mouseup', onMouseUp);
                document.body.style.cursor = 'default';
                winEl.classList.remove('resizing');
            };

            document.addEventListener('mousemove', onMouseMove);
            document.addEventListener('mouseup', onMouseUp);
            // 锁定光标，防止在快速缩放时脱离手柄导致的光标闪烁
            document.body.style.cursor = window.getComputedStyle(e.target).cursor;
        };

        onMounted(() => {
            fetchData();
            updateTime();
            setInterval(updateTime, 1000);
        });

        return {
            config,
            categories,
            articles,
            pinnedArticles,
            recentArticles,
            openFolders,
            openArticles,
            currentTime,
            openFolder,
            closeFolder,
            openArticle,
            closeArticle,
            bringToFront,
            getArticlesByCategory,
            setFolderViewMode,
            openAbout,
            openSocial,
            handleDrag,
            handleResize,
            minimizeWindow,
            maximizeWindow,
            scrollToHeading,
            getWindowTitle,
            activeWindowId
        };
    }
}).mount('#app');
