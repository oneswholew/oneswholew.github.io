// notice.js 优化版
document.addEventListener('DOMContentLoaded', function() {
    const announcementBtn = document.getElementById('announcementBtn');
    const popup = document.getElementById('announcementPopup');
    
    // 如果没有找到元素，提前退出避免报错
    if (!announcementBtn || !popup) {
        console.warn('公告弹窗元素未找到');
        return;
    }
    
    // 缓存关闭按钮引用
    let closeBtn = popup.querySelector('.closePopup');
    
    // 关闭弹窗函数
    const closePopup = () => {
        popup.classList.remove('active');
        document.body.style.overflow = '';
        
        // 可选：重置滚动位置
        // window.scrollTo(0, parseInt(document.body.style.top || '0') * -1);
    };
    
    // 打开弹窗函数
    const openPopup = () => {
        popup.classList.add('active');
        document.body.style.overflow = 'hidden';
        
        // 如果关闭按钮还没缓存或动态变化，重新获取
        if (!closeBtn || !closeBtn.isConnected) {
            closeBtn = popup.querySelector('.closePopup');
        }
    };
    
    // 点击按钮打开弹窗
    announcementBtn.addEventListener('click', openPopup);
    
    // 关闭按钮点击事件（使用事件委托，即使按钮动态加载也能工作）
    popup.addEventListener('click', (e) => {
        if (e.target.classList.contains('closePopup') || 
            e.target.closest('.closePopup')) {
            closePopup();
        }
    });
    
    // 点击背景关闭
    popup.addEventListener('click', (e) => {
        if (e.target === popup) {
            closePopup();
        }
    });
    
    // ESC关闭
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && popup.classList.contains('active')) {
            closePopup();
            e.preventDefault(); // 防止浏览器默认行为
        }
    });
    
    // 防止弹窗内滚动穿透（针对移动端）
    popup.addEventListener('touchmove', (e) => {
        if (popup.classList.contains('active')) {
            e.preventDefault();
        }
    }, { passive: false });
});