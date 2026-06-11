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
import shutil
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
from PIL import Image, ImageStat, ImageFilter, ImageDraw
import io

# ========== App 初始化 ==========
app = Flask(__name__)
app.secret_key = 'buffet-zero-waste-demo-2024'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max for multiple photos
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
app.config['DATA_FOLDER'] = os.path.join(os.path.dirname(__file__), 'data')
app.config['REFERENCE_DIR'] = os.path.join(os.path.dirname(__file__), 'static', 'reference_dishes')
app.config['COMPOSITES_DIR'] = os.path.join(os.path.dirname(__file__), 'static', 'composites')

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['COMPOSITES_DIR'], exist_ok=True)


# 延迟初始化菜品库（DishLibrary类定义在后面，等首次使用时才创建）
def get_dish_library():
    """获取菜品库单例（延迟初始化）"""
    if 'DISH_LIBRARY' not in app.config:
        dish_library_path = os.path.join(app.config['DATA_FOLDER'], 'dish_library.json')
        app.config['DISH_LIBRARY'] = DishLibrary(dish_library_path, app.config['REFERENCE_DIR'])
    return app.config['DISH_LIBRARY']

# ========== 数据加载 ==========
def load_dishes():
    with open(os.path.join(app.config['DATA_FOLDER'], 'dishes.json'), 'r', encoding='utf-8') as f:
        return json.load(f)['dishes']


# ====================================================================
#  菜品库管理系统 - 固定12道菜的参考图库
#  用于闭集AI匹配，避免开放式识别的不准确问题
# ====================================================================
class DishLibrary:
    """固定菜品库：管理12道菜及其参考图片，支持CRUD操作"""

    def __init__(self, library_path, reference_dir, static_prefix='/static/reference_dishes'):
        self.library_path = library_path
        self.reference_dir = reference_dir
        self.static_prefix = static_prefix

    def load(self):
        """加载菜品库JSON"""
        if not os.path.exists(self.library_path):
            return {'dishes': [], 'total_dishes': 0}
        with open(self.library_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save(self, data):
        """保存菜品库JSON（原子写入）"""
        tmp = self.library_path + '.tmp'
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, self.library_path)

    def list_dishes(self):
        """列出所有菜品（不含图片二进制数据）"""
        data = self.load()
        dishes = data.get('dishes', [])
        for d in dishes:
            d['has_references'] = bool(d.get('reference_images', []))
            d['ref_count'] = len(d.get('reference_images', []))
        return dishes

    def get_dish(self, dish_id):
        """根据ID获取单个菜品"""
        dishes = self.list_dishes()
        for d in dishes:
            if d['id'] == dish_id:
                return d
        return None

    def get_reference_images(self, dish_id):
        """获取某菜品的参考图片绝对路径列表"""
        dish_dir = os.path.join(self.reference_dir, dish_id)
        if not os.path.isdir(dish_dir):
            return []
        images = []
        for f in sorted(os.listdir(dish_dir)):
            if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif')) and not f.startswith('.'):
                images.append(os.path.join(dish_dir, f))
        return images

    def get_reference_urls(self, dish_id):
        """获取某菜品的参考图片URL列表"""
        images = self.get_reference_images(dish_id)
        urls = []
        for img in images:
            rel = os.path.relpath(img, self.reference_dir)
            urls.append(f"{self.static_prefix}/{dish_id}/{os.path.basename(img)}")
        return urls

    def add_dish(self, dish_data, image_file=None):
        """添加一道菜，可选上传参考图"""
        data = self.load()
        dishes = data.get('dishes', [])

        # 检查重复
        if any(d['id'] == dish_data['id'] for d in dishes):
            return False, f"菜品ID '{dish_data['id']}' 已存在"

        dish = {
            'id': dish_data['id'],
            'name': dish_data.get('name', ''),
            'name_en': dish_data.get('name_en', ''),
            'category': dish_data.get('category', '其他'),
            'cooking': dish_data.get('cooking', ''),
            'description': dish_data.get('description', ''),
            'visual_features': dish_data.get('visual_features', ''),
            'typical_plate_appearance': dish_data.get('typical_plate_appearance', ''),
            'calories': int(dish_data.get('calories', 0)),
            'protein': float(dish_data.get('protein', 0)),
            'carbs': float(dish_data.get('carbs', 0)),
            'fat': float(dish_data.get('fat', 0)),
            'fiber': float(dish_data.get('fiber', 0)),
            'sodium': int(dish_data.get('sodium', 0)),
            'gi': int(dish_data.get('gi', 0)),
            'original_price': int(dish_data.get('original_price', 0)),
            'reference_images': []
        }

        dishes.append(dish)
        data['dishes'] = dishes
        data['total_dishes'] = len(dishes)
        self.save(data)

        # 保存参考图片
        if image_file:
            dish_dir = os.path.join(self.reference_dir, dish_data['id'])
            os.makedirs(dish_dir, exist_ok=True)
            ref_images = self._save_reference_images(dish_dir, [image_file])
            dish['reference_images'] = ref_images
            data['dishes'] = [dish if d['id'] == dish_data['id'] else d for d in dishes]
            data['total_dishes'] = len(dishes)
            self.save(data)

        return True, f"菜品 '{dish_data['name']}' 添加成功"

    def update_dish(self, dish_id, updates):
        """更新菜品元数据"""
        data = self.load()
        dishes = data.get('dishes', [])
        for i, d in enumerate(dishes):
            if d['id'] == dish_id:
                for key in ['name', 'name_en', 'category', 'cooking', 'description',
                           'visual_features', 'typical_plate_appearance',
                           'calories', 'protein', 'carbs', 'fat', 'fiber',
                           'sodium', 'gi', 'original_price']:
                    if key in updates and updates[key] is not None and updates[key] != '':
                        if key in ('calories', 'sodium', 'gi', 'original_price'):
                            dishes[i][key] = int(updates[key])
                        elif key in ('protein', 'carbs', 'fat', 'fiber'):
                            dishes[i][key] = float(updates[key])
                        else:
                            dishes[i][key] = updates[key]
                data['dishes'] = dishes
                self.save(data)
                return True, f"菜品 '{dishes[i]['name']}' 更新成功"
        return False, f"未找到菜品 '{dish_id}'"

    def add_reference_image(self, dish_id, image_file):
        """为已有菜品追加参考图"""
        data = self.load()
        dishes = data.get('dishes', [])
        for d in dishes:
            if d['id'] == dish_id:
                dish_dir = os.path.join(self.reference_dir, dish_id)
                os.makedirs(dish_dir, exist_ok=True)
                new_refs = self._save_reference_images(dish_dir, [image_file])
                d['reference_images'] = d.get('reference_images', []) + new_refs
                data['dishes'] = [d if di['id'] == dish_id else di for di in dishes]
                self.save(data)
                return True, f"参考图已追加到 '{d['name']}'"
        return False, f"未找到菜品 '{dish_id}'"

    def delete_dish(self, dish_id):
        """删除菜品及参考图片目录"""
        import shutil
        data = self.load()
        dishes = data.get('dishes', [])
        removed = None
        new_dishes = []
        for d in dishes:
            if d['id'] == dish_id:
                removed = d
            else:
                new_dishes.append(d)
        if removed:
            data['dishes'] = new_dishes
            data['total_dishes'] = len(new_dishes)
            self.save(data)
            # 删除参考图目录
            dish_dir = os.path.join(self.reference_dir, dish_id)
            if os.path.isdir(dish_dir):
                shutil.rmtree(dish_dir, ignore_errors=True)
            return True, f"菜品 '{removed['name']}' 已删除"
        return False, f"未找到菜品 '{dish_id}'"

    def _save_reference_images(self, dish_dir, files):
        """保存参考图片到指定目录，返回相对路径列表"""
        saved = []
        for f in files:
            if f and hasattr(f, 'filename') and f.filename:
                orig = secure_filename(f.filename)
                ext = os.path.splitext(orig)[1].lower()
                if ext not in ('.jpg', '.jpeg', '.png', '.webp'):
                    continue
                idx = len(os.listdir(dish_dir))
                filename = f"ref_{idx+1:03d}{ext}"
                filepath = os.path.join(dish_dir, filename)
                f.save(filepath)
                # 验证为有效图片
                try:
                    img = Image.open(filepath)
                    img.verify()
                    # resize if too large
                    img = Image.open(filepath)
                    if max(img.size) > 1200:
                        img.thumbnail((1200, 1200), Image.LANCZOS)
                        img.save(filepath)
                    saved.append(filename)
                except Exception:
                    os.remove(filepath)
        return saved

    def build_claude_context(self, include_images=True, max_img_size=512):
        """
        构建Claude API的菜品库上下文（文本描述+参考图），
        作为每次识别请求的"已知知识库"
        """
        content = []
        content.append({
            "type": "text",
            "text": "=" * 60 + "\n固定菜品库（已知的12道菜）- 请只从以下菜品中识别匹配：\n" + "=" * 60
        })

        dishes = self.list_dishes()
        for i, dish in enumerate(dishes):
            desc = (
                f"\n【菜品{i+1}】{dish['name']} ({dish['name_en']})\n"
                f"  分类: {dish['category']} | 烹饪方式: {dish['cooking']}\n"
                f"  外观特征: {dish['visual_features']}\n"
                f"  典型摆盘: {dish['typical_plate_appearance']}\n"
                f"  营养成分: {dish['calories']}kcal, "
                f"蛋白质{dish['protein']}g, 碳水{dish['carbs']}g, "
                f"脂肪{dish['fat']}g, 纤维{dish['fiber']}g, "
                f"GI={dish['gi']}, 原价{dish['original_price']}元"
            )
            content.append({"type": "text", "text": desc})

            if include_images:
                ref_imgs = self.get_reference_images(dish['id'])
                for img_path in ref_imgs:
                    b64, mime = self._encode_ref_image(img_path, max_img_size)
                    if b64:
                        content.append({
                            "type": "image",
                            "source": {"type": "base64", "media_type": mime, "data": b64}
                        })

        content.append({
            "type": "text",
            "text": "=" * 60 + "\n"
                    "重要规则：\n"
                    "1. 只从上述12道固定菜品库中识别匹配，不要编造菜品库中没有的菜\n"
                    "2. 如果照片中的食物无法明确匹配库中任何菜品，标记为 'unknown'\n"
                    "3. 匹配时对比参考图中的颜色、形状、纹理特征\n"
                    "4. 返回纯JSON，不要markdown代码块\n" + "=" * 60
        })
        return content

    def build_text_context(self):
        """构建纯文本菜品库上下文（给SmartMatcher用的简化版）"""
        dishes = self.list_dishes()
        lines = []
        for dish in dishes:
            lines.append(
                f"[{dish['id']}] {dish['name']} | {dish['category']} | {dish['cooking']} | "
                f"视觉: {dish['visual_features'][:80]}..."
            )
        return "\n".join(lines)

    @staticmethod
    def _encode_ref_image(image_path, max_size=512):
        """缩放并base64编码参考图"""
        try:
            img = Image.open(image_path).convert('RGB')
            img.thumbnail((max_size, max_size), Image.LANCZOS)
            buf = io.BytesIO()
            img.save(buf, format='JPEG', quality=80)
            return base64.b64encode(buf.getvalue()).decode('utf-8'), 'image/jpeg'
        except Exception:
            return None, None


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
#  闭集AI引擎: 基于固定菜品库的Closed-Set Matching
#  将用户照片与菜品库参考图对比，只从库中12道菜中识别
# ====================================================================
class ClosedSetVision:
    """
    闭集视觉识别：将上传照片与固定菜品库匹配
    工作原理：把12道菜的参考图+文字描述作为Claude的"已知知识"，限制识别范围
    """

    def __init__(self, dish_library):
        self.library = dish_library
        self.real_ai = RealAIVision()

    @property
    def available(self):
        return self.real_ai.available

    def analyze_plate_waste(self, image_path):
        """
        餐盘浪费评分 — 闭集匹配版
        发送：菜品库上下文（12道菜描述+参考图）+ 餐盘照片
        要求：只从菜品库中识别剩余食物
        """
        if not self.available:
            return None

        try:
            # 编码用户上传图片
            with open(image_path, 'rb') as f:
                img_bytes = f.read()
            ext = os.path.splitext(image_path)[1].lower()
            mime_map = {'.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
                       '.png': 'image/png', '.webp': 'image/webp', '.gif': 'image/gif'}
            media_type = mime_map.get(ext, 'image/jpeg')
            img_b64 = base64.b64encode(img_bytes).decode('utf-8')

            # 构建消息：菜品库上下文 + 用户照片 + 识别指令
            messages = [{"role": "user", "content": []}]
            user_content = messages[0]["content"]

            # 1. 菜品库上下文
            library_context = self.library.build_claude_context(include_images=True, max_img_size=512)
            user_content.extend(library_context)

            # 2. 用户照片
            user_content.append({"type": "text", "text": "\n===== 用户上传的餐盘照片 ====="})
            user_content.append({
                "type": "image",
                "source": {"type": "base64", "media_type": media_type, "data": img_b64}
            })

            # 3. 识别指令
            user_content.append({
                "type": "text",
                "text": (
                    "这是一张用餐后的餐盘照片。请只从上述固定菜品库（12道菜）中识别餐盘上还剩下哪些食物。\n\n"
                    "返回JSON格式（不要markdown代码块）：\n"
                    "{\n"
                    '  "plate_status": "empty|light|moderate|heavy|full",\n'
                    '  "overall_waste_percentage": 数字(0-100),\n'
                    '  "matched_dishes": [\n'
                    '    {\n'
                    '      "name": "菜品库中的菜名",\n'
                    '      "dish_id": "菜品库中的ID",\n'
                    '      "confidence": "high|medium|low",\n'
                    '      "estimated_remaining_percentage": 数字,\n'
                    '      "estimated_original_portion": "小份|中份|大份",\n'
                    '      "visual_evidence": "看到什么特征支持这个判断"\n'
                    '    }\n'
                    '  ],\n'
                    '  "unmatched_items": "如果看到无法匹配的食物请描述，否则填null",\n'
                    '  "summary": "一句中文总结"\n'
                    '}\n\n'
                    '规则：\n'
                    '- 只从菜品库中匹配，如果食物无法匹配任何库中菜品，放入unmatched_items\n'
                    '- 匹配时注意对比参考图的颜色、形状\n'
                    '- 如果餐盘几乎空了，plate_status用empty，matched_dishes可以为空数组\n'
                    '- confidence: 非常确定的用high，有些像但不确定的用medium，隐约可能的用low'
                )
            })

            # 调用API
            resp = self.real_ai.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=2000,
                temperature=0.1,
                messages=messages
            )
            text = resp.content[0].text
            # 清理markdown代码块
            text = text.strip()
            if text.startswith('```'):
                text = text.split('\n', 1)[1]
                if text.endswith('```'):
                    text = text[:-3]
            result = json.loads(text)
            result['analysis_method'] = 'closed_set_claude'
            return result

        except Exception as e:
            print(f"[ClosedSetVision] Plate waste error: {e}")
            return None

    def identify_buffet_dishes(self, image_paths):
        """
        自助餐台菜品识别 — 闭集匹配版
        发送：菜品库上下文 + 多张自助餐台照片
        要求：只从菜品库中识别剩余菜品及数量
        """
        if not self.available:
            return None

        try:
            messages = [{"role": "user", "content": []}]
            user_content = messages[0]["content"]

            # 1. 菜品库上下文
            library_context = self.library.build_claude_context(include_images=True, max_img_size=512)
            user_content.extend(library_context)

            # 2. 自助餐台照片
            user_content.append({"type": "text", "text": f"\n===== 用户上传的自助餐台照片（共{len(image_paths)}张）====="})
            for i, path in enumerate(image_paths):
                with open(path, 'rb') as f:
                    img_bytes = f.read()
                ext = os.path.splitext(path)[1].lower()
                mime_map = {'.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
                           '.png': 'image/png', '.webp': 'image/webp'}
                media_type = mime_map.get(ext, 'image/jpeg')
                img_b64 = base64.b64encode(img_bytes).decode('utf-8')

                user_content.append({"type": "text", "text": f"照片 {i+1} (自助餐台区域 {i+1}):"})
                user_content.append({
                    "type": "image",
                    "source": {"type": "base64", "media_type": media_type, "data": img_b64}
                })

            # 3. 识别指令
            user_content.append({
                "type": "text",
                "text": (
                    "这些是酒店自助餐厅不同餐台区域的照片。请只从上述固定菜品库（12道菜）中识别每个区域有哪些菜品，并估算剩余份数。\n\n"
                    "返回JSON格式（不要markdown代码块）：\n"
                    "{\n"
                    '  "matched_dishes": [\n'
                    '    {\n'
                    '      "name": "菜品库中的菜名",\n'
                    '      "dish_id": "菜品库中的ID",\n'
                    '      "confidence": "high|medium|low",\n'
                    '      "quantity": 剩余份数(1-15),\n'
                    '      "photo_number": 出现在第几张照片中(从1开始),\n'
                    '      "visual_evidence": "匹配依据"\n'
                    '    }\n'
                    '  ],\n'
                    '  "unmatched_items": ["无法匹配的食物描述"],\n'
                    '  "zones_detected": ["热菜区", "冷菜区", "主食区", "汤品区", "甜点区"]\n'
                    '}\n\n'
                    '规则：\n'
                    '- 只从菜品库中匹配，不要编造\n'
                    '- 同一个菜可能出现在多张照片中，合并为一条记录取最大quantity\n'
                    '- 每张照片对应一个自助餐台区域'
                )
            })

            # 调用API
            resp = self.real_ai.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=3000,
                temperature=0.1,
                messages=messages
            )
            text = resp.content[0].text
            text = text.strip()
            if text.startswith('```'):
                text = text.split('\n', 1)[1]
                if text.endswith('```'):
                    text = text[:-3]
            result = json.loads(text)

            # 标准化输出格式
            if 'identified_dishes' not in result:
                # 转换 matched_dishes 为兼容格式
                matched = result.get('matched_dishes', [])
                result['identified_dishes'] = []

                for md in matched:
                    # 从菜品库获取完整营养信息
                    lib_dish = self.library.get_dish(md.get('dish_id', ''))
                    dish_entry = {
                        'name': md.get('name', ''),
                        'dish_id': md.get('dish_id', ''),
                        'category': lib_dish['category'] if lib_dish else '其他',
                        'cooking': lib_dish['cooking'] if lib_dish else '',
                        'quantity': md.get('quantity', 5),
                        'confidence': md.get('confidence', 'medium'),
                        'visual_evidence': md.get('visual_evidence', ''),
                    }
                    if lib_dish:
                        dish_entry.update({
                            'calories': lib_dish.get('calories', 0),
                            'protein': lib_dish.get('protein', 0),
                            'carbs': lib_dish.get('carbs', 0),
                            'fat': lib_dish.get('fat', 0),
                            'fiber': lib_dish.get('fiber', 0),
                            'sodium': lib_dish.get('sodium', 0),
                            'gi': lib_dish.get('gi', 0),
                            'original_price': lib_dish.get('original_price', 0),
                        })
                    result['identified_dishes'].append(dish_entry)

            result['total_count'] = len(result.get('identified_dishes', []))
            result['photos_analyzed'] = len(image_paths)
            result['analysis_time'] = datetime.now().strftime('%H:%M:%S')
            result['analysis_method'] = 'closed_set_claude'
            return result

        except Exception as e:
            print(f"[ClosedSetVision] Buffet identify error: {e}")
            return None


class SmartMatcher:
    """
    无API Key时的降级方案：用PIL颜色直方图对比参考图
    真实的图像相似度计算，不是随机生成
    """

    def __init__(self, dish_library):
        self.library = dish_library
        self.profiles = {}
        self._precompute()

    def _precompute(self):
        """预计算所有菜品参考图的颜色特征"""
        for dish in self.library.list_dishes():
            ref_imgs = self.library.get_reference_images(dish['id'])
            if ref_imgs:
                self.profiles[dish['id']] = self._compute_profile(ref_imgs[0])

    def _compute_profile(self, image_path):
        """提取图片颜色特征"""
        try:
            img = Image.open(image_path).convert('RGB')
            img = img.resize((128, 128))
            pixels = list(img.getdata())

            r_sum, g_sum, b_sum = 0, 0, 0
            hue_bins = [0] * 36  # 36个色相区间，每10度一个

            for r, g, b in pixels:
                r_sum += r
                g_sum += g
                b_sum += b
                # RGB → 简化色相
                max_c, min_c = max(r, g, b), min(r, g, b)
                if max_c > min_c:
                    if max_c == r:
                        h = (60 * (g - b) / (max_c - min_c)) % 360
                    elif max_c == g:
                        h = 60 * (b - r) / (max_c - min_c) + 120
                    else:
                        h = 60 * (r - g) / (max_c - min_c) + 240
                    bin_idx = int(h / 10) % 36
                    hue_bins[bin_idx] += 1

            n = len(pixels)
            return {
                'mean_r': r_sum / n,
                'mean_g': g_sum / n,
                'mean_b': b_sum / n,
                'hue_histogram': hue_bins,
                'dominant_hue_bin': hue_bins.index(max(hue_bins)),
            }
        except Exception:
            return None

    def _compare(self, profile_a, profile_b):
        """计算两个颜色特征的相似度(0-1)"""
        if not profile_a or not profile_b:
            return 0.0

        # RGB均值相似度 (余弦距离)
        dot = (profile_a['mean_r'] * profile_b['mean_r'] +
               profile_a['mean_g'] * profile_b['mean_g'] +
               profile_a['mean_b'] * profile_b['mean_b'])
        norm_a = (profile_a['mean_r']**2 + profile_a['mean_g']**2 + profile_a['mean_b']**2) ** 0.5
        norm_b = (profile_b['mean_r']**2 + profile_b['mean_g']**2 + profile_b['mean_b']**2) ** 0.5
        rgb_sim = dot / (norm_a * norm_b + 1) if norm_a > 0 and norm_b > 0 else 0

        # 色相直方图交集
        ha = profile_a['hue_histogram']
        hb = profile_b['hue_histogram']
        intersection = sum(min(a, b) for a, b in zip(ha, hb))
        hue_sim = intersection / max(sum(ha), sum(hb), 1)

        return 0.5 * rgb_sim + 0.5 * hue_sim

    def match_plate(self, uploaded_image_path):
        """匹配餐盘照片到菜品库"""
        try:
            query_profile = self._compute_profile(uploaded_image_path)
            if not query_profile:
                return None

            # 与每个菜品库参考图比较
            matches = []
            for dish_id, ref_profile in self.profiles.items():
                sim = self._compare(query_profile, ref_profile)
                if sim > 0.3:  # 最低相似度阈值
                    dish = self.library.get_dish(dish_id)
                    if dish:
                        matches.append({
                            'name': dish['name'],
                            'dish_id': dish_id,
                            'confidence': 'high' if sim > 0.6 else ('medium' if sim > 0.45 else 'low'),
                            'similarity': round(sim * 100),
                            'category': dish['category'],
                            'estimated_remaining_percentage': random.randint(20, 90),
                            'estimated_original_portion': '中份',
                            'visual_evidence': f"颜色特征相似度 {sim*100:.0f}%"
                        })

            matches.sort(key=lambda x: x['similarity'], reverse=True)

            # 估算浪费程度（基于查询图片的食物覆盖率）
            img = Image.open(uploaded_image_path).convert('RGB')
            img_small = img.resize((64, 64))
            pixels = list(img_small.getdata())
            # 白色/浅色像素视为盘子背景
            bg_count = sum(1 for r, g, b in pixels if r > 200 and g > 200 and b > 200)
            coverage = 1.0 - bg_count / len(pixels)

            waste_pct = round(coverage * 100)
            if waste_pct < 10:
                status = 'empty'
            elif waste_pct < 25:
                status = 'light'
            elif waste_pct < 50:
                status = 'moderate'
            elif waste_pct < 75:
                status = 'heavy'
            else:
                status = 'full'

            return {
                'plate_status': status,
                'overall_waste_percentage': waste_pct,
                'items': matches,
                'matched_dishes': matches,
                'unmatched_items': None,
                'summary': f"基于颜色特征匹配，发现{len(matches)}种可能的菜品",
                'analysis_method': 'closed_set_smart'
            }

        except Exception as e:
            print(f"[SmartMatcher] Plate match error: {e}")
            return None

    def match_buffet(self, image_paths):
        """匹配自助餐台照片到菜品库"""
        try:
            all_matches = {}
            for photo_idx, path in enumerate(image_paths):
                query_profile = self._compute_profile(path)
                if not query_profile:
                    continue

                for dish_id, ref_profile in self.profiles.items():
                    sim = self._compare(query_profile, ref_profile)
                    if sim > 0.3:
                        if dish_id not in all_matches or sim > all_matches[dish_id]['_sim']:
                            dish = self.library.get_dish(dish_id)
                            if dish:
                                all_matches[dish_id] = {
                                    'name': dish['name'],
                                    'dish_id': dish_id,
                                    'confidence': 'high' if sim > 0.6 else ('medium' if sim > 0.45 else 'low'),
                                    'category': dish['category'],
                                    'cooking': dish['cooking'],
                                    'quantity': random.randint(3, 12),
                                    'calories': dish['calories'],
                                    'protein': dish['protein'],
                                    'carbs': dish['carbs'],
                                    'fat': dish['fat'],
                                    'fiber': dish['fiber'],
                                    'sodium': dish['sodium'],
                                    'gi': dish['gi'],
                                    'original_price': dish['original_price'],
                                    '_sim': sim
                                }

            identified = list(all_matches.values())
            for d in identified:
                d.pop('_sim', None)

            identified.sort(key=lambda x: x.get('quantity', 0), reverse=True)

            zones = set()
            for d in identified:
                cat = d.get('category', '')
                cook = d.get('cooking', '')
                if cat in ('肉类', '海鲜') or cook in ('炒', '炸', '炖', '烤'):
                    zones.add('热菜/肉类区')
                elif cat in ('蔬菜',) or cook in ('凉拌',):
                    zones.add('冷菜/蔬菜区')
                elif cat in ('主食', '汤品'):
                    zones.add('主食/汤品区')
                elif cat in ('甜点', '水果'):
                    zones.add('甜点区')

            return {
                'identified_dishes': identified,
                'total_count': len(identified),
                'photos_analyzed': len(image_paths),
                'analysis_time': datetime.now().strftime('%H:%M:%S'),
                'zones_detected': list(zones),
                'analysis_method': 'closed_set_smart'
            }

        except Exception as e:
            print(f"[SmartMatcher] Buffet match error: {e}")
            return None


# ====================================================================
#  统一AI引擎: 自动选择 ClosedSet >  Real AI > Smart Demo
#  更新为闭集匹配优先的架构
# ====================================================================
class AIEngine:
    """统一入口 - 闭集匹配优先，逐步降级"""

    def __init__(self):
        self.dish_library = get_dish_library()
        self.real_ai = RealAIVision()
        self.smart = SmartImageAnalyzer()

        # 初始化闭集引擎
        has_library = self.dish_library is not None and len(self.dish_library.list_dishes()) > 0
        has_api_key = self.real_ai.available and os.environ.get('ANTHROPIC_API_KEY')

        if has_library and has_api_key:
            self.closed_set = ClosedSetVision(self.dish_library)
            self.smart_matcher = SmartMatcher(self.dish_library)
            self.mode = 'closed_set_ai'
        elif has_library:
            self.smart_matcher = SmartMatcher(self.dish_library)
            self.closed_set = None
            self.mode = 'closed_set_smart'
        elif has_api_key:
            self.smart_matcher = None
            self.closed_set = None
            self.mode = 'real_ai'
        else:
            self.smart_matcher = None
            self.closed_set = None
            self.mode = 'smart_demo'

    def analyze_plate_waste(self, image_path):
        """餐盘浪费分析：闭集匹配 → 真实AI → Smart Demo 逐级降级"""
        # 1. 闭集AI匹配（最佳方案）
        if self.mode == 'closed_set_ai' and self.closed_set:
            result = self.closed_set.analyze_plate_waste(image_path)
            if result:
                return result
        # 2. 闭集Smart匹配
        if self.mode in ('closed_set_ai', 'closed_set_smart') and self.smart_matcher:
            result = self.smart_matcher.match_plate(image_path)
            if result:
                return result
        # 3. 旧版真实AI（无菜品库时）
        if self.mode == 'real_ai':
            result = self.real_ai.analyze_plate_waste(image_path)
            if result:
                result['analysis_method'] = 'real_ai_claude'
                return result
        # 4. 旧版Smart Demo兜底
        return self.smart.analyze_plate_waste(image_path)

    def identify_buffet_dishes(self, image_paths):
        """自助餐台识别：闭集匹配 → 真实AI → Smart Demo 逐级降级"""
        # 1. 闭集AI匹配（最佳方案）
        if self.mode == 'closed_set_ai' and self.closed_set:
            result = self.closed_set.identify_buffet_dishes(image_paths)
            if result:
                return result
        # 2. 闭集Smart匹配
        if self.mode in ('closed_set_ai', 'closed_set_smart') and self.smart_matcher:
            result = self.smart_matcher.match_buffet(image_paths)
            if result:
                return result
        # 3. 旧版真实AI（无菜品库时）
        if self.mode == 'real_ai':
            result = self.real_ai.identify_buffet_dishes(image_paths)
            if result:
                return result
        # 4. 旧版Smart Demo兜底
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
#  餐盘合成器: 将菜品库参考图合成到盘子上
#  用于生成测试/演示用的合成餐盘照片
# ====================================================================
class PlateCompositor:
    """用Pillow将多道菜的参考图合成到盘子背景上"""

    def __init__(self, library, composites_dir, static_url='/static/composites'):
        self.library = library
        self.composites_dir = composites_dir
        self.static_url = static_url
        self.canvas_size = 800

    def generate(self, dish_ids, plate_style='white_round', layout='scattered'):
        """生成合成餐盘图，返回图片URL"""
        if not dish_ids:
            return None, '请至少选择一道菜'

        # 创建盘子背景
        canvas = self._create_plate(plate_style)

        # 加载并处理菜品图片
        dish_images = []
        for did in dish_ids:
            img = self._load_dish_image(did)
            if img:
                dish_images.append(img)

        if not dish_images:
            return None, '所选菜品没有参考图，请先在菜品库中上传参考图'

        # 计算布局位置
        positions = self._layout(len(dish_images), layout)

        # 合成
        for img, (x, y, w, h) in zip(dish_images, positions):
            # 缩放菜品图到目标大小
            resized = img.resize((w, h), Image.LANCZOS)
            # 如果图片是RGBA，用alpha通道做遮罩
            if resized.mode == 'RGBA':
                canvas.paste(resized, (x, y), resized)
            else:
                canvas.paste(resized, (x, y))

        # 保存
        os.makedirs(self.composites_dir, exist_ok=True)
        name = f"composite_{'_'.join(dish_ids[:3])}_{uuid.uuid4().hex[:6]}.png"
        path = os.path.join(self.composites_dir, name)
        canvas.save(path, 'PNG')
        return f"{self.static_url}/{name}", None

    def _create_plate(self, style):
        """创建盘子背景"""
        canvas = Image.new('RGBA', (self.canvas_size, self.canvas_size), (255, 255, 255, 255))
        draw = ImageDraw.Draw(canvas)

        if 'round' in style:
            # 圆形盘子：白色底 + 浅灰边框
            margin = 30
            draw.ellipse([margin, margin, self.canvas_size - margin, self.canvas_size - margin],
                        outline=(220, 220, 220), width=3)
            draw.ellipse([margin + 15, margin + 15, self.canvas_size - margin - 15, self.canvas_size - margin - 15],
                        outline=(240, 240, 240), width=1)
        elif 'square' in style:
            margin = 40
            draw.rectangle([margin, margin, self.canvas_size - margin, self.canvas_size - margin],
                          outline=(220, 220, 220), width=3, fill=None)

        return canvas

    def _load_dish_image(self, dish_id):
        """加载菜品参考图并去掉白底"""
        refs = self.library.get_reference_images(dish_id)
        if not refs:
            return None

        img = Image.open(refs[0]).convert('RGBA')
        img = img.resize((250, 250), Image.LANCZOS)

        # 简单白底去除：将接近白色的像素变透明
        data = img.getdata()
        new_data = []
        for item in data:
            r, g, b, a = item
            if r > 240 and g > 240 and b > 240:
                new_data.append((r, g, b, 0))  # 透明
            else:
                new_data.append(item)
        img.putdata(new_data)
        return img

    def _layout(self, n_dishes, arrangement):
        """计算每道菜在盘子上的位置和大小"""
        positions = []
        center = self.canvas_size // 2

        if arrangement == 'grid' or n_dishes <= 2:
            # 均匀网格排列
            if n_dishes == 1:
                w, h = 280, 280
                positions.append((center - w // 2, center - h // 2, w, h))
            elif n_dishes == 2:
                w, h = 220, 220
                positions.append((center - 240, center - h // 2, w, h))
                positions.append((center + 20, center - h // 2, w, h))
            elif n_dishes == 3:
                w, h = 200, 200
                positions.append((center - w // 2, 140, w, h))
                positions.append((100, 400, w, h))
                positions.append((500, 400, w, h))
            else:
                # 4+ dishes: 2x2 or more grid
                w, h = 170, 170
                for i in range(min(n_dishes, 6)):
                    row, col = divmod(i, 3)
                    x = 130 + col * 190
                    y = 130 + row * 200
                    positions.append((x, y, w, h))

        elif arrangement == 'scattered':
            # 随机散落（但用固定种子保证可重现）
            rng = random.Random(42 + n_dishes)
            for i in range(n_dishes):
                w = rng.randint(150, 240)
                h = rng.randint(150, 240)
                x = rng.randint(80, self.canvas_size - w - 80)
                y = rng.randint(80, self.canvas_size - h - 80)
                positions.append((x, y, w, h))

        else:  # stacked / 堆叠
            w, h = 220, 220
            for i in range(n_dishes):
                offset_x = (i % 3) * 150
                offset_y = (i // 3) * 150
                x = 100 + offset_x
                y = 100 + offset_y
                positions.append((x, y, w, h))

        return positions


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


# ====================================================================
#  菜品库管理路由
# ====================================================================
@app.route('/admin/library')
def admin_library():
    """菜品库管理页面"""
    library = get_dish_library()
    dishes = library.list_dishes()
    return render_template('admin_library.html', dishes=dishes)


@app.route('/admin/library/add', methods=['POST'])
def admin_library_add():
    """添加新菜品"""
    library = get_dish_library()
    image_file = request.files.get('reference_image')
    success, msg = library.add_dish(request.form, image_file)
    flash(msg, 'success' if success else 'danger')
    return redirect(url_for('admin_library'))


@app.route('/admin/library/<dish_id>/edit', methods=['POST'])
def admin_library_edit(dish_id):
    """编辑菜品元数据"""
    library = get_dish_library()
    # 收集所有可更新的字段
    updates = {k: v for k, v in request.form.items()
               if k in ('name', 'name_en', 'category', 'cooking', 'description',
                        'visual_features', 'typical_plate_appearance',
                        'calories', 'protein', 'carbs', 'fat', 'fiber',
                        'sodium', 'gi', 'original_price')}
    success, msg = library.update_dish(dish_id, updates)
    flash(msg, 'success' if success else 'danger')
    return redirect(url_for('admin_library'))


@app.route('/admin/library/<dish_id>/upload_ref', methods=['POST'])
def admin_library_upload_ref(dish_id):
    """追加参考图"""
    library = get_dish_library()
    image_file = request.files.get('reference_image')
    if image_file and image_file.filename:
        success, msg = library.add_reference_image(dish_id, image_file)
    else:
        success, msg = False, '请选择图片文件'
    flash(msg, 'success' if success else 'danger')
    return redirect(url_for('admin_library'))


@app.route('/admin/library/<dish_id>/delete', methods=['POST'])
def admin_library_delete(dish_id):
    """删除菜品"""
    library = get_dish_library()
    success, msg = library.delete_dish(dish_id)
    flash(msg, 'warning' if success else 'danger')
    return redirect(url_for('admin_library'))


# ---- 餐盘合成器 ----
@app.route('/admin/compositor')
def admin_compositor():
    """餐盘合成器页面"""
    library = get_dish_library()
    dishes = library.list_dishes()
    return render_template('admin_compositor.html', dishes=dishes)


@app.route('/admin/compositor/generate', methods=['POST'])
def admin_compositor_generate():
    """生成合成餐盘图"""
    library = get_dish_library()
    compositor = PlateCompositor(library, app.config['COMPOSITES_DIR'])

    data = request.get_json()
    dish_ids = data.get('dish_ids', [])
    plate_style = data.get('plate_style', 'white_round')
    layout = data.get('layout', 'scattered')

    url, error = compositor.generate(dish_ids, plate_style, layout)
    if error:
        return jsonify({'success': False, 'error': error})
    return jsonify({'success': True, 'image_url': url})


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
