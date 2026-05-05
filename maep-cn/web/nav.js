/* Shared navigation — injected into every page */
document.addEventListener('DOMContentLoaded', () => {
    const navItems = [
        { href: 'index.html', label: '首页' },
        { href: 'motivation.html', label: '价值与意义' },
        { href: 'protocol.html', label: '协议设计' },
        { href: 'experiments.html', label: '实验结果' },
        { href: 'comparison.html', label: '已有工作' },
        { href: 'demo.html', label: '在线演示' },
        { href: 'future.html', label: '未来展望' },
    ];

    const currentPage = location.pathname.split('/').pop() || 'index.html';

    const nav = document.createElement('nav');
    nav.className = 'nav';
    nav.innerHTML = `
        <div class="nav-inner">
            <a href="index.html" class="nav-logo">MAEP<span class="accent">-CN</span></a>
            <div class="nav-links">
                ${navItems.map(item =>
                    `<a href="${item.href}" class="${item.href === currentPage ? 'active' : ''}">${item.label}</a>`
                ).join('')}
            </div>
            <button class="nav-toggle" onclick="this.parentElement.classList.toggle('open')">&#9776;</button>
        </div>
    `;
    document.body.prepend(nav);

    // Footer
    const existingFooter = document.querySelector('.footer');
    if (!existingFooter) {
        const footer = document.createElement('footer');
        footer.className = 'footer';
        footer.innerHTML = `
            <div class="container">
                <p>MAEP-CN — 多智能体执行协议（中国版） | <a href="https://github.com" class="footer-link">GitHub</a></p>
                <p class="footer-sub">基于预付费余额 · 随用随扣 · 毫秒结算 · 最小信任</p>
            </div>
        `;
        document.body.appendChild(footer);
    }
});
