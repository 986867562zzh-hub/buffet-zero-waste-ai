# ZeroDine零膳 - AI智能管理系统

> 课程: 智慧旅游专题研究 | 教师: 黃穎祚 | 澳门科技大学

---

## 📁 项目文件结构

```
buffet-demo/
│
├── app.py                    ← Flask主程序
├── run.py                    ← 启动脚本
├── config.py                 ← ⭐ 集中配置文件（魔法数字、路径、阈值等）
├── test_core.py              ← ⭐ 核心逻辑测试（评分引擎、折扣映射、热量估算）
├── start.bat                 ← Windows双击启动
├── .env                      ← API Key配置文件
├── requirements.txt          ← Python依赖
├── Procfile                  ← Render部署Procfile
│
├── templates/                ← 6个HTML页面模板
│   ├── base.html
│   ├── index.html
│   ├── product1_scan.html
│   ├── product1_result.html
│   ├── product2_dishes.html
│   └── product2_result.html
│
├── static/
│   ├── css/style.css         ← 自定义样式
│   └── js/main.js            ← 前端交互脚本
│
└── data/
    ├── dishes.json           ← 菜品营养数据库
    └── dish_library.json     ← 固定菜品库（含参考图base64）
```

## 🚀 本地运行

1. 安装依赖：
   ```
   pip install -r requirements.txt
   ```

2. 配置环境变量（可选，否则自动使用Smart Demo模式）：
   ```
   在 .env 文件中填入 ANTHROPIC_API_KEY 或 OPENAI_API_KEY
   ```

3. 启动服务器：
   ```
   python run.py
   ```
   或双击 `start.bat`

4. 访问 http://127.0.0.1:5000

## ☁️ 部署到 Render

1. 将项目推送至 GitHub
2. 在 Render 中新建 **Web Service**，选择该仓库
3. 配置：
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn run:app`
4. 在 Environment Variables 中添加 `ANTHROPIC_API_KEY` 或 `OPENAI_API_KEY`

## 🧪 运行测试

```
python -m pytest test_core.py -v
```

**注意**: 测试不需要 API Key 或 Flask 环境，只测试核心逻辑（评分引擎、折扣映射、热量估算）。

## ✅ 当前功能

- ✅ 产品一：拍照评分 + 热量追踪 完整流程
- ✅ 产品二：多图上传 → AI识别 → 智能搭配 完整流程
- ✅ AI模式：Real AI（Claude/GPT-4o Vision）+ Smart Demo（PIL图像分析）
- ✅ 一键演示模式（6步预设流程，适合课堂展示）
- ⭐ v2 新增：
  - 骨架屏加载、Toast通知、全屏Loading遮罩
  - 暗色模式自动适配
  - 无障碍键盘导航
  - 核心配置集中化（config.py）
  - 核心逻辑单元测试
  - 下单Modal（替代alert）
  - 移动端响应式优化
