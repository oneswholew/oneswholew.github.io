(function() {
    if (window._faviconScriptExecuted) {
        console.log('脚本已经执行过，跳过');
        return;
    }
    window._faviconScriptExecuted = true;

    document.addEventListener('DOMContentLoaded', function() {
        console.log('脚本开始执行（全部并发版）');

        const links = document.querySelectorAll('li a');
        console.log('找到链接数量:', links.length);

        const getFaviconUrl = (origin) => {
            try {
                const domain = new URL(origin).hostname;
                return `https://toolb.cn/favicon/${domain}?_t=${Date.now()}&_=${Math.random()}`;
            } catch (e) {
                return null;
            }
        };

        const TIMEOUT = 15000;
        const IMAGE_TIMEOUT = 8000;

        const processedLinks = new WeakMap();

        // 强化 loader 样式
        if (!document.querySelector('#favicon-loader-style')) {
            const style = document.createElement('style');
            style.id = 'favicon-loader-style';
            style.textContent = `
                .elegant-loader {
                    display: inline-block !important;
                    width: 16.5px !important;
                    height: 16.5px !important;
                    margin-right: 6.5px !important;
                    vertical-align: middle !important;
                    background: linear-gradient(135deg, #6b8cff 0%, #8b6bff 100%) !important;
                    border-radius: 50% !important;
                    animation: pulse 1.5s ease-in-out infinite !important;
                    box-shadow: 0 2px 8px rgba(107, 140, 255, 0.3) !important;
                }
                @keyframes pulse {
                    0% { transform: scale(0.8); opacity: 0.7; }
                    50% { transform: scale(1); opacity: 1; box-shadow: 0 4px 12px rgba(107, 140, 255, 0.5); }
                    100% { transform: scale(0.8); opacity: 0.7; }
                }
                .letter-placeholder {
                    display: inline-flex !important;
                    align-items: center !important;
                    justify-content: center !important;
                    width: 16.5px !important;
                    height: 16.5px !important;
                    margin-right: 6.5px !important;
                    vertical-align: middle !important;
                    border-radius: 4px !important;
                    font-size: 11px !important;
                    font-weight: 600 !important;
                    color: white !important;
                    flex-shrink: 0 !important;
                    text-transform: uppercase !important;
                }
                .favicon-img {
                    width: 16.5px !important;
                    height: 16.5px !important;
                    margin-right: 6.5px !important;
                    vertical-align: middle !important;
                    object-fit: contain !important;
                    border-radius: 3px !important;
                }
            `;
            document.head.appendChild(style);
        }

        // 收集所有需要处理的任务
        const allTasks = [];

        links.forEach(link => {
            if (processedLinks.has(link)) return;
            try {
                if (!link.href || !link.href.startsWith('http')) return;
                const url = new URL(link.href);
                const origin = url.origin;

                const hasIcon = link.parentNode.querySelector('.favicon-img, .letter-placeholder');
                if (hasIcon) return;

                // 立即创建 loader
                const loader = document.createElement('span');
                loader.className = 'elegant-loader';
                link.parentNode.insertBefore(loader, link);
                console.log(`创建 loader: ${origin}`);

                processedLinks.set(link, true);
                allTasks.push({ link, origin, loader });
            } catch (error) {
                console.error('处理链接出错:', error);
            }
        });

        console.log('全部任务数:', allTasks.length);

        // 一次性并发所有任务，不限制数量
        allTasks.forEach(task => {
            loadFavicon(task.origin, task.link, task.loader);
        });

        function loadFavicon(origin, link, loader) {
            let isCompleted = false;
            let attemptCount = 0;
            const MAX_RETRIES = 2;

            const loaderStartTime = Date.now();

            function finishWithIcon(img) {
                const elapsed = Date.now() - loaderStartTime;
                const remaining = Math.max(0, 300 - elapsed);
                setTimeout(() => {
                    if (loader && loader.parentNode) loader.remove();
                    img.className = 'favicon-img';
                    img.setAttribute('data-favicon', 'true');
                    link.parentNode.insertBefore(img, link);
                }, remaining);
            }

            function finishWithPlaceholder() {
                const elapsed = Date.now() - loaderStartTime;
                const remaining = Math.max(0, 300 - elapsed);
                setTimeout(() => {
                    if (loader && loader.parentNode) {
                        useLetterPlaceholder(link, loader);
                    }
                }, remaining);
            }

            function attemptLoad() {
                if (isCompleted) return;

                const iconUrl = getFaviconUrl(origin);
                if (!iconUrl) {
                    if (!isCompleted) {
                        isCompleted = true;
                        finishWithPlaceholder();
                    }
                    return;
                }

                console.log(`[${origin}] 尝试 ${attemptCount + 1}/${MAX_RETRIES + 1}`);

                const img = new Image();
                let timeoutId = null;

                timeoutId = setTimeout(() => {
                    if (isCompleted) return;
                    console.log(`[${origin}] 超时`);
                    img.onload = null;
                    img.onerror = null;
                    if (attemptCount < MAX_RETRIES) {
                        attemptCount++;
                        attemptLoad();
                    } else {
                        isCompleted = true;
                        finishWithPlaceholder();
                    }
                }, IMAGE_TIMEOUT);

                img.onload = () => {
                    if (isCompleted) return;
                    const isValid = img.width > 1 && img.height > 1 && img.naturalWidth > 1;
                    if (isValid) {
                        console.log(`[${origin}] ✅ 成功 (${img.width}x${img.height})`);
                        clearTimeout(timeoutId);
                        isCompleted = true;
                        finishWithIcon(img);
                    } else {
                        console.log(`[${origin}] ❌ 空白图片`);
                        clearTimeout(timeoutId);
                        if (attemptCount < MAX_RETRIES) {
                            attemptCount++;
                            attemptLoad();
                        } else {
                            isCompleted = true;
                            finishWithPlaceholder();
                        }
                    }
                };

                img.onerror = () => {
                    if (isCompleted) return;
                    console.log(`[${origin}] ❌ 加载失败`);
                    clearTimeout(timeoutId);
                    if (attemptCount < MAX_RETRIES) {
                        attemptCount++;
                        attemptLoad();
                    } else {
                        isCompleted = true;
                        finishWithPlaceholder();
                    }
                };

                img.src = iconUrl;
            }

            attemptLoad();

            // 总超时保护
            const totalTimeout = setTimeout(() => {
                if (!isCompleted) {
                    console.log(`[${origin}] ⏱️ 总超时`);
                    isCompleted = true;
                    finishWithPlaceholder();
                }
            }, TIMEOUT);

            // 清理总超时
            const cleanup = () => clearTimeout(totalTimeout);
            const originalFinish = finishWithIcon;
            finishWithIcon = (img) => { cleanup(); originalFinish(img); };
            const originalPlaceholder = finishWithPlaceholder;
            finishWithPlaceholder = () => { cleanup(); originalPlaceholder(); };
        }

        function useLetterPlaceholder(link, loader) {
            if (!loader || !loader.parentNode) return;

            const existingIcon = link.parentNode.querySelector('.favicon-img');
            const existingPlaceholder = link.parentNode.querySelector('.letter-placeholder');
            if (existingIcon || existingPlaceholder) {
                if (loader.parentNode) loader.remove();
                return;
            }
            loader.remove();

            let letter = '?';
            try {
                const url = new URL(link.href);
                const hostname = url.hostname;
                letter = hostname.replace(/^www\./, '').charAt(0).toUpperCase();
                if (!letter.match(/[A-Z0-9]/)) letter = '?';
            } catch (e) {}

            const placeholder = document.createElement('span');
            placeholder.textContent = letter;
            placeholder.className = 'letter-placeholder';
            placeholder.style.backgroundColor = getRandomColor(letter);
            link.parentNode.insertBefore(placeholder, link);
        }

        function getRandomColor(letter) {
            const colors = [
                '#6b8cff', '#ff8b6b', '#6bcf8b', '#ffb86b',
                '#cf8bff', '#6bcfff', '#ff8bcf', '#8b9cff',
                '#9cff8b', '#ff9c8b', '#8b6bff', '#ff6b9c'
            ];
            const index = (letter.charCodeAt(0) || 0) % colors.length;
            return colors[index];
        }
    });
})();