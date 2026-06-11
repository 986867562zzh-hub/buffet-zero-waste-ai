# 自助餐零废弃AI智能管理系统 - 项目文件索引

> 课程: 智慧旅游专题研究 | 教师: 黃穎祚 | 澳门科技大学

---

## 📁 项目文件结构

```
D:\Quant_Projects\Quant_Projects\
│
├── 自助餐零废弃AI智能管理系统_完整方案.md    ← 📋 完整技术方案（含OpenAI API代码、数据库设计、商业模式）
│
└── buffet-demo/                              ← 💻 可运行的Live Demo
    ├── 开发过程文档.md                        ← 📝 本次开发过程完整记录（供课程提交）
    ├── app.py                                ← Flask主程序 (1050行)
    ├── run.py                                ← 启动脚本
    ├── start.bat                             ← Windows双击启动
    ├── .env                                  ← API Key配置文件
    ├── requirements.txt                      ← Python依赖
    ├── templates/                            ← 5个HTML页面模板
    ├── static/css/                           ← 样式表
    ├── static/js/                            ← 前端脚本
    ├── static/uploads/                       ← 上传图片目录
    └── data/dishes.json                      ← 菜品营养数据库
```

## 📋 两份核心文档

| 文档 | 用途 |
|------|------|
| **开发过程文档.md** | 提交给老师的开发过程记录：需求分析→技术方案→迭代记录→Bug修复→测试验证 |
| **自助餐零废弃AI智能管理系统_完整方案.md** | 完整技术白皮书：产品设计、API代码、数据库设计、商业模式、风险评估 |

## 🚀 当前状态

- ✅ Flask服务器运行中
- ✅ 访问地址：http://127.0.0.1:5000
- ✅ 产品一：拍照评分完整流程
- ✅ 产品二：多图上传→AI识别→智能搭配完整流程
- ✅ AI模式：Smart Demo（基于PIL实际图像分析）
