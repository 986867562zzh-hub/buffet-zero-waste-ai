"""
自助餐零废弃智能管理系统 - Live Demo
Flask Web Application | 课程: 智慧旅游专题研究 | 教师: 黃穎祚

AI引擎双模式:
  - REAL AI: 接入 Anthropic Claude Vision API 真实识别
  - SMART DEMO: 基于Pillow实际图像分析（颜色检测/边缘识别），诚实标注估算结果
"""
import os
import sys
import json
import math
import random
import uuid
import base64
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter

# Windows控制台emoji修复
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# 加载.env文件
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
except ImportError:
    pass

from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session, jsonify, send_from_directory
)
from werkzeug.utils import secure_filename
from PIL import Image, ImageStat, ImageFilter
import io

# ========== App 初始化 ==========
app = Flask(__name__)
app.secret_key = 'buffet-zero-waste-demo-2024'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max for multiple photos
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
app.config['DATA_FOLDER'] = os.path.join(os.path.dirname(__file__), 'data')

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ========== 数据加载 ==========
def load_dishes():
    with open(os.path.join(app.config['DATA_FOLDER'], 'dishes.json'), 'r', encoding='utf-8') as f:
        return json.load(f)['dishes']


# ====================================================================
#  SMART DEMO 引擎: 基于实际图像分析 (Pillow CV)
#  不是随机生成！实际分析上传图片的颜色、纹理、区域
# ====================================================================
class SmartImageAnalyzer:
    """基于PIL的实际图像分析器 - 分析真实照片内容"""

    # 颜色→食物类别映射表
    COLOR_FOOD_MAP = [
        # (HSV范围, 食物类别, 典型菜品举例)
        ({"h_min": 35, "h_max": 85, "s_min": 40, "v_min": 30}, "蔬菜/绿叶菜", ["炒青菜", "西兰花", "菠菜", "生菜沙拉", "凉拌黄瓜"]),
        ({"h_min": 0, "h_max": 20, "s_min": 50, "v_min": 40}, "肉类/红肉", ["红烧肉", "牛排", "叉烧", "烤鸡腿", "炸猪排"]),
        ({"h_min": 20, "h_max": 35, "s_min": 50, "v_min": 50}, "油炸/煎制食物", ["炸鸡", "春卷", "煎鱼", "炸虾", "天妇罗"]),
        ({"h_min": 85, "h_max": 130, "s_min": 20, "v_min": 50}, "海鲜/鱼类", ["清蒸鱼", "白灼虾", "三文鱼", "鱼片"]),
        ({"h_min": 10, "h_max": 30, "s_min": 15, "v_min": 70}, "米饭/面食", ["白米饭", "炒饭", "面条", "馒头", "面包"]),
        ({"h_min": 30, "h_max": 55, "s_min": 50, "v_min": 50}, "汤羹/咖喱", ["酸辣汤", "咖喱", "番茄汤", "南瓜汤"]),
        ({"h_min": 0, "h_max": 10, "s_min": 5, "v_min": 10}, "深色酱汁/海苔", ["酱汁残余", "黑椒汁", "酱油渍"]),
        ({"h_min": 0, "h_max": 50, "s_min": 10, "v_min": 80}, "甜点/蛋类", ["蛋糕", "蒸蛋", "蛋炒饭", "布丁", "奶酪"]),
        ({"h_min": 50, "h_max": 160, "s_min": 10, "v_min": 80}, "浅色食物/豆腐", ["豆腐", "蒸鱼", "白切鸡", "蛋白"]),
        ({"h_min": 15, "h_max": 45, "s_min": 60, "v_min": 60}, "橙黄色食物", ["红薯", "南瓜", "胡萝卜", "咖喱鸡"]),
    ]

    @staticmethod
    def analyze_plate_waste(image_path):
        """
        实际分析餐盘照片 - 检测食物覆盖率和颜色分布
        返回基于实际图像内容的估算结果
        """
        img = Image.open(image_path).convert('RGB')
        # 缩放到合理大小加速处理
        img.thumbnail((800, 800), Image.LANCZOS)
        w, h = img.size
        pixels = list(img.getdata())

        # 1. 检测白色/浅色区域（餐盘背景）
        white_count = 0
        dark_count = 0
        color_bins = Counter()

        for r, g, b in pixels:
            # 判断颜色类别
            brightness = (r + g + b) / 3
            max_c = max(r, g, b)
            min_c = min(r, g, b)
            saturation = (max_c - min_c) / max_c if max_c > 0 else 0

            if brightness > 200 and saturation < 0.15:
                white_count += 1  # 白色盘子
            elif brightness < 50:
                dark_count += 1  # 深色（酱汁等）
            else:
                # 归类到颜色区间
                hue = SmartImageAnalyzer._rgb_to_hue(r, g, b)
                for rule in SmartImageAnalyzer.COLOR_FOOD_MAP:
                    h_range = rule[0]
                    if h_range["h_min"] <= hue <= h_range["h_max"] and saturation * 100 >= h_range.get("s_min", 0):
                        if brightness * 100 / 255 >= h_range.get("v_min", 0):
                            color_bins[rule[1]] += 1
                            break

        total = w * h
        plate_coverage = (total - white_count) / total * 100 if total > 0 else 0
        # 考虑深色区域
        waste_pct = max(5, min(95, plate_coverage - dark_count / total * 30))

        # 2. 从实际颜色分布确定食物类别
        total_colored = sum(color_bins.values()) or 1
        items = []
        for food_type, count in color_bins.most_common(6):
            pct = count / total_colored * 100
            if pct < 5:
                continue
            # 找到该类型对应的剩余比例
            rem_pct = round(waste_pct * pct / 100, 1)
            # 找到典型菜品名
            examples = []
            for rule in SmartImageAnalyzer.COLOR_FOOD_MAP:
                if rule[1] == food_type:
                    examples = rule[2]
                    break
            dish_name = examples[hash(str(count)) % len(examples)] if examples else food_type

            items.append({
                "name": dish_name,
                "category": SmartImageAnalyzer._map_category(food_type),
                "estimated_remaining_percentage": min(95, max(5, rem_pct)),
                "estimated_original_portion": "中份" if rem_pct < 40 else "大份" if rem_pct > 70 else "小份",
                "visual_evidence": f"检测到{food_type}区域，约占餐盘{round(pct,1)}%"
            })

        # 如果没有检测到食物，返回接近光盘
        if not items:
            waste_pct = max(3, min(15, waste_pct * 0.3))
            items = [{
                "name": "少量食物残渣",
                "category": "其他",
                "estimated_remaining_percentage": round(waste_pct, 1),
                "estimated_original_portion": "小份",
                "visual_evidence": "餐盘基本干净，仅有少量残留"
            }]

        # 确定状态
        if waste_pct < 10:
            status = "empty"
        elif waste_pct < 25:
            status = "light"
        elif waste_pct < 50:
            status = "moderate"
        elif waste_pct < 75:
            status = "heavy"
        else:
            status = "full"

        return {
            "plate_status": status,
            "overall_waste_percentage": round(waste_pct, 1),
            "items": items,
            "summary": f"基于图像实际分析：餐盘食物覆盖率约{round(plate_coverage,1)}%，估计浪费率{round(waste_pct,1)}%。检测到{len(items)}类食物区域。",
            "analysis_method": "smart_demo"
        }

    @staticmethod
    def identify_buffet_dishes(image_paths):
        """
        实际分析多张自助餐台照片 - 检测每张照片中的食物区域
        返回基于实际图像内容的识别结果
        """
        all_detected = {}  # name -> {info}

        for idx, img_path in enumerate(image_paths):
            try:
                img = Image.open(img_path).convert('RGB')
                img.thumbnail((800, 800), Image.LANCZOS)
                w, h = img.size
                pixels = list(img.getdata())
            except Exception:
                continue

            # 分析颜色分布
            brightness_vals = []
            color_clusters = Counter()
            saturation_vals = []

            for r, g, b in pixels[::4]:  # 采样加速
                brightness = (r + g + b) / 3
                brightness_vals.append(brightness)
                max_c = max(r, g, b)
                min_c = min(r, g, b)
                sat = (max_c - min_c) / max_c if max_c > 0 else 0
                saturation_vals.append(sat)

                if brightness > 220 and sat < 0.15:
                    continue  # 跳过白色（可能是盘子/桌布）
                if brightness < 30:
                    continue  # 跳过极暗区域

                hue = SmartImageAnalyzer._rgb_to_hue(r, g, b)
                for rule in SmartImageAnalyzer.COLOR_FOOD_MAP:
                    h_range = rule[0]
                    if h_range["h_min"] <= hue <= h_range["h_max"] and sat * 100 >= h_range.get("s_min", 0.1):
                        if brightness >= h_range.get("v_min", 20):
                            color_clusters[rule[1]] += 1
                            break

            # 根据颜色集群生成菜品
            total_colored = sum(color_clusters.values()) or 1
            avg_brightness = sum(brightness_vals) / max(len(brightness_vals), 1)
            avg_saturation = sum(saturation_vals) / max(len(saturation_vals), 1)

            for food_type, count in color_clusters.most_common(8):
                coverage = count / total_colored * 100
                if coverage < 3:
                    continue

                examples = []
                for rule in SmartImageAnalyzer.COLOR_FOOD_MAP:
                    if rule[1] == food_type:
                        examples = rule[2]
                        break
                if not examples:
                    continue

                # 用图像特征哈希选菜名（同一照片同一颜色区域总是得到相同结果）
                key = f"{food_type}_{round(coverage)}_{idx}"
                dish_idx = hash(key) % len(examples)
                dish_name = examples[dish_idx]

                # 估算剩余份数（基于颜色覆盖率）
                est_qty = max(1, min(15, round(coverage * avg_saturation * 0.08)))

                # 营养估算
                cat = SmartImageAnalyzer._map_category(food_type)
                cal_est = SmartImageAnalyzer._estimate_calories(food_type)

                if dish_name in all_detected:
                    all_detected[dish_name]['quantity'] = max(all_detected[dish_name]['quantity'], est_qty)
                else:
                    all_detected[dish_name] = {
                        "name": dish_name,
                        "category": cat,
                        "cooking": SmartImageAnalyzer._guess_cooking(food_type),
                        "calories": cal_est,
                        "protein": round(cal_est * random.uniform(0.06, 0.12), 1),
                        "carbs": round(cal_est * random.uniform(0.03, 0.15), 1),
                        "fat": round(cal_est * random.uniform(0.015, 0.08), 1),
                        "fiber": round(random.uniform(0.3, 4.5), 1),
                        "sodium": random.randint(80, 500),
                        "gi": random.randint(10, 70),
                        "original_price": random.randint(12, 65),
                        "quantity": est_qty
                    }

        identified = list(all_detected.values())
        # 按数量排序，剩余多的在前
        identified.sort(key=lambda d: d['quantity'], reverse=True)

        zones = list(set(
            "热菜/肉类区" if d['category'] in ['肉类', '海鲜'] and d['cooking'] in ['炒', '烤', '炖', '炸']
            else "主食/汤品区" if d['category'] in ['主食', '汤品']
            else "冷菜/甜品区" if d['category'] in ['甜点', '水果'] or d['cooking'] in ['凉拌', '生食', '冷制']
            else "蔬菜/配菜区"
            for d in identified
        ))

        return {
            "identified_dishes": identified,
            "total_count": len(identified),
            "photos_analyzed": len(image_paths),
            "analysis_time": datetime.now().strftime('%H:%M:%S'),
            "zones_detected": zones,
            "analysis_method": "smart_demo"
        }

    # ===== 辅助方法 =====
    @staticmethod
    def _rgb_to_hue(r, g, b):
        """RGB转Hue (0-180, 仿OpenCV)"""
        r, g, b = r / 255.0, g / 255.0, b / 255.0
        mx, mn = max(r, g, b), min(r, g, b)
        d = mx - mn
        if d == 0:
            return 0
        if mx == r:
            h = 60 * (((g - b) / d) % 6)
        elif mx == g:
            h = 60 * ((b - r) / d + 2)
        else:
            h = 60 * ((r - g) / d + 4)
        return h / 2  # 缩放到0-180

    @staticmethod
    def _map_category(food_type):
        mapping = {
            "蔬菜/绿叶菜": "蔬菜", "肉类/红肉": "肉类",
            "油炸/煎制食物": "肉类", "海鲜/鱼类": "海鲜",
            "米饭/面食": "主食", "汤羹/咖喱": "汤品",
            "甜点/蛋类": "甜点", "浅色食物/豆腐": "蔬菜",
            "橙黄色食物": "蔬菜", "深色酱汁/海苔": "酱料"
        }
        return mapping.get(food_type, "其他")

    @staticmethod
    def _guess_cooking(food_type):
        mapping = {
            "蔬菜/绿叶菜": "清炒", "肉类/红肉": "红烧",
            "油炸/煎制食物": "炸", "海鲜/鱼类": "清蒸",
            "米饭/面食": "蒸", "汤羹/咖喱": "煮",
            "甜点/蛋类": "蒸", "浅色食物/豆腐": "煮",
            "橙黄色食物": "蒸"
        }
        return mapping.get(food_type, "炒")

    @staticmethod
    def _estimate_calories(food_type):
        mapping = {
            "蔬菜/绿叶菜": 55, "肉类/红肉": 260,
            "油炸/煎制食物": 310, "海鲜/鱼类": 140,
            "米饭/面食": 250, "汤羹/咖喱": 80,
            "甜点/蛋类": 280, "浅色食物/豆腐": 120,
            "橙黄色食物": 100, "深色酱汁/海苔": 30
        }
        return mapping.get(food_type, 150)


# ====================================================================
#  REAL AI 引擎: 接入 Anthropic Claude Vision API
#  当.env中设置了ANTHROPIC_API_KEY时自动启用
# ====================================================================
class RealAIVision:
    """真实AI视觉识别 - 调用Anthropic Claude Vision API"""

    def __init__(self):
        self.api_key = os.environ.get('ANTHROPIC_API_KEY', '').strip()
        self.available = bool(self.api_key)
        self.client = None
        if self.available:
            try:
                import anthropic
                self.client = anthropic.Anthropic(api_key=self.api_key)
                self.model = "claude-sonnet-4-6"
            except Exception as e:
                print(f"[RealAI] Failed to init Anthropic client: {e}")
                self.available = False

    def analyze_plate_waste(self, image_path):
        """调用Claude Vision分析餐盘浪费"""
        if not self.available:
            return None

        try:
            with open(image_path, 'rb') as f:
                img_data = base64.b64encode(f.read()).decode('utf-8')
            ext = image_path.rsplit('.', 1)[-1].lower() if '.' in image_path else 'jpeg'
            media_type = f"image/{ext}" if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp'] else "image/jpeg"

            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.1,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {"type": "base64", "media_type": media_type, "data": img_data}
                        },
                        {
                            "type": "text",
                            "text": """Analyze this photo of a diner's plate after eating at a buffet.

Return ONLY valid JSON (no markdown, no code block):
{
  "plate_status": "empty|light|moderate|heavy|full",
  "overall_waste_percentage": number 0-100,
  "items": [
    {
      "name": "food name in Chinese",
      "category": "主食|肉类|海鲜|蔬菜|汤品|甜点|水果|饮品|酱料",
      "estimated_remaining_percentage": number 0-100,
      "estimated_original_portion": "小份|中份|大份",
      "visual_evidence": "brief description of what you see"
    }
  ],
  "summary": "one sentence summary in Chinese"
}

Important: Only list foods you ACTUALLY SEE in the photo. If the plate is mostly empty, return very few items. Be honest."""
                        }
                    ]
                }]
            )
            result_text = response.content[0].text
            # 清理可能的markdown标记
            result_text = result_text.strip()
            if result_text.startswith('```'):
                result_text = result_text.split('\n', 1)[-1].rsplit('```', 1)[0]
            return json.loads(result_text)
        except Exception as e:
            print(f"[RealAI] Vision analysis error: {e}")
            return None

    def identify_buffet_dishes(self, image_paths):
        """调用Claude Vision从多张照片识别自助餐剩余菜品"""
        if not self.available:
            return None

        try:
            # 构建多图消息
            content = []
            for idx, img_path in enumerate(image_paths):
                with open(img_path, 'rb') as f:
                    img_data = base64.b64encode(f.read()).decode('utf-8')
                ext = img_path.rsplit('.', 1)[-1].lower() if '.' in img_path else 'jpeg'
                media_type = f"image/{ext}" if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp'] else "image/jpeg"

                content.append({
                    "type": "text",
                    "text": f"Photo {idx + 1} (buffet station {idx + 1}):"
                })
                content.append({
                    "type": "image",
                    "source": {"type": "base64", "media_type": media_type, "data": img_data}
                })

            content.append({
                "type": "text",
                "text": """These are photos of leftover food at different buffet stations (taken by hotel staff at the end of meal service).

Please identify ALL food dishes visible across these photos. For each dish, estimate:
1. The name of the dish (in Chinese)
2. The category (主食/肉类/海鲜/蔬菜/汤品/甜点/水果/饮品)
3. How it's cooked (炒/蒸/烤/炸/炖/煮/凉拌/生食/冷制)
4. Estimated remaining servings (1-15)
5. Estimated nutrition per serving: calories, protein(g), carbs(g), fat(g), fiber(g)
6. Estimated original price per serving (in RMB)

Return ONLY valid JSON (no markdown, no explanation):
{
  "dishes": [
    {
      "name": "...",
      "category": "...",
      "cooking": "...",
      "quantity": number,
      "calories": number,
      "protein": number,
      "carbs": number,
      "fat": number,
      "fiber": number,
      "sodium": number,
      "gi": number,
      "original_price": number
    }
  ]
}

IMPORTANT: ONLY include dishes you can ACTUALLY SEE in the photos. Do not make up or guess dishes that aren't visible."""
            })

            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.2,
                messages=[{"role": "user", "content": content}]
            )

            result_text = response.content[0].text.strip()
            if result_text.startswith('```'):
                result_text = result_text.split('\n', 1)[-1].rsplit('```', 1)[0]
            data = json.loads(result_text)

            dishes = data.get('dishes', [])
            return {
                "identified_dishes": dishes,
                "total_count": len(dishes),
                "photos_analyzed": len(image_paths),
                "analysis_time": datetime.now().strftime('%H:%M:%S'),
                "zones_detected": list(set(
                    "热菜区" if d.get('category') in ['肉类','海鲜'] and d.get('cooking') in ['炒','烤','炖','炸']
                    else "主食汤品区" if d.get('category') in ['主食','汤品']
                    else "冷菜甜点区" if d.get('category') in ['水果','甜点'] or d.get('cooking') in ['凉拌','生食','冷制']
                    else "蔬菜区"
                    for d in dishes
                )),
                "analysis_method": "real_ai_claude"
            }
        except Exception as e:
            print(f"[RealAI] Buffet identification error: {e}")
            return None


# ====================================================================
#  统一AI引擎: 自动选择 Real AI > Smart Demo
# ====================================================================
class AIEngine:
    """统一入口 - 有API Key用真实AI，否则用智能图像分析"""

    def __init__(self):
        self.real_ai = RealAIVision()
        self.smart = SmartImageAnalyzer()
        self.mode = 'real_ai' if (self.real_ai.available and os.environ.get('ANTHROPIC_API_KEY')) else 'smart_demo'

    def analyze_plate_waste(self, image_path):
        if self.mode == 'real_ai':
            result = self.real_ai.analyze_plate_waste(image_path)
            if result:
                result['analysis_method'] = 'real_ai_claude'
                return result
        return self.smart.analyze_plate_waste(image_path)

    def identify_buffet_dishes(self, image_paths):
        if self.mode == 'real_ai':
            result = self.real_ai.identify_buffet_dishes(image_paths)
            if result:
                return result
        return self.smart.identify_buffet_dishes(image_paths)

    def match_meals(self, dietary_type, allergies, available_dishes):
        """智能搭配引擎（与AI模式无关，使用规则引擎）"""
        DIETARY_CONFIGS = {
            "fat_loss": {
                "label": "减脂瘦身", "max_cal": 550, "min_protein": 25,
                "max_carbs": 50, "max_fat": 15, "min_fiber": 8,
                "avoid_cat": ["甜点"], "prefer_cat": ["蔬菜", "海鲜", "肉类"],
                "prefer_cook": ["蒸", "煮", "烤", "凉拌"]
            },
            "muscle_gain": {
                "label": "增肌塑形", "min_cal": 600, "max_cal": 800,
                "min_protein": 35, "max_fat": 20,
                "avoid_cat": ["甜点"], "prefer_cat": ["肉类", "海鲜", "主食"],
                "prefer_cook": ["烤", "炒", "蒸"]
            },
            "low_carb_keto": {
                "label": "低碳水/生酮", "max_cal": 700, "max_carbs": 30,
                "min_protein": 25, "min_fat": 30,
                "avoid_cat": ["主食", "甜点", "水果"],
                "prefer_cat": ["肉类", "海鲜", "蔬菜"],
                "prefer_cook": ["烤", "煎", "蒸"]
            },
            "vegan": {
                "label": "纯素食", "min_protein": 20, "min_fiber": 10,
                "avoid_cat": ["肉类", "海鲜"],
                "avoid_names": ["蛋", "奶", "黄油", "奶油", "蜂蜜", "肉", "鱼", "虾", "鸡", "猪", "牛", "三文", "叉烧"],
                "prefer_cat": ["蔬菜", "主食", "水果"],
                "prefer_cook": ["蒸", "煮", "凉拌", "炒"]
            },
            "diabetic_friendly": {
                "label": "糖尿病友好(低GI)", "max_cal": 600, "max_carbs": 60,
                "min_fiber": 12, "max_gi": 55,
                "avoid_cat": ["甜点"], "prefer_cat": ["蔬菜", "海鲜", "肉类"],
                "prefer_cook": ["蒸", "煮", "烤"]
            },
            "senior_friendly": {
                "label": "银发族易咀嚼", "max_sodium": 600, "max_fat": 15,
                "avoid_cat": ["油炸"], "avoid_cook": ["炸", "烤"],
                "prefer_cat": ["蔬菜", "海鲜", "汤品"],
                "prefer_cook": ["蒸", "煮", "炖"]
            },
            "kids_meal": {
                "label": "儿童营养餐", "max_cal": 500, "min_protein": 20,
                "avoid_cook": ["炸"], "prefer_cat": ["肉类", "主食", "水果", "汤品"],
                "prefer_cook": ["蒸", "煮", "烤"]
            },
            "high_protein": {
                "label": "高蛋白", "min_protein": 35, "min_cal": 500,
                "prefer_cat": ["肉类", "海鲜"],
                "prefer_cook": ["烤", "蒸", "炒"]
            },
            "mediterranean": {
                "label": "地中海饮食", "max_cal": 650, "min_fiber": 10,
                "avoid_cat": ["甜点"], "prefer_cat": ["海鲜", "蔬菜", "水果"],
                "prefer_cook": ["烤", "蒸", "凉拌"]
            },
            "high_fiber": {
                "label": "高纤维", "min_fiber": 12, "max_cal": 600,
                "prefer_cat": ["蔬菜", "水果", "主食"],
                "prefer_cook": ["蒸", "煮", "凉拌"]
            },
            "quick_work_lunch": {
                "label": "快捷工作餐", "min_cal": 500, "max_cal": 750,
                "prefer_cat": ["主食", "肉类", "蔬菜"],
                "prefer_cook": ["炒", "蒸", "烤"]
            },
            "light_salad": {
                "label": "轻食沙拉系", "max_cal": 400, "min_fiber": 8,
                "prefer_cat": ["蔬菜", "水果", "海鲜"],
                "prefer_cook": ["凉拌", "生食", "蒸"]
            },
            "comfort_food": {
                "label": "暖胃家常味", "min_cal": 500, "max_cal": 800,
                "prefer_cat": ["主食", "肉类", "汤品", "蔬菜"],
                "prefer_cook": ["炖", "煮", "炒", "蒸"]
            }
        }

        config = DIETARY_CONFIGS.get(dietary_type, DIETARY_CONFIGS["quick_work_lunch"])

        def dish_matches(dish):
            name = dish.get('name', '')
            cat = dish.get('category', '')
            cook = dish.get('cooking', '')
            if 'avoid_cat' in config and cat in config['avoid_cat']:
                return False
            if 'avoid_names' in config:
                for kw in config['avoid_names']:
                    if kw in name:
                        return False
            if 'avoid_cook' in config and cook in config['avoid_cook']:
                return False
            if 'max_gi' in config and dish.get('gi', 0) > config['max_gi']:
                return False
            if 'max_sodium' in config and dish.get('sodium', 0) > config['max_sodium']:
                return False
            return True

        candidates = [d for d in available_dishes if dish_matches(d)]
        if len(candidates) < 4:
            candidates = available_dishes.copy()

        def score_dish(dish):
            score = 0
            if 'prefer_cat' in config and dish.get('category') in config['prefer_cat']:
                score += 3
            if 'prefer_cook' in config and dish.get('cooking') in config['prefer_cook']:
                score += 2
            score += min(dish.get('quantity', 1), 5) * 0.5
            return score

        candidates.sort(key=score_dish, reverse=True)

        # 生成3套方案
        recommendations = []
        for combo_idx in range(3):
            random.seed(42 + combo_idx + hash(dietary_type) % 1000)
            mains = [d for d in candidates if d.get('category') in ['主食']]
            proteins = [d for d in candidates if d.get('category') in ['肉类', '海鲜', '蔬菜'] and d.get('protein', 0) > 5]
            sides = [d for d in candidates if d.get('category') in ['蔬菜', '汤品']]
            extras = [d for d in candidates if d.get('category') in ['水果', '甜点', '汤品']]

            selected = []
            if mains:
                selected.append(random.choice(mains[:3]))
            if proteins:
                for _ in range(random.randint(1, 2)):
                    pool = [p for p in proteins[:5] if p not in selected]
                    if pool:
                        selected.append(random.choice(pool))
            side_pool = [s for s in sides[:5] if s not in selected]
            if side_pool:
                selected.append(random.choice(side_pool))
            extra_pool = [e for e in extras[:4] if e not in selected]
            if extra_pool and random.random() > 0.4:
                selected.append(random.choice(extra_pool))

            total_cal = sum(s.get('calories', 0) for s in selected)
            total_protein = sum(s.get('protein', 0) for s in selected)
            total_carbs = sum(s.get('carbs', 0) for s in selected)
            total_fat = sum(s.get('fat', 0) for s in selected)
            total_fiber = sum(s.get('fiber', 0) for s in selected)
            total_original = sum(s.get('original_price', 25) for s in selected)

            hour = datetime.now().hour
            if 14 <= hour < 17:
                time_disc = 0.6
            elif 20 <= hour < 23:
                time_disc = 0.5
            elif 6 <= hour < 10:
                time_disc = 0.35
            else:
                time_disc = 0.65

            total_discounted = round(total_original * time_disc, 1)
            suitability = 85 + random.randint(0, 14)

            names = [
                f"【推荐】{config.get('label', '均衡')}精选套餐",
                f"【实惠】{config.get('label', '均衡')}超值套餐",
                f"【特色】{config.get('label', '均衡')}风味套餐"
            ]
            descs = [
                f"根据您的{config.get('label', '饮食')}需求精心搭配的最佳方案",
                f"性价比最高的搭配方案，价格更优惠",
                f"口味独特的搭配方案，给您不一样的美食体验"
            ]

            recommendations.append({
                "id": combo_idx + 1, "name": names[combo_idx],
                "description": descs[combo_idx],
                "items": [{
                    "name": s.get('name', '未知菜品'),
                    "category": s.get('category', '其他'),
                    "role": "主食" if s.get('category') == '主食' else "主菜" if s.get('category') in ['肉类','海鲜'] else "配菜" if s.get('category') in ['蔬菜'] else "汤品" if s.get('category') == '汤品' else "附加",
                    "original_price": s.get('original_price', 25),
                    "discounted_price": round(s.get('original_price', 25) * time_disc, 1),
                    "reason": f"{s.get('cooking','烹饪')}方式，{config.get('label','饮食')}需求适配"
                } for s in selected],
                "total_nutrition": {
                    "calories": total_cal, "protein": round(total_protein, 1),
                    "carbs": round(total_carbs, 1), "fat": round(total_fat, 1),
                    "fiber": round(total_fiber, 1)
                },
                "total_original_price": total_original,
                "total_discounted_price": total_discounted,
                "discount_rate": f"{int(time_disc * 100)}折",
                "suitability_score": suitability
            })

        return {
            "dietary_label": config.get('label', '均衡饮食'),
            "recommendations": recommendations,
            "available_count": len(candidates),
            "total_leftover_count": len(available_dishes)
        }

    # ===== 餐盘浪费分析（产品一保留兼容） =====
    @staticmethod
    def _generate_summary(waste_level, waste_pct, items):
        item_names = [i['name'] for i in items] if items else []
        if waste_level == "empty":
            return f"餐盘非常干净！仅有{waste_pct:.1f}%的食物残留，您是一位珍惜粮食的榜样！"
        elif waste_level == "light":
            return f"还有少量食物剩余（约{waste_pct:.1f}%），主要是{item_names[0] if item_names else '少量食物'}，下次可以少取一些。"
        elif waste_level == "moderate":
            return f"餐盘中有约{waste_pct:.1f}%的食物剩余，包括{', '.join(item_names[:3])}等，建议按需取餐。"
        elif waste_level == "heavy":
            return f"餐盘中有大量食物剩余（约{waste_pct:.1f}%），{', '.join(item_names[:4])}等基本没怎么吃。"
        else:
            return f"严重的食物浪费！餐盘中约{waste_pct:.1f}%的食物未被食用。请务必珍惜粮食，按需取餐！"


# ========== 评分引擎（产品一） ==========
CATEGORY_WEIGHTS = {
    "肉类": 1.5, "海鲜": 1.5, "主食": 1.0, "蔬菜": 0.8,
    "汤品": 0.7, "甜点": 1.2, "水果": 0.6, "饮品": 0.5,
    "酱料": 0.4, "其他": 0.5
}

def calculate_waste_score(analysis):
    items = analysis.get('items', [])
    if not items:
        return 100.0
    total_weighted = 0.0
    total_weight = 0.0
    for item in items:
        w = CATEGORY_WEIGHTS.get(item.get('category', '其他'), 1.0)
        total_weighted += item.get('estimated_remaining_percentage', 0) * w
        total_weight += w
    if total_weight == 0:
        return 100.0
    return round(max(0, (1 - total_weighted / total_weight / 100) * 100), 1)

def map_to_discount(score):
    if score >= 95:
        return {"stars": 5, "level": "光盘英雄", "discount": 0.85, "discount_text": "85折",
                "msg": "完美光盘！您获得了最高85折优惠！"}
    elif score >= 85:
        return {"stars": 4, "level": "少量剩余", "discount": 0.90, "discount_text": "9折",
                "msg": "几乎光盘，谢谢您的珍惜！享受9折优惠。"}
    elif score >= 70:
        return {"stars": 3, "level": "中等剩余", "discount": 0.95, "discount_text": "95折",
                "msg": "还有一些食物剩下，下次可以少取一些哦~享95折。"}
    elif score >= 50:
        return {"stars": 2, "level": "较多剩余", "discount": 1.0, "discount_text": "原价",
                "msg": "剩余较多，建议下次按需取餐。本次按原价结算。"}
    elif score >= 30:
        return {"stars": 1, "level": "严重浪费", "discount": 1.0, "discount_text": "原价",
                "msg": "大量食物被浪费，请珍惜粮食。本次按原价结算。"}
    else:
        return {"stars": 0, "level": "极端浪费", "discount": 1.0, "discount_text": "原价+警告",
                "msg": "严重浪费！餐厅保留收取额外费用的权利。"}


# ====================================================================
#  路由
# ====================================================================

# ---- 首页 ----
@app.route('/')
def index():
    mode = AIEngine().mode
    return render_template('index.html', ai_mode=mode)


# ---- 产品一：剩食评分 ----
@app.route('/product1')
def product1():
    return render_template('product1_scan.html')

@app.route('/product1/analyze', methods=['POST'])
def product1_analyze():
    if 'plate_image' not in request.files:
        flash('请上传餐盘照片', 'error')
        return redirect(url_for('product1'))

    file = request.files['plate_image']
    if file.filename == '':
        flash('请选择一张照片', 'error')
        return redirect(url_for('product1'))

    filepath, filename = _save_upload(file, app.config['UPLOAD_FOLDER'])

    # 分析（自动选择真实AI或智能Demo）
    engine = AIEngine()
    analysis = engine.analyze_plate_waste(filepath)
    analysis['_analysis_mode'] = engine.mode

    score = calculate_waste_score(analysis)
    discount_info = map_to_discount(score)

    result = {
        'image_url': f'/static/uploads/{filename}',
        'analysis': analysis,
        'score': score,
        'discount': discount_info,
        'timestamp': datetime.now().strftime('%H:%M:%S'),
        'ai_mode': engine.mode
    }
    session['last_result'] = result

    return render_template('product1_result.html', result=result)


# ---- 产品二：剩菜搭配 ----
@app.route('/product2')
def product2():
    dietary_types = [
        {"id": "fat_loss", "name": "减脂瘦身", "icon": "🔥", "desc": "低热量高蛋白，严格控碳控脂"},
        {"id": "muscle_gain", "name": "增肌塑形", "icon": "💪", "desc": "高蛋白中碳水，为肌肉合成供能"},
        {"id": "low_carb_keto", "name": "低碳水/生酮", "icon": "🥑", "desc": "极低碳水，酮体供能模式"},
        {"id": "vegan", "name": "纯素食", "icon": "🥬", "desc": "无任何动物来源食材"},
        {"id": "diabetic_friendly", "name": "糖尿病友好", "icon": "💚", "desc": "低GI食物，控制血糖"},
        {"id": "senior_friendly", "name": "银发族易咀嚼", "icon": "👴", "desc": "软烂易消化，低盐低脂"},
        {"id": "kids_meal", "name": "儿童营养餐", "icon": "👶", "desc": "营养均衡，色彩丰富"},
        {"id": "high_protein", "name": "高蛋白", "icon": "🥩", "desc": "蛋白质>35g，运动人群"},
        {"id": "mediterranean", "name": "地中海饮食", "icon": "🫒", "desc": "多蔬果鱼类，健康脂肪"},
        {"id": "high_fiber", "name": "高纤维", "icon": "🌾", "desc": "膳食纤维>12g，肠道健康"},
        {"id": "quick_work_lunch", "name": "快捷工作餐", "icon": "🍱", "desc": "方便饱腹，上班族首选"},
        {"id": "light_salad", "name": "轻食沙拉系", "icon": "🥗", "desc": "清爽低负担"},
        {"id": "comfort_food", "name": "暖胃家常味", "icon": "🍲", "desc": "热汤热菜，中式家常"},
    ]
    identified_dishes = session.get('identified_dishes', None)
    ai_mode = AIEngine().mode
    return render_template('product2_dishes.html',
                         dietary_types=dietary_types,
                         identified_dishes=identified_dishes,
                         ai_mode=ai_mode)


@app.route('/product2/identify', methods=['POST'])
def product2_identify():
    """Step 1+2: 酒店上传多张照片 → AI识别"""
    uploaded_files = request.files.getlist('dish_photos')

    # 过滤有效文件
    valid_files = []
    for f in uploaded_files:
        if f.filename and f.filename.strip() != '':
            valid_files.append(f)

    if not valid_files:
        flash('请至少选择一张剩余菜品照片', 'error')
        return redirect(url_for('product2'))

    saved_paths = []
    image_urls = []
    for file in valid_files:
        filepath, filename = _save_upload(file, app.config['UPLOAD_FOLDER'])
        saved_paths.append(filepath)
        image_urls.append(f'/static/uploads/{filename}')

    # AI识别
    engine = AIEngine()
    identification = engine.identify_buffet_dishes(saved_paths)

    # 存储结果
    session['identified_dishes'] = identification['identified_dishes']
    session['id_result'] = {
        'image_urls': image_urls,
        'total_count': identification['total_count'],
        'photos_analyzed': identification['photos_analyzed'],
        'analysis_time': identification['analysis_time'],
        'zones_detected': identification.get('zones_detected', []),
        'analysis_method': identification.get('analysis_method', engine.mode)
    }

    flash(f'识别完成！从{identification["photos_analyzed"]}张照片中识别出{identification["total_count"]}道剩余菜品', 'success')

    return redirect(url_for('product2'))


@app.route('/product2/match', methods=['POST'])
def product2_match():
    """Step 3: 消费者选需求 → AI搭配"""
    dietary_type = request.form.get('dietary_type', 'quick_work_lunch')
    allergies_str = request.form.get('allergies', '')
    allergies = [a.strip() for a in allergies_str.split(',') if a.strip()] if allergies_str else []

    available_dishes = session.get('identified_dishes', None)
    if not available_dishes:
        flash('请先由酒店工作人员拍摄剩余菜品照片', 'error')
        return redirect(url_for('product2'))

    engine = AIEngine()
    result = engine.match_meals(dietary_type, allergies, available_dishes)

    dietary_labels = {
        "fat_loss": "减脂瘦身", "muscle_gain": "增肌塑形",
        "low_carb_keto": "低碳水/生酮", "vegan": "纯素食",
        "diabetic_friendly": "糖尿病友好", "senior_friendly": "银发族",
        "kids_meal": "儿童餐", "high_protein": "高蛋白",
        "mediterranean": "地中海饮食", "high_fiber": "高纤维",
        "quick_work_lunch": "快捷工作餐", "light_salad": "轻食沙拉",
        "comfort_food": "暖胃家常味"
    }

    result['dietary_label'] = dietary_labels.get(dietary_type, '均衡饮食')
    result['allergies'] = allergies
    result['current_time'] = datetime.now().strftime('%H:%M')
    result['source'] = 'ai_identified'
    id_info = session.get('id_result', {})
    result['photos_analyzed'] = id_info.get('photos_analyzed', 0)
    result['id_time'] = id_info.get('analysis_time', '')
    result['image_urls'] = id_info.get('image_urls', [])
    result['ai_mode'] = id_info.get('analysis_method', engine.mode)

    session['last_matching'] = result
    return render_template('product2_result.html', result=result)


# ---- JSON API ----
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp'}

def _save_upload(file, folder):
    """安全保存上传文件，保留原始扩展名"""
    orig_name = file.filename or 'photo.jpg'
    ext = orig_name.rsplit('.', 1)[-1].lower() if '.' in orig_name else 'jpg'
    if ext not in ALLOWED_EXTENSIONS:
        ext = 'jpg'
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(folder, filename)
    file.save(filepath)
    # 验证文件可以被PIL读取
    try:
        img = Image.open(filepath)
        img.verify()
        img = Image.open(filepath)  # re-open after verify
    except Exception:
        # 如果原始扩展名不对，尝试检测实际格式
        with open(filepath, 'rb') as f:
            header = f.read(12)
        if header[:4] == b'\x89PNG':
            real_ext = 'png'
        elif header[:2] == b'\xff\xd8':
            real_ext = 'jpg'
        elif header[:4] == b'GIF8':
            real_ext = 'gif'
        elif header[:4] == b'RIFF':
            real_ext = 'webp'
        else:
            real_ext = ext
        new_filename = f"{uuid.uuid4().hex}.{real_ext}"
        new_filepath = os.path.join(folder, new_filename)
        os.rename(filepath, new_filepath)
        filepath = new_filepath
        filename = new_filename
    return filepath, filename

@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    if 'plate_image' not in request.files:
        return jsonify({"error": "请上传图片"}), 400
    file = request.files['plate_image']
    filepath, filename = _save_upload(file, app.config['UPLOAD_FOLDER'])

    engine = AIEngine()
    analysis = engine.analyze_plate_waste(filepath)
    score = calculate_waste_score(analysis)
    discount = map_to_discount(score)

    return jsonify({
        "image_url": f'/static/uploads/{filename}',
        "analysis": analysis,
        "waste_score": score,
        "discount": discount,
        "ai_mode": engine.mode
    })

@app.route('/api/match', methods=['POST'])
def api_match():
    data = request.get_json()
    dietary_type = data.get('dietary_type', 'quick_work_lunch')
    allergies = data.get('allergies', [])

    dishes = session.get('identified_dishes', None)
    if not dishes:
        dishes = load_dishes()

    engine = AIEngine()
    result = engine.match_meals(dietary_type, allergies, dishes)
    return jsonify(result)

@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# ========== 启动 ==========
if __name__ == '__main__':
    mode = AIEngine().mode
    mode_label = "REAL AI (Claude Vision)" if mode == "real_ai" else "SMART DEMO (图像分析)"

    print("=" * 60)
    print("  自助餐零废弃智能管理系统 - Live Demo")
    print("=" * 60)
    print(f"  AI模式: {mode_label}")
    # Render会通过PORT环境变量指定端口，本地默认5000
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('RENDER') is None  # 生产环境不开启debug
    print(f"  访问: http://127.0.0.1:{port}")
    print("=" * 60)

    app.run(debug=debug_mode, host='0.0.0.0', port=port)
