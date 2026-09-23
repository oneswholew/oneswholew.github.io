// 背景模式切换功能 - 优化版
document.addEventListener('DOMContentLoaded', function() {
	const backgroundBtn = document.getElementById('backgroundBtn');
	const ANIMATION_DURATION = 400; // 提取常量

	if (!backgroundBtn || window.innerWidth <= 768) return;

	let isAnimating = false;
	let animationTimer = null;

	function setBackgroundMode(active) {
		if (active) {
			document.body.classList.add('background-mode');
			backgroundBtn.textContent = '🔙';
			backgroundBtn.title = '点击返回';
		} else {
			document.body.classList.remove('background-mode');
			backgroundBtn.textContent = '🌄';
			backgroundBtn.title = '只看背景';
		}
	}

	function toggleBackgroundMode() {
		if (isAnimating) return;

		isAnimating = true;
		setBackgroundMode(!document.body.classList.contains('background-mode'));

		// 清除之前的计时器
		if (animationTimer) clearTimeout(animationTimer);

		animationTimer = setTimeout(() => {
			isAnimating = false;
			animationTimer = null;
		}, ANIMATION_DURATION);
	}

	// 重置状态
	function resetBackgroundMode() {
		if (document.body.classList.contains('background-mode')) {
			setBackgroundMode(false);
			// 重置动画状态
			if (animationTimer) clearTimeout(animationTimer);
			isAnimating = false;
			animationTimer = null;
		}
	}

	backgroundBtn.addEventListener('click', function(e) {
		e.stopPropagation();
		toggleBackgroundMode();
	});

	// ESC退出
	document.addEventListener('keydown', function(e) {
		if (e.key === 'Escape' && document.body.classList.contains('background-mode') && !isAnimating) {
			toggleBackgroundMode();
		}
	});

	// 窗口大小改变
	window.addEventListener('resize', function() {
		if (window.innerWidth <= 768) {
			resetBackgroundMode();
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

// 刷新背景图片
function refreshBackground() {
	const bgUrl = `https://tu.ltyuanfang.cn/api/fengjing.php?t=${Date.now()}`;
	document.body.style.backgroundImage = `url('${bgUrl}')`;
}