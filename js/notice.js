// notice.js - 豪华增强版（丝滑淡入淡出 + 性能优化）
document.addEventListener('DOMContentLoaded', function() {
    const announcementBtn = document.getElementById('announcementBtn');
    const popup = document.getElementById('announcementPopup');
    
    if (!announcementBtn || !popup) {
        console.warn('公告弹窗元素未找到');
        return;
    }
    
    let closeBtn = popup.querySelector('.closePopup');
    let isAnimating = false;  // 防止动画冲突
    
    // 关闭弹窗函数
    const closePopup = () => {
        if (isAnimating) return;
        isAnimating = true;
        
        popup.classList.remove('active');
        document.body.style.overflow = '';
        
        // 动画结束后解锁
        setTimeout(() => {
            isAnimating = false;
        }, 300);  // 和CSS过渡时间一致
    };
    
    // 打开弹窗函数
    const openPopup = () => {
        if (isAnimating) return;
        isAnimating = true;
        
        popup.classList.add('active');
        document.body.style.overflow = 'hidden';
        
        // 重新获取关闭按钮（防止动态加载问题）
        closeBtn = popup.querySelector('.closePopup');
        
        setTimeout(() => {
            isAnimating = false;
        }, 300);
    };
    
    // 点击按钮打开弹窗
    announcementBtn.addEventListener('click', openPopup);
    
    // 关闭按钮点击
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
            e.preventDefault();
        }
    });
    
    // 移动端优化：阻止弹窗内滚动穿透
    popup.addEventListener('touchmove', (e) => {
        if (popup.classList.contains('active')) {
            e.preventDefault();
        }
    }, { passive: false });
});