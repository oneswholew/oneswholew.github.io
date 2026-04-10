// notice.js - 豪华增强版（丝滑淡入淡出 + 性能优化）
document.addEventListener('DOMContentLoaded', function() {
    const announcementBtn = document.getElementById('announcementBtn');
    const popup = document.getElementById('announcementPopup');
    
    if (!announcementBtn || !popup) {
        console.warn('公告弹窗元素未找到');
        return;
    }
    
    const ANIMATION_DURATION = 300;  // 动画时长常量
    let closeBtn = popup.querySelector('.closePopup');
    let isAnimating = false;
    
    // 统一处理动画状态
    const setAnimating = (callback) => {
        if (isAnimating) return;
        isAnimating = true;
        
        callback();
        
        setTimeout(() => {
            isAnimating = false;
        }, ANIMATION_DURATION);
    };
    
    // 关闭弹窗函数
    const closePopup = () => {
        setAnimating(() => {
            popup.classList.remove('active');
            document.body.style.overflow = '';
        });
    };
    
    // 打开弹窗函数
    const openPopup = () => {
        setAnimating(() => {
            popup.classList.add('active');
            document.body.style.overflow = 'hidden';
            // 重新获取关闭按钮（防止动态加载问题）
            closeBtn = popup.querySelector('.closePopup');
        });
    };
    
    // 事件监听合并
    const handlePopupClick = (e) => {
        // 点击关闭按钮或背景
        if (e.target.classList.contains('closePopup') || 
            e.target.closest('.closePopup') ||
            e.target === popup) {
            closePopup();
        }
    };
    
    // 点击按钮打开弹窗
    announcementBtn.addEventListener('click', openPopup);
    
    // 弹窗点击处理（关闭按钮和背景）
    popup.addEventListener('click', handlePopupClick);
    
    // ESC关闭
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && popup.classList.contains('active')) {
            closePopup();
        }
    });
    
    // 移动端优化：阻止弹窗内滚动穿透
    popup.addEventListener('touchmove', (e) => {
        if (popup.classList.contains('active')) {
            e.preventDefault();
        }
    }, { passive: false });
});