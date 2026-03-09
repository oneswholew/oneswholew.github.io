document.addEventListener('DOMContentLoaded', function() {
    const links = document.querySelectorAll('li a');
    const placeholderIcon = 'css/img/failedicon.png';
    
    // 国内可用的图标服务备选列表
    const faviconServices = [
        function(origin) { return origin + '/favicon.ico?t=' + Date.now(); },
        function(origin) { return origin + '/favicon.png?t=' + Date.now(); },
        function(origin) { return origin + '/assets/favicon.ico?t=' + Date.now(); },
        function(origin) { return origin + '/images/favicon.ico?t=' + Date.now(); },
        function(origin) { return origin + '/icons/favicon.ico?t=' + Date.now(); },
        function(origin) { return origin + '/favicon-32x32.png?t=' + Date.now(); }
    ];
    
    links.forEach(function(link) {
        try {
            const url = new URL(link.href);
            
            // 创建加载动画
            const loader = document.createElement('span');
            loader.classList.add('loader');
            link.parentNode.insertBefore(loader, link);
            
            // 开始尝试获取图标
            tryFetchFavicon(url.origin, link, loader, 0);
            
        } catch (error) {
            console.log('无效的URL:', link.href);
        }
    });
    
    function tryFetchFavicon(origin, link, loader, attemptIndex) {
        if (attemptIndex >= faviconServices.length) {
            // 所有尝试都失败，使用占位图
            usePlaceholderIcon(link, loader);
            return;
        }
        
        const img = document.createElement('img');
        img.src = faviconServices[attemptIndex](origin);
        img.style.width = '16px';
        img.style.height = '16px';
        img.style.marginRight = '5px';
        img.style.verticalAlign = 'middle';
        
        img.onload = function() {
            loader.remove();
            link.parentNode.insertBefore(img, link);
        };
        
        img.onerror = function() {
            // 尝试下一个方案
            tryFetchFavicon(origin, link, loader, attemptIndex + 1);
        };
    }
    
    function usePlaceholderIcon(link, loader) {
        loader.remove();
        
        const placeholder = document.createElement('img');
        placeholder.src = placeholderIcon;
        placeholder.style.width = '16px';
        placeholder.style.height = '16px';
        placeholder.style.marginRight = '5px';
        placeholder.style.verticalAlign = 'middle';
        placeholder.style.opacity = '0.6'; // 占位图半透明，表明是默认图标
        
        link.parentNode.insertBefore(placeholder, link);
    }
});