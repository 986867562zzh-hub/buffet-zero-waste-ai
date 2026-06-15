"""
ZeroDine零膳 — API 连接诊断
用法: python check_api.py
检查 DeepSeek / Claude API Key 配置和连通性
"""
import os, sys

def check():
    print("=" * 50)
    print("ZeroDine零膳 v2.6 — API 连接诊断")
    print("=" * 50)

    # 1. 加载 .env
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        try:
            from dotenv import load_dotenv
            load_dotenv(env_path)
            print(f"[OK] .env 已加载: {env_path}")
        except ImportError:
            print("[WARN] python-dotenv 未安装，pip install python-dotenv")
    else:
        print("[WARN] .env 文件不存在")

    # 2. 检查 DeepSeek
    ds_key = os.environ.get('DEEPSEEK_API_KEY', '').strip()
    print(f"\n--- DeepSeek ---")
    if not ds_key or ds_key == 'your-deepseek-key-here':
        print("[FAIL] DEEPSEEK_API_KEY 未配置或仍是占位符")
        print("  -> 前往 https://platform.deepseek.com/api_keys 获取")
    elif not ds_key.startswith('sk-'):
        print(f"[WARN] Key 格式异常（应以 sk- 开头），当前: {ds_key[:8]}...")
    elif len(ds_key) < 20:
        print(f"[WARN] Key 长度异常（{len(ds_key)}字符），真实 Key 通常 >35 字符")
    else:
        print(f"[OK] Key 格式正常 ({ds_key[:5]}...{ds_key[-4:]})")

        # 测试连接
        try:
            import requests
            r = requests.post(
                'https://api.deepseek.com/chat/completions',
                headers={
                    'Authorization': f'Bearer {ds_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': 'deepseek-chat',
                    'messages': [{'role': 'user', 'content': 'hi'}],
                    'max_tokens': 5
                },
                timeout=15
            )
            if r.status_code == 200:
                print(f"[OK] API 连接成功！模型可用")
            elif r.status_code == 401:
                print(f"[FAIL] API Key 无效 (401 Unauthorized)")
            elif r.status_code == 402:
                print(f"[FAIL] 账户余额不足 (402 Payment Required)")
            else:
                print(f"[FAIL] HTTP {r.status_code}: {r.text[:100]}")
        except Exception as e:
            print(f"[FAIL] 网络连接失败: {type(e).__name__}")
            print(f"  -> 检查是否需要代理/VPN: {str(e)[:100]}")

    # 3. 检查 Claude
    cl_key = os.environ.get('ANTHROPIC_API_KEY', '').strip()
    print(f"\n--- Claude ---")
    if not cl_key:
        print("[SKIP] ANTHROPIC_API_KEY 未配置（非必须，DeepSeek优先）")
    elif not cl_key.startswith('sk-ant-'):
        print(f"[WARN] Key 格式异常（应以 sk-ant- 开头）")
    else:
        print(f"[OK] Key 格式正常 ({cl_key[:8]}...{cl_key[-4:]})")

    # 4. 总结
    print(f"\n{'=' * 50}")
    has_ds = ds_key and ds_key != 'your-deepseek-key-here' and len(ds_key) > 20
    has_cl = cl_key and cl_key.startswith('sk-ant-')
    if has_ds or has_cl:
        print("[OK] 至少一个 API Key 已配置，可以启动")
    else:
        print("[ACTION REQUIRED] 请配置至少一个 API Key:")
        print("  1. 编辑 .env 文件")
        print("  2. 填入真实的 DEEPSEEK_API_KEY 或 ANTHROPIC_API_KEY")
        print("  3. 重新运行 python check_api.py")
    print("=" * 50)

if __name__ == '__main__':
    check()
