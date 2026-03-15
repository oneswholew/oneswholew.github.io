// 使用立即执行函数和标志位防止重复执行
(function() {
    // 检查是否已经执行过
    if (window._faviconScriptExecuted) {
        console.log('脚本已经执行过，跳过');
        return;
    }
    window._faviconScriptExecuted = true;

    document.addEventListener('DOMContentLoaded', function() {
        console.log('脚本开始执行'); // 调试1：脚本是否加载

        const links = document.querySelectorAll('li a');
        console.log('找到链接数量:', links.length); // 调试2：是否找到链接

        const placeholderIcon = 'css/img/failedicon.png';
        const fallbackPlaceholder =
            'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABGdBTUEAALGPC/xhBQAAAAlwFlzAAAOwQAADsEBuJFr7QAAABh0RVh0U29mdHdhcmUAcGFpbnQubmV0IDQuMC41ZYUyZQAAAG1JREFUOE+lk8ENwCAMRdu7ewZXJ/EqHkJwE9TBCwR+a6FLUQsRwYBTeD8/35wADnZVmPvEiVEWmoY1E06LLUnO0ANGTA19j5OY9R8QvOgvZOLHn4bASWf0B5AkTLb8c0g0T2FQVNLUgA9vQQ08IOxLdgAAAABJRU5ErkJggg==';
        const TIMEOUT = 3000; // 超时时间

        const faviconServices = [
            origin => {
                try {
                    const domain = new URL(origin).hostname;
                    return `https://toolb.cn/favicon/${domain}`;
                } catch (e) {
                    return null;
                }
            }
        ];

        function setIconStyle(img) {
            img.style.width = '16.5px';
            img.style.height = '16.5px';
            img.style.marginRight = '6.5px';
            img.style.verticalAlign = 'middle';
        }

        // ==== 使用Map记录已处理的链接 ====
        const processedLinks = new WeakMap();

        // 直接处理所有链接
        links.forEach(link => {
            // 检查是否已经处理过这个链接
            if (processedLinks.has(link)) {
                console.log('链接已处理，跳过:', link.href);
                return;
            }

            try {
                if (!link.href || !link.href.startsWith('http')) return;

                const url = new URL(link.href);
                const origin = url.origin;

                // 检查是否已有loader，如果有且是之前留下的，就复用但确保样式正确
                let loader = link.parentNode.querySelector('.loader');
                
                // 如果已经有loader，但不是当前处理流程创建的，检查是否需要重置
                if (loader) {
                    console.log('找到已存在的loader，可能来自之前执行');
                    // 确保loader样式正确（可能之前的执行被中断）
                    loader.style.display = 'inline-block';
                    loader.style.animation = 'spin 1s linear infinite';
                } else {
                    // 创建新的loader
                    loader = document.createElement('span');
                    loader.classList.add('loader');
                    loader.style.border = '3px solid #f3f3f3';
                    loader.style.borderTop = '3px solid #3498db';
                    loader.style.width = '16.5px';
                    loader.style.height = '16.5px';
                    loader.style.display = 'inline-block';
                    loader.style.marginRight = '6.5px';
                    loader.style.animation = 'spin 1s linear infinite';
                    link.parentNode.insertBefore(loader, link);
                }

                // 标记链接为已处理
                processedLinks.set(link, true);

                const totalTimeout = setTimeout(() => {
                    // 检查这个链接是否已经被成功加载（可以通过检查是否已有图标来判断）
                    const existingIcon = link.parentNode.querySelector('img[data-favicon="true"]');
                    if (!existingIcon) {
                        usePlaceholderIcon(link, loader);
                    }
                }, TIMEOUT);

                tryFetchFavicon(origin, link, loader, 0, totalTimeout);

            } catch (error) {
                console.error('处理链接出错:', error);
                const loader = link.parentNode.querySelector('.loader');
                if (loader) usePlaceholderIcon(link, loader);
            }
        });

        function tryFetchFavicon(origin, link, loader, attemptIndex, totalTimeout) {
            console.log('尝试获取favicon, 索引:', attemptIndex, 'origin:', origin);
            let isCompleted = false;

            if (attemptIndex >= faviconServices.length) {
                console.log('所有尝试失败，使用占位图');
                clearTimeout(totalTimeout);
                usePlaceholderIcon(link, loader);
                return;
            }

            const iconUrl = faviconServices[attemptIndex](origin);
            if (!iconUrl) {
                console.log('URL无效，尝试下一个');
                tryFetchFavicon(origin, link, loader, attemptIndex + 1, totalTimeout);
                return;
            }

            console.log('尝试加载图标:', iconUrl);
            const img = new Image();
            img.src = iconUrl;
            setIconStyle(img);
            img.setAttribute('data-favicon', 'true'); // 标记为favicon图标

            const timeout = setTimeout(() => {
                if (isCompleted) return;
                console.log('单路径超时, 尝试下一个');
                isCompleted = true;
                img.onerror = null;
                img.onload = null;
                tryFetchFavicon(origin, link, loader, attemptIndex + 1, totalTimeout);
            }, TIMEOUT);

            img.onload = function() {
                if (isCompleted) return;
                console.log('图标加载成功:', iconUrl);
                isCompleted = true;

                clearTimeout(timeout);
                clearTimeout(totalTimeout);

                // 方案一：隐藏loader而不是移除
                if (loader && loader.parentNode) {
                    console.log('隐藏loader');
                    loader.style.display = 'none';
                }
                
                // 添加loading="lazy"属性
                img.loading = 'lazy';
                // 添加decoding="async"异步解码，不阻塞渲染
                img.decoding = 'async';

                link.parentNode.insertBefore(img, link);
            };

            img.onerror = function() {
                if (isCompleted) return;
                console.log('图标加载失败:', iconUrl);
                isCompleted = true;

                clearTimeout(timeout);
                tryFetchFavicon(origin, link, loader, attemptIndex + 1, totalTimeout);
            };
        }

        // 首字母占位符函数
        function usePlaceholderIcon(link, loader) {
            console.log('使用首字母占位符');
            if (!loader || !loader.parentNode) return;

            // 检查是否已经插入过占位符
            const existingPlaceholder = link.parentNode.querySelector('.letter-placeholder');
            const existingIcon = link.parentNode.querySelector('img[data-favicon="true"]');
            
            if (existingPlaceholder || existingIcon) {
                console.log('占位符或图标已存在，跳过');
                // 只需要隐藏loader
                loader.style.display = 'none';
                return;
            }

            // 隐藏loader
            loader.style.display = 'none';

            // 获取网站首字母
            let letter = '?';
            try {
                const url = new URL(link.href);
                const hostname = url.hostname;
                // 取域名第一个字符，去掉www.
                letter = hostname.replace('www.', '').charAt(0).toUpperCase();
                if (!letter.match(/[A-Z]/)) letter = '?'; // 如果不是字母就显示?
            } catch (e) {
                letter = '?';
            }

            // 创建首字母占位符
            const placeholder = document.createElement('span');
            placeholder.textContent = letter;
            placeholder.classList.add('letter-placeholder'); // 添加类名便于识别
            placeholder.style.display = 'inline-block';
            placeholder.style.width = '16.5px';
            placeholder.style.height = '16.5px';
            placeholder.style.backgroundColor = getRandomColor(letter);
            placeholder.style.color = 'white';
            placeholder.style.fontSize = '12px';
            placeholder.style.fontWeight = 'bold';
            placeholder.style.textAlign = 'center';
            placeholder.style.lineHeight = '16.5px';
            placeholder.style.borderRadius = '3px';
            placeholder.style.marginRight = '6.5px';
            placeholder.style.verticalAlign = 'middle';
            placeholder.style.flexShrink = '0';

            link.parentNode.insertBefore(placeholder, link);
        }

        // 根据字母生成颜色（同一个字母颜色固定）
        function getRandomColor(letter) {
            const colors = [
                '#6b8cff', '#ff8b6b', '#6bcf8b', '#ffb86b',
                '#cf8bff', '#6bcfff', '#ff8bcf', '#8b9cff',
                '#9cff8b', '#ff9c8b', '#8b6bff', '#ff6b9c'
            ];
            const index = letter.charCodeAt(0) % colors.length;
            return colors[index];
        }
    });
})();