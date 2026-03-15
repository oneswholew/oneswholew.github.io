// 背景模式切换功能 - 优化版
document.addEventListener('DOMContentLoaded', function() {
	const backgroundBtn = document.getElementById('backgroundBtn');

	if (!backgroundBtn || window.innerWidth <= 768) return;

	let isAnimating = false;
	let animationTimer = null; // 新增：动画计时器引用

	function toggleBackgroundMode() {
		if (isAnimating) return;

		isAnimating = true;

		if (document.body.classList.contains('background-mode')) {
			document.body.classList.remove('background-mode');
			backgroundBtn.textContent = '🌄';
			backgroundBtn.title = '只看背景';
		} else {
			document.body.classList.add('background-mode');
			backgroundBtn.textContent = '🔙';
			backgroundBtn.title = '点击返回';
		}

		// 清除之前的计时器（防止多次切换时混乱）
		if (animationTimer) clearTimeout(animationTimer);

		animationTimer = setTimeout(() => {
			isAnimating = false;
			animationTimer = null;
		}, 400); // 改为400ms，和CSS一致
	}

	backgroundBtn.addEventListener('click', function(e) {
		e.stopPropagation();
		toggleBackgroundMode();
	});

	// ESC退出
	document.addEventListener('keydown', function(e) {
		if (e.key === 'Escape' &&
			document.body.classList.contains('background-mode') &&
			!isAnimating) {
			toggleBackgroundMode();
		}
	});

	// 窗口大小改变
	window.addEventListener('resize', function() {
		if (window.innerWidth <= 768) {
			if (document.body.classList.contains('background-mode')) {
				document.body.classList.remove('background-mode');
				backgroundBtn.textContent = '🌄';
				backgroundBtn.title = '只看背景';
				// 重置动画状态
				if (animationTimer) clearTimeout(animationTimer);
				isAnimating = false;
				animationTimer = null;
			}
		}
	});

	// 公告按钮冲突处理
	const announcementBtn = document.getElementById('announcementBtn');
	if (announcementBtn) {
		announcementBtn.addEventListener('click', function() {
			if (document.body.classList.contains('background-mode') && !isAnimating) {
				toggleBackgroundMode();
			}
		});
	}
});

// 在文件末尾添加
function refreshBackground() {
	const bgUrl = 'https://tu.ltyuanfang.cn/api/fengjing.php?t=' + Date.now();
	document.body.style.backgroundImage = `url('${bgUrl}')`;
}

// // 双击背景按钮刷新背景（不干扰原有功能）
// backgroundBtn.addEventListener('dblclick', function(e) {
// 	e.stopPropagation();
// 	refreshBackground();
// 	// 可选：给个提示
// 	backgroundBtn.textContent = '🔄';
// 	setTimeout(() => {
// 		backgroundBtn.textContent = document.body.classList.contains('background-mode') ? '🔙' : '🌄';
// 	}, 500);
// });
