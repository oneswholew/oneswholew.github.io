document.addEventListener('DOMContentLoaded', function () {
    const links = document.querySelectorAll('li a');
    const placeholderIcon = 'css/img/failedicon.png';

    links.forEach(link => {
        const url = new URL(link.href);
        const faviconUrl = `${url.origin}/favicon.ico?timestamp=${Date.now()}`; // 添加时间戳避免缓存

        const loader = document.createElement('span');
        loader.classList.add('loader');
        link.parentNode.insertBefore(loader, link);

        const img = document.createElement('img');
        img.src = faviconUrl;
        img.style.width = '16px';
        img.style.height = '16px';
        img.style.marginRight = '5px';

        img.onload = function () {
            loader.style.display = 'none';
            link.parentNode.insertBefore(img, link);
        };

        img.onerror = function () {
            this.src = placeholderIcon;
            this.onerror = function () {
                loader.style.display = 'none';
                link.style.color = 'red';
            };
        };
    });
});