// 标准 Vue 2 实例化，main.js 只是个文件名，你想叫 app.js 也行
new Vue({
	el: '#link-app',
	data: {
		website_data: typeof website_data !== 'undefined' ? website_data : []
	},
	computed: {
		topData() {
			return this.website_data.filter(item => item.layout === 'top');
		},
		bottomData() {
			return this.website_data.filter(item => item.layout === 'bottom');
		}
	}
});