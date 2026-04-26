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

        const openArticle = async (article) => {
            const existing = openArticles.value.find(a => a.id === article.id);
            if (existing) {
                existing.minimized = false;
                bringToFront(article.id, 'article');
                return;
            }

            // 如果内容还没加载，则进行异步加载
            let content = article.content || '';
            if (!content && article.content_url) {
                try {
                    const response = await fetch(article.content_url);
                    content = await response.text();
                } catch (e) {
                    content = '<p style="color:red">内容加载失败</p>';
                }
            }

            const win = {
                ...article,
                content: content, // 将加载好的内容存入窗口对象
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
            activeWindowId
        };
    }
}).mount('#app');
