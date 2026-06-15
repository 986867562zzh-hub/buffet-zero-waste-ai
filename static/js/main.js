/**
 * 自助餐零废弃智能管理系统 - 前端交互
 */

// ============ 全局初始化 ============
document.addEventListener('DOMContentLoaded', function() {
    // 初始化所有 tooltip
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (el) {
        return new bootstrap.Tooltip(el);
    });

    // 初始化所有 popover
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (el) {
        return new bootstrap.Popover(el);
    });

    // 进度条动画
    document.querySelectorAll('.progress-bar').forEach(function(bar) {
        const width = bar.style.width;
        bar.style.width = '0%';
        setTimeout(function() {
            bar.style.width = width;
        }, 300);
    });

    // 折扣徽章脉冲动画
    const discountBadge = document.querySelector('.discount-badge');
    if (discountBadge) {
        discountBadge.classList.add('animate__animated', 'animate__pulse');
    }

    // 星级逐一亮起
    animateStars();
});

// ============ 星级动画 ============
function animateStars() {
    const stars = document.querySelectorAll('.stars .fa-star');
    if (!stars.length) return;

    stars.forEach(function(star, index) {
        star.style.opacity = '0';
        star.style.transform = 'scale(0) rotate(-180deg)';
        setTimeout(function() {
            star.style.transition = 'all 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275)';
            star.style.opacity = '1';
            star.style.transform = 'scale(1) rotate(0deg)';
        }, 200 + index * 150);
    });
}

// ============ 图片上传预览 ============
function previewImage(input, previewId) {
    const preview = document.getElementById(previewId);
    if (!preview) return;

    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
            preview.src = e.target.result;
            preview.style.display = 'block';
        };
        reader.readAsDataURL(input.files[0]);
    }
}

// ============ 倒计时器（食品安全提醒） ============
function startCountdown(elementId, minutes) {
    const el = document.getElementById(elementId);
    if (!el) return;

    let seconds = minutes * 60;

    function tick() {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        el.textContent = mins + ':' + (secs < 10 ? '0' : '') + secs;

        if (seconds <= 300) {
            el.classList.add('text-danger', 'fw-bold');
        }

        if (seconds > 0) {
            seconds--;
            setTimeout(tick, 1000);
        } else {
            el.textContent = '已过期';
            el.classList.add('text-decoration-line-through');
        }
    }

    tick();
}

// ============ 模拟下单 ============
function placeOrder(comboId, comboName, price) {
    const confirmed = confirm(
        '确认下单？\n\n' +
        '套餐：' + comboName + '\n' +
        '金额：¥' + price + '\n\n' +
        '取餐地点：酒店自助餐厅前台\n' +
        '请在30分钟内到店取餐'
    );

    if (confirmed) {
        const orderId = 'BF' + Date.now().toString(36).toUpperCase();
        alert(
            '🎉 下单成功！\n\n' +
            '订单号：' + orderId + '\n' +
            '套餐：' + comboName + '\n' +
            '金额：¥' + price + '\n\n' +
            '请于30分钟内到店取餐，出示订单号即可。\n' +
            '感谢您为减少食物浪费做出的贡献！🌱'
        );
    }
}

// ============ 打印折扣券 ============
function printCoupon() {
    const couponContent = document.querySelector('.discount-badge');
    if (!couponContent) return;

    const printWindow = window.open('', '_blank', 'width=400,height=500');
    printWindow.document.write('<html><head><title>折扣券</title>');
    printWindow.document.write('<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">');
    printWindow.document.write('</head><body class="p-4 text-center">');
    printWindow.document.write('<h3>自助餐零废弃 · 折扣券</h3>');
    printWindow.document.write(couponContent.outerHTML);
    printWindow.document.write('<p class="mt-3 small">出示此券享受对应折扣</p>');
    printWindow.document.write('</body></html>');
    printWindow.document.close();
    printWindow.print();
}

// ============ 触摸设备适配 ============
document.addEventListener('touchstart', function() {}, {passive: true});

// 防止iOS橡皮筋效果影响拖拽
document.addEventListener('touchmove', function(e) {
    if (e.target.closest('.upload-zone')) {
        e.preventDefault();
    }
}, {passive: false});

// ============ 键盘快捷键 ============
document.addEventListener('keydown', function(e) {
    // Ctrl+1: 跳转产品一
    if (e.ctrlKey && e.key === '1') {
        window.location.href = '/product1';
    }
    // Ctrl+2: 跳转产品二
    if (e.ctrlKey && e.key === '2') {
        window.location.href = '/product2';
    }
    // Escape: 返回首页
    if (e.key === 'Escape' && !e.target.closest('input, textarea')) {
        window.location.href = '/';
    }
});

// ============================================
// === v2 新增功能 ===
// ============================================

// ---- Toast 通知系统 ----
function showToast(title, message, type) {
    // type: 'success', 'error', 'warning', 'info'
    var container = document.getElementById('toastContainer');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container-custom';
        document.body.appendChild(container);
    }
    var icons = {
        success: '✅',
        error: '❌',
        warning: '⚠️',
        info: '💡'
    };
    var toast = document.createElement('div');
    toast.className = 'toast-custom toast-' + (type || 'info');
    toast.innerHTML =
        '<span class="toast-icon">' + (icons[type] || icons.info) + '</span>' +
        '<div class="toast-body-custom">' +
            '<div class="toast-title">' + escapeHtml(title) + '</div>' +
            '<div class="toast-msg">' + escapeHtml(message) + '</div>' +
        '</div>' +
        '<button class="toast-close" onclick="dismissToast(this)" aria-label="关闭通知">&times;</button>';
    container.appendChild(toast);
    setTimeout(function() { dismissToastByEl(toast); }, 5000);
}

function dismissToast(btn) {
    dismissToastByEl(btn.closest('.toast-custom'));
}
function dismissToastByEl(el) {
    if (!el || el.classList.contains('toast-exit')) return;
    el.classList.add('toast-exit');
    setTimeout(function() { if (el.parentNode) el.parentNode.removeChild(el); }, 300);
}
function escapeHtml(text) {
    var div = document.createElement('div');
    div.appendChild(document.createTextNode(text));
    return div.innerHTML;
}

// ---- Loading 遮罩 ----
function showLoading(text, subText) {
    var existing = document.getElementById('loadingOverlay');
    if (existing) return;
    var overlay = document.createElement('div');
    overlay.id = 'loadingOverlay';
    overlay.className = 'loading-overlay show';
    overlay.setAttribute('role', 'dialog');
    overlay.setAttribute('aria-modal', 'true');
    overlay.setAttribute('aria-label', text || '加载中');
    overlay.innerHTML =
        '<div class="loading-card">' +
            '<div class="loading-spinner" aria-hidden="true"></div>' +
            '<div class="loading-text">' + escapeHtml(text || 'AI 分析中...') + '</div>' +
            '<div class="loading-sub">' + escapeHtml(subText || '') + '</div>' +
        '</div>';
    document.body.appendChild(overlay);
    // 禁止背景滚动
    document.body.style.overflow = 'hidden';
}

function hideLoading() {
    var overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.classList.remove('show');
        overlay.style.display = 'none';
        document.body.removeChild(overlay);
        document.body.style.overflow = '';
    }
}

// ---- 上传区键盘支持 ----
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.upload-zone, .multi-upload-zone').forEach(function(zone) {
        zone.setAttribute('tabindex', '0');
        zone.setAttribute('role', 'button');
        if (!zone.getAttribute('aria-label')) {
            zone.setAttribute('aria-label', '点击或拖拽上传图片');
        }
        zone.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                var fileInput = zone.querySelector('input[type="file"]');
                if (fileInput) fileInput.click();
            }
        });
    });

    // 所有 form 提交自动显示 loading
    document.querySelectorAll('form[data-auto-loading]').forEach(function(form) {
        form.addEventListener('submit', function() {
            var btn = form.querySelector('button[type="submit"]');
            var text = btn ? btn.textContent.trim() : '处理中...';
            showLoading(text, '请稍候，正在 AI 分析...');
        });
    });
});

// ---- 骨架屏工具 ----
function showSkeleton(containerId, template) {
    var container = document.getElementById(containerId);
    if (!container) return;
    container.innerHTML = template;
    container.classList.add('skeleton-container');
}

function hideSkeleton(containerId) {
    var container = document.getElementById(containerId);
    if (!container) return;
    container.classList.remove('skeleton-container');
}

// ---- 全局表单提交 loading（通用） ----
function bindFormLoading(formId, btnId, loadingText) {
    var form = document.getElementById(formId);
    if (!form) return;
    form.addEventListener('submit', function() {
        var btn = document.getElementById(btnId);
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>' + (loadingText || '处理中...');
        }
        showLoading(loadingText || 'AI 分析中...', '请稍候，正在智能识别...');
    });
}

// ============================================
// === v2.6 新增: 优化增强功能 ===
// ============================================

// ---- 暗色模式手动切换 ----
(function() {
    var TOGGLE_KEY = 'zerodine-theme';
    // 初始化：优先读 localStorage，其次系统偏好
    var saved = localStorage.getItem(TOGGLE_KEY);
    if (saved === 'dark' || (!saved && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
        document.body.classList.add('dark-theme');
    }
    // 创建切换按钮
    function createThemeToggle() {
        var navbar = document.querySelector('.navbar .container');
        if (!navbar) return;
        var btn = document.createElement('button');
        btn.className = 'theme-toggle-btn';
        btn.setAttribute('aria-label', '切换暗色模式');
        btn.title = '切换暗色/亮色模式';
        updateIcon();
        btn.addEventListener('click', function() {
            document.body.classList.toggle('dark-theme');
            var isDark = document.body.classList.contains('dark-theme');
            localStorage.setItem(TOGGLE_KEY, isDark ? 'dark' : 'light');
            updateIcon();
        });
        // 插入到 navbar-toggler 之前
        var toggler = navbar.querySelector('.navbar-toggler');
        if (toggler) {
            toggler.parentNode.insertBefore(btn, toggler);
        } else {
            navbar.appendChild(btn);
        }
        function updateIcon() {
            var isDark = document.body.classList.contains('dark-theme');
            btn.innerHTML = isDark ? '<i class="fas fa-sun"></i>' : '<i class="fas fa-moon"></i>';
        }
    }
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', createThemeToggle);
    } else {
        createThemeToggle();
    }
})();

// ---- 撒花/纸屑特效 ----
var Confetti = {
    _canvas: null,
    _ctx: null,
    _particles: [],
    _animId: null,
    _colors: ['#ff6b6b','#ffa502','#2ed573','#1e90ff','#ff6348','#7bed9f',
              '#ffc312','#12CBC4','#ED4C67','#f368e0','#ff9ff3','#54a0ff'],

    fire: function(duration) {
        duration = duration || 4000;
        if (this._animId) return; // 已经在播放

        // 创建 canvas
        var canvas = document.createElement('canvas');
        canvas.className = 'confetti-canvas';
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        document.body.appendChild(canvas);
        this._canvas = canvas;
        this._ctx = canvas.getContext('2d');

        // 生成粒子
        this._particles = [];
        for (var i = 0; i < 150; i++) {
            this._particles.push({
                x: Math.random() * canvas.width,
                y: -20 - Math.random() * canvas.height * 0.6,
                w: Math.random() * 10 + 5,
                h: Math.random() * 6 + 3,
                color: this._colors[Math.floor(Math.random() * this._colors.length)],
                vx: (Math.random() - 0.5) * 3,
                vy: Math.random() * 3 + 2,
                rot: Math.random() * 360,
                rotV: (Math.random() - 0.5) * 10,
                opacity: 1
            });
        }

        var self = this;
        var start = Date.now();
        function animate() {
            var elapsed = Date.now() - start;
            var ctx = self._ctx;
            var canvas = self._canvas;
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            var stillAlive = false;
            for (var i = 0; i < self._particles.length; i++) {
                var p = self._particles[i];
                // 渐隐
                if (elapsed > duration - 800) {
                    p.opacity = Math.max(0, 1 - (elapsed - (duration - 800)) / 800);
                }
                if (p.opacity <= 0) continue;
                stillAlive = true;

                p.x += p.vx;
                p.vy += 0.05; // 微重力
                p.y += p.vy;
                p.rot += p.rotV;

                ctx.save();
                ctx.translate(p.x, p.y);
                ctx.rotate(p.rot * Math.PI / 180);
                ctx.globalAlpha = p.opacity;
                ctx.fillStyle = p.color;
                ctx.fillRect(-p.w/2, -p.h/2, p.w, p.h);
                ctx.restore();
            }

            if (stillAlive && elapsed < duration + 200) {
                self._animId = requestAnimationFrame(animate);
            } else {
                self.cleanup();
            }
        }
        this._animId = requestAnimationFrame(animate);

        // resize 监听
        this._resizeHandler = function() {
            if (self._canvas) {
                self._canvas.width = window.innerWidth;
                self._canvas.height = window.innerHeight;
            }
        };
        window.addEventListener('resize', this._resizeHandler);
    },

    cleanup: function() {
        if (this._animId) { cancelAnimationFrame(this._animId); this._animId = null; }
        if (this._canvas && this._canvas.parentNode) {
            this._canvas.parentNode.removeChild(this._canvas);
        }
        this._canvas = null;
        this._ctx = null;
        this._particles = [];
        if (this._resizeHandler) {
            window.removeEventListener('resize', this._resizeHandler);
            this._resizeHandler = null;
        }
    }
};

// ---- 滚动渐入揭示 ----
(function() {
    function initReveal() {
        var reveals = document.querySelectorAll('.reveal');
        if (!reveals.length) return;

        var observer = new IntersectionObserver(function(entries) {
            entries.forEach(function(entry) {
                if (entry.isIntersecting) {
                    entry.target.classList.add('revealed');
                    observer.unobserve(entry.target);
                }
            });
        }, {
            threshold: 0.15,
            rootMargin: '0px 0px -40px 0px'
        });

        reveals.forEach(function(el) {
            observer.observe(el);
        });
    }
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initReveal);
    } else {
        initReveal();
    }
})();

// ---- 数字滚动动画 ----
function animateCounters() {
    var counters = document.querySelectorAll('.stat-number[data-target]');
    if (!counters.length) return;

    var observer = new IntersectionObserver(function(entries) {
        entries.forEach(function(entry) {
            if (!entry.isIntersecting) return;
            var el = entry.target;
            var target = parseInt(el.getAttribute('data-target'));
            var suffix = el.getAttribute('data-suffix') || '';
            var prefix = el.getAttribute('data-prefix') || '';
            var duration = 1500;
            var startTime = null;

            function step(timestamp) {
                if (!startTime) startTime = timestamp;
                var progress = Math.min((timestamp - startTime) / duration, 1);
                // easeOutExpo
                var eased = progress === 1 ? 1 : 1 - Math.pow(2, -10 * progress);
                var current = Math.floor(eased * target);
                el.textContent = prefix + current + suffix;
                if (progress < 1) {
                    requestAnimationFrame(step);
                } else {
                    el.textContent = prefix + target + suffix;
                    el.classList.remove('counting');
                }
            }

            el.classList.add('counting');
            requestAnimationFrame(step);
            observer.unobserve(el);
        });
    }, { threshold: 0.5 });

    counters.forEach(function(c) { observer.observe(c); });
}

// ---- 进度条入场动画 ----
function animateProgressBars() {
    var bars = document.querySelectorAll('.progress-bar.animate-once');
    if (!bars.length) return;

    var observer = new IntersectionObserver(function(entries) {
        entries.forEach(function(entry) {
            if (!entry.isIntersecting) return;
            var bar = entry.target;
            var targetWidth = bar.getAttribute('data-width') || bar.style.width;
            bar.style.width = targetWidth;
            observer.unobserve(bar);
        });
    }, { threshold: 0.3 });

    bars.forEach(function(b) { observer.observe(b); });
}

// ---- 全局增强初始化 ----
document.addEventListener('DOMContentLoaded', function() {
    animateCounters();
    animateProgressBars();
});
