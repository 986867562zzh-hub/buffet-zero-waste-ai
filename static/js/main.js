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
