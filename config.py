"""
ZeroDine零膳 - 配置文件
集中管理所有魔法数字和环境配置
"""
import os

# ============ Flask 基础配置 ============
SECRET_KEY = os.environ.get("SECRET_KEY", "buffet-zero-waste-demo-2024")
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB

# ============ 路径配置 ============
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_FOLDER = os.path.join(BASE_DIR, "static")
UPLOAD_FOLDER = os.path.join(STATIC_FOLDER, "uploads")
DATA_FOLDER = os.path.join(BASE_DIR, "data")
REFERENCE_DIR = os.path.join(STATIC_FOLDER, "reference_dishes")
COMPOSITES_DIR = os.path.join(STATIC_FOLDER, "composites")

# ============ 热量追踪 ============
CALORIE_THRESHOLD_DEFAULT = 1800
CALORIE_THRESHOLD_MIN = 500
CALORIE_THRESHOLD_MAX = 4000

# ============ 浪费评分 & 折扣映射 ============
WASTE_SCORE_GRADES = [
    {"min": 90, "grade": "A", "label": "光盘达人", "discount": 0.85, "emoji": "🏆"},
    {"min": 75, "grade": "B", "label": "节约先锋", "discount": 0.90, "emoji": "🥈"},
    {"min": 60, "grade": "C", "label": "尚可改进", "discount": 0.95, "emoji": "🥉"},
    {"min": 0,  "grade": "D", "label": "浪费严重", "discount": 1.00, "emoji": "😅"},
]

# 评分惩罚权重（各类别剩余比例对得分的影响）
SCORE_PENALTY_STAPLE = {"over": 25, "over_factor": 50}      # 主食类
SCORE_PENALTY_MEAT = {"under": 15, "under_factor": 30}       # 肉类
SCORE_PENALTY_VEG = {"under": 20, "under_factor": 40}        # 蔬菜类
SCORE_PENALTY_SOUP = {"over": 15, "over_factor": 30}         # 汤品类
SCORE_PENALTY_DESSERT = {"over": 15, "over_factor": 30}      # 甜点
SCORE_PENALTY_FRUIT = {"under": 10, "under_factor": 20}      # 水果

# 食物类别权重（用于加权评分）
CATEGORY_WEIGHTS = {
    "肉类": 1.5,
    "海鲜": 1.5,
    "主食": 1.0,
    "蔬菜": 0.8,
    "汤品": 0.7,
    "甜点": 1.2,
    "水果": 0.6,
    "饮品": 0.5,
}

# ============ 搭配引擎 ============
DIETARY_LABELS = {
    "balanced": "均衡营养",
    "low_calorie": "低卡减脂",
    "high_protein": "高蛋白增肌",
    "low_carb": "低碳水",
    "low_fat": "低脂",
    "vegetarian": "素食",
    "vegan": "纯素",
    "diabetic": "糖尿病友好",
    "seafood": "海鲜偏好",
    "meat_lover": "无肉不欢",
    "light": "清淡口味",
    "spicy": "无辣不欢",
}

# 膳食角色
MEAL_ROLES = ["主食", "主菜", "配菜", "汤品"]
MEAL_ROLE_MIN_COUNTS = {"主食": 1, "主菜": 1, "配菜": 1, "汤品": 0}

# ============ AI 引擎配置 ============
AI_MAX_TOKENS_VISION = 2000
AI_MAX_TOKENS_ANALYSIS = 4000
AI_MAX_TOKENS_MATCH = 3000
AI_TEMPERATURE = 0.1
AI_MAX_TOKENS_IDENTIFY = 2000

# OpenAI 模型
OPENAI_VISION_MODEL = "gpt-4o"
OPENAI_TEXT_MODEL = "gpt-4o"

# ============ 菜品库管理 ============
DISH_REFERENCE_MAX_SIZE = 512
DISH_LIBRARY_PATH = os.path.join(DATA_FOLDER, "dish_library.json")
DISHES_DATA_PATH = os.path.join(DATA_FOLDER, "dishes.json")

# ============ 图像分析 ============
COLOR_SIMILARITY_WEIGHT = 0.25
HASH_WEIGHT = 0.45
EDGE_WEIGHT = 0.30
MATCH_THRESHOLD = 0.30
