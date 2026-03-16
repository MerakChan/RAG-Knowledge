document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('loginForm');
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    const captchaInput = document.getElementById('captcha');
    const captchaImage = document.getElementById('captchaImage');
    const errorMessage = document.getElementById('errorMessage');
    
    let currentCaptcha = '';
    
    // 生成随机验证码
    function generateCaptcha() {
        const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
        let captcha = '';
        for (let i = 0; i < 4; i++) {
            captcha += chars.charAt(Math.floor(Math.random() * chars.length));
        }
        return captcha;
    }
    
    // 更新验证码显示
    function updateCaptcha() {
        currentCaptcha = generateCaptcha();
        captchaImage.textContent = currentCaptcha;
    }
    
    // 初始生成验证码
    updateCaptcha();
    
    // 点击刷新验证码
    captchaImage.addEventListener('click', updateCaptcha);
    
    // 登录表单提交
    loginForm.addEventListener('submit', (e) => {
        e.preventDefault();
        
        const username = usernameInput.value.trim();
        const password = passwordInput.value.trim();
        const captcha = captchaInput.value.trim().toUpperCase();
        
        // 验证输入
        if (!username || !password || !captcha) {
            showError('请填写所有必填字段');
            return;
        }
        
        // 验证码验证
        if (captcha !== currentCaptcha) {
            showError('验证码错误，请重新输入');
            updateCaptcha();
            return;
        }
        
        // 默认账号密码验证
        if (username === 'admin' && password === '123456') {
            // 登录成功，保存登录状态
            localStorage.setItem('isLoggedIn', 'true');
            
            // 重定向到聊天界面
            window.location.href = 'index.html';
        } else {
            showError('用户名或密码错误');
        }
    });
    
    // 显示错误信息
    function showError(message) {
        errorMessage.textContent = message;
        errorMessage.style.display = 'block';
        
        // 3秒后自动隐藏错误信息
        setTimeout(() => {
            errorMessage.style.display = 'none';
        }, 3000);
    }
});