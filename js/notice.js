// notice.js 完整修正版
document.addEventListener('DOMContentLoaded', function() {
	// 获取元素的正确方式
	const announcementBtn = document.getElementById('announcementBtn');
	const popup = document.getElementById('announcementPopup');

	// 确保获取关闭按钮的方式可靠
	const getCloseBtn = () => popup.querySelector('.closePopup');

	// 显示弹窗
	announcementBtn.addEventListener('click', () => {
		popup.classList.add('active');
		document.body.style.overflow = 'hidden';

		// 动态绑定关闭按钮（解决异步加载问题）
		const closeBtn = getCloseBtn();
		closeBtn.addEventListener('click', closePopup);
	});

	// 关闭功能
	const closePopup = () => {
		popup.classList.remove('active');
		document.body.style.overflow = '';

		// 移除事件监听防止内存泄漏
		const closeBtn = getCloseBtn();
		closeBtn.removeEventListener('click', closePopup);
	};

	// 点击背景关闭（增强判断）
	popup.addEventListener('click', (e) => {
		if (e.target === popup || e.target.closest('.closePopup')) {
			closePopup();
		}
	});

	// ESC关闭（增强兼容性）
	document.addEventListener('keyup', (e) => {
		if (e.key === 'Escape' && popup.classList.contains('active')) {
			closePopup();
		}
	});
});