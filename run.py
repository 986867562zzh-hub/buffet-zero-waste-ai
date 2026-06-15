"""
ZeroDine零膳 - 启动脚本
直接运行: python run.py
"""
import os
import sys
import subprocess

# Windows控制台emoji修复
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def main():
    print("=" * 60)
    print("🍽️  ZeroDine零膳")
    print("   AI视觉识别驱动的自助餐零废弃方案")
    print("=" * 60)
    print()

    # 检查依赖
    print("📦 检查依赖...")
    try:
        import flask
        import PIL
        print(f"   ✅ Flask {flask.__version__}")
        print(f"   ✅ Pillow {PIL.__version__}")
    except ImportError as e:
        print(f"   ❌ 缺少依赖: {e}")
        print()
        print("正在安装依赖...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("   ✅ 依赖安装完成")
        print()

    # 确保目录存在
    os.makedirs(os.path.join(os.path.dirname(__file__), 'static', 'uploads'), exist_ok=True)

    # 启动应用
    print("🚀 启动服务...")
    print()
    print(f"📍 本地访问: http://127.0.0.1:5000")
    print(f"📍 局域网访问: http://0.0.0.0:5000")
    print()
    print("📱 手机访问: 确保手机与电脑在同一WiFi，")
    print("   在命令行输入 ipconfig 查看本机IP地址，")
    print("   然后在手机浏览器输入 http://<你的IP>:5000")
    print()
    print("💡 提示: 按 Ctrl+C 停止服务")
    print("=" * 60)

    from app import app
    app.run(debug=True, host='0.0.0.0', port=5000)

if __name__ == '__main__':
    main()
