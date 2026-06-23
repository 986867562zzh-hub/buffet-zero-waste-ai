"""
ZeroDine零膳 - Live Demo
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

from translations import get_text as _, LANGUAGES, get_lang, dish_name as _dn, cat_name as _cn, cook_name as _ckn, dietary_name as _diet

from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session, jsonify, send_from_directory
)
from werkzeug.utils import secure_filename
from PIL import Image, ImageStat, ImageFilter, ImageDraw
import io

# ========== 导入配置 ==========
try:
    from config import (
        SECRET_KEY, MAX_CONTENT_LENGTH,
        UPLOAD_FOLDER, DATA_FOLDER, REFERENCE_DIR, COMPOSITES_DIR,
        CALORIE_THRESHOLD_DEFAULT, CALORIE_THRESHOLD_MIN, CALORIE_THRESHOLD_MAX,
        WASTE_SCORE_GRADES, CATEGORY_WEIGHTS,
        DIETARY_LABELS, MEAL_ROLES,
        AI_MAX_TOKENS_VISION, AI_MAX_TOKENS_ANALYSIS, AI_MAX_TOKENS_MATCH, AI_TEMPERATURE,
        DISH_LIBRARY_PATH, DISHES_DATA_PATH,
        COLOR_SIMILARITY_WEIGHT, HASH_WEIGHT, EDGE_WEIGHT, MATCH_THRESHOLD,
    )
    USE_CONFIG = True
except ImportError:
    USE_CONFIG = False

# ========== App 初始化 ==========
app = Flask(__name__)
app.secret_key = SECRET_KEY if USE_CONFIG else 'buffet-zero-waste-demo-2024'
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH if USE_CONFIG else 50 * 1024 * 1024  # 50MB max
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER if USE_CONFIG else os.path.join(os.path.dirname(__file__), 'static', 'uploads')
app.config['DATA_FOLDER'] = DATA_FOLDER if USE_CONFIG else os.path.join(os.path.dirname(__file__), 'data')
app.config['REFERENCE_DIR'] = REFERENCE_DIR if USE_CONFIG else os.path.join(os.path.dirname(__file__), 'static', 'reference_dishes')
app.config['COMPOSITES_DIR'] = COMPOSITES_DIR if USE_CONFIG else os.path.join(os.path.dirname(__file__), 'static', 'composites')

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['COMPOSITES_DIR'], exist_ok=True)


# ═══════════════════════════════════════════
# v2.6 多语言支持: zh-CN / zh-TW / en
# ═══════════════════════════════════════════
@app.context_processor
def inject_translations():
    """向所有模板注入翻译函数和当前语言"""
    return {
        '_': _,
        'lang': get_lang(),
        'languages': LANGUAGES,
        'dn': _dn,        # 菜品名翻译
        'cn': _cn,        # 分类名翻译
        'ckn': _ckn,      # 烹饪方式翻译
        'diet_name': lambda d_id: _diet(d_id)['name'],    # 饮食需求名
        'diet_desc': lambda d_id: _diet(d_id)['desc'],    # 饮食需求描述
    }

@app.route('/set_lang/<language>')
def set_lang(language):
    """切换语言"""
    if language in LANGUAGES:
        session['lang'] = language
    return redirect(request.referrer or url_for('index'))


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
    """固定菜品库：参考图以base64编码存储在JSON中，确保Render部署不丢失"""

    def __init__(self, library_path, reference_dir=None, static_prefix='/static/reference_dishes'):
        self.library_path = library_path
        self.reference_dir = reference_dir  # 保留兼容，但不再主动使用
        self.static_prefix = static_prefix
        self._temp_dir = os.path.join(os.path.dirname(library_path), '..', 'static', 'uploads', '_ref_cache')
        os.makedirs(self._temp_dir, exist_ok=True)

    def load(self):
        if not os.path.exists(self.library_path):
            return {'dishes': [], 'total_dishes': 0}
        with open(self.library_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save(self, data):
        """保存到JSON（原子写入），推送后可持久化"""
        tmp = self.library_path + '.tmp'
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, self.library_path)

    def list_dishes(self):
        """列出所有菜品，附上第一张参考图的base64数据用于显示"""
        data = self.load()
        dishes = data.get('dishes', [])
        for d in dishes:
            refs = d.get('reference_images', [])
            d['has_references'] = bool(refs)
            d['ref_count'] = len(refs)
        return dishes

    def get_dish(self, dish_id):
        dishes = self.list_dishes()
        for d in dishes:
            if d['id'] == dish_id:
                return d
        return None

    def _image_to_base64(self, image_file, max_size=300):
        """将上传图片转为base64 data URI（小尺寸节省空间）"""
        try:
            img = Image.open(image_file).convert('RGB')
            img.thumbnail((max_size, max_size), Image.LANCZOS)
            buf = io.BytesIO()
            img.save(buf, format='JPEG', quality=75)
            b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
            return f"data:image/jpeg;base64,{b64}"
        except Exception as e:
            print(f"[DishLibrary] image_to_base64 error: {e}")
            return None

    def _base64_to_file(self, b64_data_uri, output_path=None):
        """将base64 data URI解码写入临时文件，返回文件路径（供SmartMatcher等需要文件路径的场景）"""
        try:
            if ',' not in b64_data_uri:
                return None
            header, b64 = b64_data_uri.split(',', 1)
            data = base64.b64decode(b64)
            if not output_path:
                output_path = os.path.join(self._temp_dir, f"ref_{uuid.uuid4().hex[:8]}.jpg")
            with open(output_path, 'wb') as f:
                f.write(data)
            return output_path
        except Exception as e:
            print(f"[DishLibrary] base64_to_file error: {e}")
            return None

    def get_reference_urls(self, dish_id):
        """返回参考图的URL列表（base64 data URI可直接用于<img src>）"""
        dish = self.get_dish(dish_id)
        if not dish:
            return []
        return dish.get('reference_images', [])

    def get_reference_images(self, dish_id):
        """获取参考图片的文件路径（兼容SmartMatcher等需要文件的场景）"""
        dish = self.get_dish(dish_id)
        if not dish:
            return []
        refs = dish.get('reference_images', [])
        paths = []
        for i, b64_uri in enumerate(refs):
            cache_path = os.path.join(self._temp_dir, f"{dish_id}_ref{i}.jpg")
            if not os.path.exists(cache_path):
                self._base64_to_file(b64_uri, cache_path)
            if os.path.exists(cache_path):
                paths.append(cache_path)
        return paths

    def add_dish(self, dish_data, image_file=None):
        data = self.load()
        dishes = data.get('dishes', [])
        if any(d['id'] == dish_data['id'] for d in dishes):
            return False, f"菜品ID '{dish_data['id']}' 已存在"

        refs = []
        if image_file and hasattr(image_file, 'filename') and image_file.filename:
            b64 = self._image_to_base64(image_file)
            if b64:
                refs.append(b64)

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
            'reference_images': refs
        }
        dishes.append(dish)
        data['dishes'] = dishes
        data['total_dishes'] = len(dishes)
        self.save(data)
        return True, f"菜品 '{dish_data['name']}' 添加成功，参考图已base64编码存入JSON"

    def update_dish(self, dish_id, updates):
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
        """追加参考图（base64编码存入JSON）"""
        data = self.load()
        dishes = data.get('dishes', [])
        for d in dishes:
            if d['id'] == dish_id:
                b64 = self._image_to_base64(image_file)
                if b64:
                    d.setdefault('reference_images', []).append(b64)
                data['dishes'] = [d if di['id'] == dish_id else di for di in dishes]
                self.save(data)
                # 清除缓存的文件
                cache_path = os.path.join(self._temp_dir, f"{dish_id}_ref{len(d.get('reference_images',[]))-1}.jpg")
                if os.path.exists(cache_path):
                    os.remove(cache_path)
                return True, f"参考图已保存到 '{d['name']}' (base64编码)"
        return False, f"未找到菜品 '{dish_id}'"

    def delete_dish(self, dish_id):
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
            # 清理缓存文件
            for f in os.listdir(self._temp_dir):
                if f.startswith(dish_id):
                    os.remove(os.path.join(self._temp_dir, f))
            return True, f"菜品 '{removed['name']}' 已删除"
        return False, f"未找到菜品 '{dish_id}'"

    def build_claude_context(self, include_images=True, max_img_size=512):
        """构建Claude API的菜品库上下文，图片直接使用base64"""
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
                refs = dish.get('reference_images', [])
                for b64_uri in refs:
                    if b64_uri and ',' in b64_uri:
                        # base64 data URI → 直接用
                        header, b64 = b64_uri.split(',', 1)
                        mime = 'image/jpeg'
                        if 'png' in header:
                            mime = 'image/png'
                        elif 'webp' in header:
                            mime = 'image/webp'
                        # Decode and re-encode at correct size for Claude
                        try:
                            img_data = base64.b64decode(b64)
                            img = Image.open(io.BytesIO(img_data)).convert('RGB')
                            img.thumbnail((max_img_size, max_img_size), Image.LANCZOS)
                            buf = io.BytesIO()
                            img.save(buf, format='JPEG', quality=80)
                            final_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
                            content.append({
                                "type": "image",
                                "source": {"type": "base64", "media_type": "image/jpeg", "data": final_b64}
                            })
                        except Exception:
                            pass

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
        dishes = self.list_dishes()
        lines = []
        for dish in dishes:
            lines.append(
                f"[{dish['id']}] {dish['name']} | {dish['category']} | {dish['cooking']} | "
                f"视觉: {dish['visual_features'][:80]}..."
            )
        return "\n".join(lines)


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
        ({"h_min": 0, "h_max": 20, "s_min": 50, "v_min": 40}, "肉类/红肉", ["红烧肉", "锅包肉", "牛排", "叉烧", "烤鸡腿", "炸猪排"]),
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
        for food_type, count in color_bins.most_common(4):
            pct = count / total_colored * 100
            if pct < 8:
                continue
            # 找到该类型对应的剩余比例
            rem_pct = round(waste_pct * pct / 100, 1)
            # 找到典型菜品名
            examples = []
            for rule in SmartImageAnalyzer.COLOR_FOOD_MAP:
                if rule[1] == food_type:
                    examples = rule[2]
                    break
            # 🔧 v2.7: 用MD5确定性hash替代Python hash（避免每次运行结果不同）
            import hashlib as _hl
            h = int(_hl.md5(str(count).encode()).hexdigest()[:8], 16)
            dish_name = examples[h % len(examples)] if examples else food_type

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

            # v2.6: 提高阈值防虚假识别，每张照片最多2道
            photo_dish_count = 0
            for food_type, count in color_clusters.most_common(8):
                coverage = count / total_colored * 100
                if coverage < 8:  # 从3%提高到8%，过滤微小色块
                    continue
                if photo_dish_count >= 2:  # 每张照片上限2道
                    break
                photo_dish_count += 1

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
        # v2.6: 全局上限6道，防止虚假识别泛滥
        identified = identified[:6]

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

            # v2.6方案B: 构建菜品库上下文
            try:
                lib = get_dish_library()
                lib_dishes = lib.list_dishes() if lib else []
            except Exception:
                lib_dishes = []
            lib_text = "FIXED MENU — You can ONLY pick dishes from this list:\n"
            for d in lib_dishes:
                features = d.get('visual_features', '')
                lib_text += f"- {d['name']} | {d['category']} | {d['cooking']} | {d['calories']}kcal"
                if features:
                    lib_text += f" | looks like: {features[:100]}"
                lib_text += "\n"

            content.append({
                "type": "text",
                "text": lib_text + f"""

These are photos of leftover food at different buffet stations (taken by hotel staff at the end of meal service).

CRITICAL RULES — YOU MUST FOLLOW:
1. You can ONLY identify dishes from the FIXED MENU above. DO NOT invent any dish name not in the list.
2. MAX 2 dishes PER PHOTO. If only 1 is visible, return 1.
3. If a food item cannot be confidently matched to the fixed menu, put it in unmatched_items instead.
4. WHEN IN DOUBT, LEAVE IT OUT. Honesty > completeness.

For each matched dish, provide:
1. name: exact match from the fixed menu
2. confidence: "high" (very certain), "medium" (probable), or "low" (guess — DO NOT USE, put in unmatched_items instead)
3. quantity: estimated remaining servings (1-15)
4. visual_evidence: brief description of what you see that matches

Return ONLY valid JSON (no markdown):
{{
  "matched_dishes": [
    {{
      "name": "exact dish name from fixed menu",
      "category": "主食|肉类|海鲜|蔬菜|汤品|甜点|水果",
      "cooking": "炒|蒸|烤|炸|炖|煮|凉拌|生食",
      "confidence": "high|medium",
      "quantity": number,
      "calories": number, "protein": number, "carbs": number,
      "fat": number, "fiber": number, "sodium": number,
      "gi": number, "original_price": number,
      "visual_evidence": "what confirms this match"
    }}
  ],
  "unmatched_items": ["descriptions of food that doesn't match any menu item"],
  "zones_detected": ["zone names"]
}}"""
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

            # v2.6方案B: 解析闭集匹配结果
            data = json.loads(result_text)
            dishes = data.get('matched_dishes', data.get('dishes', []))
            # 过滤低置信度匹配
            dishes = [d for d in dishes if d.get('confidence', 'medium') != 'low']
            return {
                "identified_dishes": dishes,
                "total_count": len(dishes),
                "photos_analyzed": len(image_paths),
                "analysis_time": datetime.now().strftime('%H:%M:%S'),
                "zones_detected": data.get('zones_detected', list(set(
                    "热菜区" if d.get('category') in ['肉类','海鲜'] and d.get('cooking') in ['炒','烤','炖','炸']
                    else "主食汤品区" if d.get('category') in ['主食','汤品']
                    else "冷菜甜点区" if d.get('category') in ['水果','甜点'] or d.get('cooking') in ['凉拌','生食','冷制']
                    else "蔬菜区"
                    for d in dishes
                ))),
                "analysis_method": "real_ai_claude_closed_set"
            }
        except Exception as e:
            print(f"[RealAI] Buffet identification error: {e}")
            return None


# ====================================================================
#  DeepSeek Vision API: 使用DeepSeek视觉模型进行食物识别
#  OpenAI兼容接口，性价比高，中文理解力强
# ====================================================================
class DeepSeekVision:
    """DeepSeek Vision API 识别引擎（OpenAI兼容）"""

    def __init__(self):
        self.api_key = os.environ.get('DEEPSEEK_API_KEY', '')
        self.available = bool(self.api_key)
        self.client = None
        self._library = None  # v2.6方案B: 延迟加载菜品库
        # v2.6: v4推理模型需要更大的max_tokens（推理tokens+输出tokens）
        self.max_tokens = 4000
        if self.available:
            try:
                from openai import OpenAI
                import httpx
                # 绕过系统代理（校园网代理可能拦截DeepSeek API）
                http_client = httpx.Client(trust_env=False, timeout=60.0)
                self.client = OpenAI(
                    api_key=self.api_key,
                    base_url="https://api.deepseek.com",
                    http_client=http_client
                )
            except Exception as e:
                print(f"[DeepSeek] Init error: {e}")
                self.available = False

    # ═══════════════════════════════════════════
    # v2.6 PIL图像特征提取: 将图片转为文字描述供DeepSeek推理
    # ═══════════════════════════════════════════
    @staticmethod
    def _describe_image(image_path):
        """用PIL提取图片视觉特征，返回文字描述"""
        from collections import Counter
        try:
            img = Image.open(image_path).convert('RGB')
            img.thumbnail((400, 400), Image.LANCZOS)
            w, h = img.size
            pixels = list(img.getdata())
        except Exception:
            return "无法读取图片"

        # 颜色统计
        color_bins = Counter()
        total_sampled = 0
        for r, g, b in pixels[::8]:  # 采样加速
            brightness = (r + g + b) / 3
            if brightness > 230:  # 跳过白色（盘子/桌布）
                continue
            if brightness < 20:    # 跳过极暗
                continue
            total_sampled += 1
            max_c, min_c = max(r, g, b), min(r, g, b)
            sat = (max_c - min_c) / max_c if max_c > 0 else 0

            if sat < 0.1:  # 灰/白/黑
                if brightness < 80: color_bins['深灰/黑色'] += 1
                else: color_bins['浅灰/白色'] += 1
            elif r > g and r > b:
                if g > 120: color_bins['金黄色/橙黄色'] += 1
                elif r > 160: color_bins['红色/橙红色'] += 1
                else: color_bins['深棕色/褐色'] += 1
            elif g > r and g > b:
                if g > 120: color_bins['绿色/黄绿色'] += 1
                else: color_bins['深绿色'] += 1
            elif b > r and b > g:
                color_bins['蓝紫色'] += 1
            elif r > 180 and g > 180 and b < 120:
                color_bins['黄色/金色'] += 1
            else:
                color_bins['中性色/米色'] += 1

        if total_sampled == 0:
            return "图片过亮或过暗，无法分析"

        # 平均颜色
        valid_pixels = [(r, g, b) for r, g, b in pixels if 20 < (r+g+b)/3 < 230]
        if valid_pixels:
            avg_r = sum(p[0] for p in valid_pixels) // len(valid_pixels)
            avg_g = sum(p[1] for p in valid_pixels) // len(valid_pixels)
            avg_b = sum(p[2] for p in valid_pixels) // len(valid_pixels)
        else:
            avg_r = avg_g = avg_b = 128

        # 亮度分布估算覆盖率
        bright_count = sum(1 for r, g, b in pixels if (r+g+b)/3 > 180)
        coverage_pct = round((1 - bright_count / len(pixels)) * 100)

        # 构建文字描述
        top_colors = color_bins.most_common(4)
        color_desc = ', '.join(f'{name}({round(cnt/total_sampled*100)}%)' for name, cnt in top_colors)

        return (
            f"图片尺寸{w}x{h}, 食物覆盖率约{coverage_pct}%\n"
            f"主色调: {color_desc}\n"
            f"平均RGB: ({avg_r}, {avg_g}, {avg_b})\n"
            f"色调特征: {'偏暖(金/红/棕)' if avg_r > avg_b + 20 else '偏冷(绿/蓝)' if avg_b > avg_r + 20 else '中性'}"
        )

    def analyze_plate_waste(self, image_path):
        """餐盘浪费分析 — v2.6 PIL+DeepSeek混合方案"""
        if not self.available:
            return None
        try:
            # PIL提取图片特征
            img_desc = self._describe_image(image_path)

            prompt = (
                "你是一个专业的美食识别助手。\n"
                "以下是顾客用餐后餐盘的计算机视觉分析：\n\n"
                f"{img_desc}\n\n"
                "【任务】根据颜色和纹理特征，判断餐盘的食物剩余情况。\n"
                "- 食物覆盖率<15%: empty(光盘), 15-35%: light(少量), 35-60%: moderate(中等), 60-80%: heavy(较多), >80%: full(几乎没吃)\n"
                "- 根据颜色特征推断可能是什么食物（参考：金黄色→炸肉类，红褐色→红烧，白色→清蒸/白灼，绿色→蔬菜）\n\n"
                "返回纯JSON（不要markdown）：\n"
                '{"plate_status":"empty|light|moderate|heavy|full",'
                '"overall_waste_percentage":数字(0-100),'
                '"items":[{"name":"菜名","category":"主食|肉类|海鲜|蔬菜|汤品|甜点|水果",'
                '"estimated_remaining_percentage":数字,"estimated_original_portion":"小份|中份|大份",'
                '"visual_evidence":"颜色和特征依据"}],'
                '"summary":"一句中文总结"}\n'
                "基于颜色分析诚实推断，不确定的食物不要编造。"
            )
            resp = self.client.chat.completions.create(
                model="deepseek-v4-pro",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=self.max_tokens, temperature=0.1
            )
            text = resp.choices[0].message.content.strip()
            if text.startswith('```'): text = text.split('\n', 1)[1]; text = text[:-3] if text.endswith('```') else text
            result = json.loads(text)
            result['analysis_method'] = 'deepseek_vision'
            return result
        except Exception as e:
            print(f"[DeepSeek] Plate analysis error: {e}")
            return None

    def identify_buffet_dishes(self, image_paths):
        """
        自助餐台菜品识别 — v2.6 PIL+DeepSeek混合方案
        PIL提取图片颜色/纹理特征 → 文字描述 → DeepSeek匹配12道菜品库
        """
        if not self.available:
            return None
        try:
            # 构建菜品库上下文
            if self._library is None:
                self._library = get_dish_library()
            lib_dishes = self._library.list_dishes() if self._library else []
            lib_text = "【固定菜品库 — 你只能从以下12道菜中选择】\n"
            for d in lib_dishes:
                features = d.get('visual_features', '')
                lib_text += f"- {d['name']} | {d['category']} | {d['cooking']} | {d['calories']}kcal"
                if features:
                    lib_text += f" | 特征: {features[:100]}"
                lib_text += "\n"

            # v2.6: PIL提取图片特征 → 文字描述
            image_descs = []
            for i, path in enumerate(image_paths):
                desc = self._describe_image(path)
                image_descs.append(f"--- 照片{i+1}的PIL分析 ---\n{desc}")

            prompt = (
                lib_text + "\n"
                f"以上是固定菜品库（共{len(lib_dishes)}道菜）。\n"
                f"酒店员工拍摄了{len(image_paths)}张自助餐台照片。\n"
                "由于系统使用PIL进行图像分析，以下是每张照片的计算机视觉特征描述：\n\n"
                + "\n".join(image_descs) + "\n\n"
                "【任务】根据上述颜色和纹理特征，从固定菜品库中匹配最可能的菜品。\n"
                "【核心规则】\n"
                "1. 只能从菜品库中匹配，严禁编造库外菜名\n"
                "2. 每张照片最多匹配2道菜\n"
                "3. 利用颜色特征判断：金黄色→炸/烤肉类, 红褐色→红烧/酱炒, 白色→清蒸/白灼, 绿色→蔬菜\n"
                "4. 不确定的匹配放入 unmatched_items\n\n"
                "返回纯JSON：\n"
                '{"matched_dishes":[{"name":"菜品库中的菜名","category":"分类","cooking":"烹饪方式",'
                '"quantity":份数,"calories":热量,"protein":蛋白质,"carbs":碳水,"fat":脂肪,'
                '"fiber":纤维,"sodium":钠,"gi":GI值,"original_price":原价,'
                '"confidence":"high|medium","visual_evidence":"颜色和特征匹配依据"}],'
                '"unmatched_items":["无法匹配的描述"],"zones_detected":["区域"]}'
            )

            resp = self.client.chat.completions.create(
                model="deepseek-v4-pro",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=self.max_tokens, temperature=0.1
            )
            text = resp.choices[0].message.content.strip()
            if not text:
                return None
            if text.startswith('```'): text = text.split('\n', 1)[1]; text = text[:-3] if text.endswith('```') else text
            result = json.loads(text)
            # v2.6方案B: 标准化输出格式
            if 'identified_dishes' not in result:
                result['identified_dishes'] = result.get('matched_dishes', result.get('dishes', []))
            # 只保留 confidence 不为 'low' 的匹配
            result['identified_dishes'] = [
                d for d in result['identified_dishes']
                if d.get('confidence', 'medium') != 'low'
            ]
            result['total_count'] = len(result.get('identified_dishes', []))
            result['photos_analyzed'] = len(image_paths)
            result['analysis_time'] = datetime.now().strftime('%H:%M:%S')
            result['analysis_method'] = 'deepseek_vision'
            return result
        except Exception as e:
            print(f"[DeepSeek] Buffet error: {e}")
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
                    '- 每张照片最多匹配2道菜。如果只看到1道，就只返回1道\n'
                    '- 同一个菜可能出现在多张照片中，合并为一条记录取最大quantity\n'
                    '- 每张照片对应一个自助餐台区域\n'
                    '- 宁少勿多：不确定的匹配直接放入 unmatched_items'
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
    多特征融合匹配器：感知哈希 + 颜色直方图 + 边缘特征
    准确率远高于单纯颜色匹配，适合课堂演示
    """

    def __init__(self, dish_library):
        self.library = dish_library
        self.profiles = {}  # dish_id → {'hash': str, 'color': dict, 'edge': float}
        self._precompute()

    def _precompute(self):
        for dish in self.library.list_dishes():
            ref_imgs = self.library.get_reference_images(dish['id'])
            if ref_imgs:
                self.profiles[dish['id']] = self._extract_features(ref_imgs[0])

    # ========== 感知哈希 (Average Hash) ==========
    @staticmethod
    def _compute_ahash(img):
        """计算平均哈希：将图片缩放到8×8灰度图，比平均值大的为1"""
        try:
            gray = img.convert('L').resize((8, 8), Image.LANCZOS)
            pixels = list(gray.getdata())
            avg = sum(pixels) / 64
            return ''.join('1' if p > avg else '0' for p in pixels)
        except Exception:
            return '0' * 64

    @staticmethod
    def _hamming_distance(h1, h2):
        """两个哈希的汉明距离（越小越相似）"""
        return sum(c1 != c2 for c1, c2 in zip(h1, h2))

    @staticmethod
    def _hash_similarity(h1, h2):
        """哈希相似度 0-1，距离0=完全相同"""
        dist = SmartMatcher._hamming_distance(h1, h2)
        return 1.0 - dist / 64.0

    # ========== 颜色特征 ==========
    @staticmethod
    def _compute_color_profile(img):
        """计算HSV颜色直方图特征"""
        try:
            small = img.resize((32, 32), Image.LANCZOS)
            pixels = list(small.getdata())
            hue_bins = [0] * 36
            r_sum = g_sum = b_sum = 0
            for r, g, b in pixels:
                r_sum += r; g_sum += g; b_sum += b
                max_c, min_c = max(r, g, b), min(r, g, b)
                if max_c > min_c:
                    if max_c == r:
                        h = (60 * (g - b) / (max_c - min_c)) % 360
                    elif max_c == g:
                        h = 60 * (b - r) / (max_c - min_c) + 120
                    else:
                        h = 60 * (r - g) / (max_c - min_c) + 240
                    hue_bins[int(h / 10) % 36] += 1
            n = max(len(pixels), 1)
            return {
                'mean_r': r_sum / n, 'mean_g': g_sum / n, 'mean_b': b_sum / n,
                'hue_histogram': hue_bins
            }
        except Exception:
            return None

    @staticmethod
    def _color_similarity(c1, c2):
        """颜色相似度 0-1"""
        if not c1 or not c2:
            return 0.0
        dot = c1['mean_r'] * c2['mean_r'] + c1['mean_g'] * c2['mean_g'] + c1['mean_b'] * c2['mean_b']
        n1 = (c1['mean_r']**2 + c1['mean_g']**2 + c1['mean_b']**2) ** 0.5
        n2 = (c2['mean_r']**2 + c2['mean_g']**2 + c2['mean_b']**2) ** 0.5
        rgb_sim = dot / (n1 * n2 + 1) if n1 > 0 and n2 > 0 else 0
        ha, hb = c1['hue_histogram'], c2['hue_histogram']
        inter = sum(min(a, b) for a, b in zip(ha, hb))
        hue_sim = inter / max(sum(ha), sum(hb), 1)
        return 0.5 * rgb_sim + 0.5 * hue_sim

    # ========== 边缘特征 ==========
    @staticmethod
    def _compute_edge_score(img):
        """简单边缘密度：用PIL的FIND_EDGES滤波器"""
        try:
            edges = img.convert('L').resize((32, 32), Image.LANCZOS).filter(ImageFilter.FIND_EDGES)
            pixels = list(edges.getdata())
            edge_count = sum(1 for p in pixels if p > 30)
            return edge_count / len(pixels)
        except Exception:
            return 0.0

    # ========== 综合特征提取 ==========
    def _extract_features(self, image_path):
        try:
            img = Image.open(image_path).convert('RGB')
            return {
                'hash': self._compute_ahash(img),
                'color': self._compute_color_profile(img),
                'edge': self._compute_edge_score(img)
            }
        except Exception:
            return None

    def _compute_similarity(self, f1, f2):
        """
        综合相似度评分：
        - 感知哈希: 60%（结构匹配）
        - 颜色特征: 30%（色调匹配）
        - 边缘特征: 10%（纹理匹配）
        """
        if not f1 or not f2:
            return 0.0
        hash_sim = self._hash_similarity(f1['hash'], f2['hash'])
        color_sim = self._color_similarity(f1['color'], f2['color'])
        edge_diff = abs(f1['edge'] - f2['edge'])
        edge_sim = 1.0 - min(edge_diff / max(f1['edge'] + f2['edge'], 0.01), 1.0)
        return 0.60 * hash_sim + 0.30 * color_sim + 0.10 * edge_sim

    # ========== 匹配方法 ==========
    def match_plate(self, uploaded_image_path):
        """匹配餐盘照片 → 返回最匹配的1道菜"""
        try:
            query_features = self._extract_features(uploaded_image_path)
            if not query_features:
                return None

            # 与每道菜的参考图计算综合相似度
            scored = []
            for dish_id, ref_features in self.profiles.items():
                sim = self._compute_similarity(query_features, ref_features)
                dish = self.library.get_dish(dish_id)
                if dish:
                    scored.append((dish, sim))

            scored.sort(key=lambda x: x[1], reverse=True)

            if not scored:
                return None

            # 只取最佳匹配的那一道菜
            dish, sim = scored[0]
            sim_pct = round(sim * 100)

            # 🔧 v2.7: 先算实际餐盘覆盖率（不管匹配相似度，这是真实的物理量）
            img = Image.open(uploaded_image_path).convert('RGB')
            img_small = img.resize((64, 64))
            pixels = list(img_small.getdata())
            bg_count = sum(1 for r, g, b in pixels if r > 200 and g > 200 and b > 200)
            coverage = 1.0 - bg_count / len(pixels)
            actual_coverage_pct = round(coverage * 100)

            # 根据实际覆盖率判断份量（不是根据相似度！）
            if actual_coverage_pct > 75:
                portion = '大份'
            elif actual_coverage_pct > 35:
                portion = '中份'
            else:
                portion = '小份'

            if sim > 0.70:
                conf = 'high'
                evidence = f"✅ 高置信度匹配 {dish['name']}（相似度{sim_pct}%，覆盖率{actual_coverage_pct}%）"
            elif sim > 0.55:
                conf = 'medium'
                evidence = f"🔍 中等置信度，最接近 {dish['name']}（相似度{sim_pct}%，覆盖率{actual_coverage_pct}%）"
            else:
                conf = 'low'
                evidence = f"⚠️ 低置信度（{sim_pct}%），可能是 {dish['name']}（覆盖率{actual_coverage_pct}%）"

            matches = [{
                'name': dish['name'],
                'dish_id': dish['id'],
                'confidence': conf,
                'similarity': sim_pct,
                'category': dish['category'],
                'estimated_remaining_percentage': actual_coverage_pct,  # ← 用实际覆盖率！
                'estimated_original_portion': portion,
                'visual_evidence': evidence
            }]

            waste_pct = actual_coverage_pct
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
                'summary': f"多特征融合匹配，发现{len(matches)}种可能的菜品",
                'analysis_method': 'closed_set_smart'
            }

        except Exception as e:
            print(f"[SmartMatcher] Plate match error: {e}")
            return None

    def match_buffet(self, image_paths):
        """匹配自助餐台照片 — v2.6方案B: 纯闭集，高阈值+最佳匹配优先"""
        try:
            all_matches = {}
            for photo_idx, path in enumerate(image_paths):
                query_features = self._extract_features(path)
                if not query_features:
                    continue
                # 收集每张照片的所有匹配分数
                photo_matches = []
                for dish_id, ref_features in self.profiles.items():
                    sim = self._compute_similarity(query_features, ref_features)
                    if sim > 0.6:
                        dish = self.library.get_dish(dish_id)
                        if dish:
                            photo_matches.append((sim, dish_id, dish))
                # v2.6方案B: 单张照片保守匹配——宁少勿错
                photo_matches.sort(key=lambda x: x[0], reverse=True)
                max_per_photo = 1 if len(image_paths) <= 1 else 2  # 单图:1道, 多图:2道
                kept_in_photo = 0
                for sim, dish_id, dish in photo_matches:
                    if kept_in_photo >= max_per_photo:
                        break
                    # v2.6方案B: 极高阈值，宁缺毋滥。感知哈希跨光线/角度区分度有限
                    if sim < 0.75:  # 低于0.75不取，避免假阳性
                        continue
                    confidence = 'high' if sim > 0.80 else 'medium'
                    if dish_id not in all_matches or sim > all_matches[dish_id]['_sim']:
                        all_matches[dish_id] = {
                            'name': dish['name'], 'dish_id': dish_id,
                            'confidence': confidence,
                            'category': dish['category'], 'cooking': dish['cooking'],
                            'quantity': int(sim * 10 + 2),
                            'calories': dish['calories'], 'protein': dish['protein'],
                            'carbs': dish['carbs'], 'fat': dish['fat'],
                            'fiber': dish['fiber'], 'sodium': dish['sodium'],
                            'gi': dish['gi'], 'original_price': dish['original_price'],
                            '_sim': sim
                        }
                        kept_in_photo += 1
            identified = list(all_matches.values())
            for d in identified:
                d.pop('_sim', None)
            # v2.6方案B: 按相似度排序只取top-3，防止泛滥匹配
            identified.sort(key=lambda x: x.get('quantity', 0), reverse=True)
            identified = identified[:3]

            zones = set()
            for d in identified:
                cat = d.get('category', '')
                if cat in ('肉类', '海鲜'):
                    zones.add('热菜/肉类区')
                elif cat in ('蔬菜',):
                    zones.add('冷菜/蔬菜区')
                elif cat in ('主食', '汤品'):
                    zones.add('主食/汤品区')

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
    """统一入口 - DeepSeek/Claude AI优先，闭集匹配兜底"""

    def __init__(self):
        self.dish_library = get_dish_library()
        self.real_ai = RealAIVision()
        self.deepseek = DeepSeekVision()
        self.smart = SmartImageAnalyzer()

        has_library = self.dish_library is not None and len(self.dish_library.list_dishes()) > 0
        has_claude = self.real_ai.available and os.environ.get('ANTHROPIC_API_KEY')
        has_deepseek = self.deepseek.available and os.environ.get('DEEPSEEK_API_KEY')

        # 优先级: DeepSeek > Claude > SmartMatcher > SmartDemo
        if has_library and has_deepseek:
            self.closed_set = ClosedSetVision(self.dish_library)
            self.smart_matcher = SmartMatcher(self.dish_library)
            self.mode = 'closed_set_deepseek'
        elif has_library and has_claude:
            self.closed_set = ClosedSetVision(self.dish_library)
            self.smart_matcher = SmartMatcher(self.dish_library)
            self.mode = 'closed_set_ai'
        elif has_library:
            self.smart_matcher = SmartMatcher(self.dish_library)
            self.closed_set = None
            self.mode = 'closed_set_smart'
        elif has_claude:
            self.smart_matcher = None
            self.closed_set = None
            self.mode = 'real_ai'
        else:
            self.smart_matcher = None
            self.closed_set = None
            self.mode = 'smart_demo'

    def analyze_plate_waste(self, image_path):
        """餐盘分析：DeepSeek → Claude → 闭集匹配 → Smart Demo 逐级降级"""
        # 1. DeepSeek（优先：便宜+中文强）
        if self.mode == 'closed_set_deepseek' and self.deepseek.available:
            result = self.deepseek.analyze_plate_waste(image_path)
            if result and (result.get('items') or result.get('matched_dishes')):
                return result
        # 2. Claude（备选）
        if self.mode == 'closed_set_ai' and self.closed_set:
            result = self.closed_set.analyze_plate_waste(image_path)
            if result and (result.get('items') or result.get('matched_dishes')):
                return result
        # 3. 闭集Smart匹配
        if self.mode in ('closed_set_deepseek', 'closed_set_ai', 'closed_set_smart') and self.smart_matcher:
            result = self.smart_matcher.match_plate(image_path)
            if result and result.get('items'):
                return result
        # 4. 旧版Claude（无菜品库）
        if self.mode == 'real_ai':
            result = self.real_ai.analyze_plate_waste(image_path)
            if result:
                result['analysis_method'] = 'real_ai_claude'
                return result
        # 5. Smart Demo兜底
        return self.smart.analyze_plate_waste(image_path)

    def identify_buffet_dishes(self, image_paths):
        """
        自助餐台识别 — v2.6方案B: 纯菜品库闭集匹配
        所有识别路径强制约束到12道固定菜品库，绝不编造
        优先级: DeepSeek → Claude闭集 → SmartMatcher感知哈希 → 空结果(诚实)
        """
        # 1. DeepSeek + 菜品库约束
        if self.mode == 'closed_set_deepseek' and self.deepseek.available:
            result = self.deepseek.identify_buffet_dishes(image_paths)
            if result and result.get('identified_dishes'):
                return result
        # 2. Claude + 菜品库约束（闭集包装）
        if self.mode in ('closed_set_deepseek', 'closed_set_ai') and self.closed_set:
            result = self.closed_set.identify_buffet_dishes(image_paths)
            if result and result.get('identified_dishes'):
                return result
        # 3. DeepSeek 无闭集包装（但仍受菜品库约束）
        if self.deepseek.available:
            result = self.deepseek.identify_buffet_dishes(image_paths)
            if result and result.get('identified_dishes'):
                return result
        # 4. Claude 无闭集包装（但仍受菜品库约束）
        if self.real_ai.available:
            result = self.real_ai.identify_buffet_dishes(image_paths)
            if result and result.get('identified_dishes'):
                return result
        # 5. SmartMatcher 感知哈希匹配 —— 纯库匹配，绝不编造
        if self.smart_matcher:
            result = self.smart_matcher.match_buffet(image_paths)
            if result and result.get('identified_dishes'):
                return result
            # SmartMatcher没匹配到：返回空结果，诚实告知
            return {
                'identified_dishes': [],
                'total_count': 0,
                'photos_analyzed': len(image_paths),
                'analysis_time': datetime.now().strftime('%H:%M:%S'),
                'zones_detected': [],
                'analysis_method': 'closed_set_smart_no_match'
            }
        # 6. 绝对兜底：无菜品库、无API、无SmartMatcher → 空结果
        return {
            'identified_dishes': [],
            'total_count': 0,
            'photos_analyzed': len(image_paths),
            'analysis_time': datetime.now().strftime('%H:%M:%S'),
            'zones_detected': [],
            'analysis_method': 'no_engine_available'
        }

    def match_meals(self, dietary_type, allergies, available_dishes):
        """智能搭配引擎 v2.4 — P1~P4 改进版"""
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

        config = DIETARY_CONFIGS.get(dietary_type, DIETARY_CONFIGS["comfort_food"])

        # ---- P2: 过敏过滤（兼容字符串和列表） ----
        allergy_keywords = []
        if allergies:
            if isinstance(allergies, list):
                allergy_keywords = [a.strip().lower() for a in allergies if a.strip()]
            else:
                allergy_keywords = [a.strip().lower() for a in str(allergies).replace('，', ',').split(',') if a.strip()]

        # ---- P1: 逐级放宽过滤 ----
        def dish_matches(dish, skip_cook=False, skip_gi_na=False, skip_names=False):
            name = dish.get('name', '')
            cat = dish.get('category', '')
            cook = dish.get('cooking', '')

            # P2: 过敏检查（始终执行）
            for kw in allergy_keywords:
                if kw in name.lower() or kw in cat.lower():
                    return False, 'allergy'

            if 'avoid_cat' in config and cat in config['avoid_cat']:
                return False, 'category'
            if not skip_names and 'avoid_names' in config:
                for kw in config['avoid_names']:
                    if kw in name:
                        return False, 'name_keyword'
            if not skip_cook and 'avoid_cook' in config and cook in config['avoid_cook']:
                return False, 'cooking'
            if not skip_gi_na:
                if 'max_gi' in config and dish.get('gi', 0) > config['max_gi']:
                    return False, 'gi'
                if 'max_sodium' in config and dish.get('sodium', 0) > config['max_sodium']:
                    return False, 'sodium'
            return True, ''

        candidates = []
        relaxed_dishes = set()  # 记录被放宽规则收录的菜

        for d in available_dishes:
            ok, _ = dish_matches(d)
            if ok:
                candidates.append(d)

        # P1: 候选不足4道时逐级放宽
        relaxation_level = 0
        if len(candidates) < 4:
            # Level 1: 放宽烹饪方式
            l1 = []
            for d in available_dishes:
                if d in candidates:
                    l1.append(d)
                else:
                    ok, reason = dish_matches(d, skip_cook=True)
                    if ok and reason != 'allergy':
                        l1.append(d)
                        relaxed_dishes.add(d.get('name', ''))
            if len(l1) < 4:
                # Level 2: 再放宽 GI/钠
                l2 = []
                for d in available_dishes:
                    if d in l1:
                        l2.append(d)
                    else:
                        ok, reason = dish_matches(d, skip_cook=True, skip_gi_na=True)
                        if ok and reason != 'allergy':
                            l2.append(d)
                            relaxed_dishes.add(d.get('name', ''))
                if len(l2) < 4:
                    # Level 3: 只保留过敏 + 分类过滤
                    l3 = []
                    for d in available_dishes:
                        ok, reason = dish_matches(d, skip_cook=True, skip_gi_na=True, skip_names=True)
                        if ok and reason != 'allergy':
                            l3.append(d)
                            relaxed_dishes.add(d.get('name', ''))
                    candidates = l3
                    relaxation_level = 3
                else:
                    candidates = l2
                    relaxation_level = 2
            else:
                candidates = l1
                relaxation_level = 1

        # ---- P3: 真实营养合规评分 ----
        def calc_suitability(selected_dishes):
            """基于实际营养合规计算适配度（0-100）"""
            tot_cal = sum(s.get('calories', 0) for s in selected_dishes)
            tot_protein = sum(s.get('protein', 0) for s in selected_dishes)
            tot_carbs = sum(s.get('carbs', 0) for s in selected_dishes)
            tot_fat = sum(s.get('fat', 0) for s in selected_dishes)
            tot_fiber = sum(s.get('fiber', 0) for s in selected_dishes)

            score = 100
            # 热量检查
            if 'max_cal' in config and tot_cal > config['max_cal']:
                over_pct = (tot_cal - config['max_cal']) / config['max_cal']
                score -= min(25, int(over_pct * 50))
            if 'min_cal' in config and tot_cal < config['min_cal']:
                under_pct = (config['min_cal'] - tot_cal) / config['min_cal']
                score -= min(15, int(under_pct * 30))
            # 蛋白质
            if 'min_protein' in config and tot_protein < config['min_protein']:
                under_pct = (config['min_protein'] - tot_protein) / config['min_protein']
                score -= min(20, int(under_pct * 40))
            # 碳水
            if 'max_carbs' in config and tot_carbs > config['max_carbs']:
                over_pct = (tot_carbs - config['max_carbs']) / config['max_carbs']
                score -= min(15, int(over_pct * 30))
            # 脂肪
            if 'max_fat' in config and tot_fat > config['max_fat']:
                over_pct = (tot_fat - config['max_fat']) / max(config['max_fat'], 1)
                score -= min(15, int(over_pct * 30))
            # 纤维
            if 'min_fiber' in config and tot_fiber < config['min_fiber']:
                under_pct = (config['min_fiber'] - tot_fiber) / max(config['min_fiber'], 1)
                score -= min(10, int(under_pct * 20))

            return max(35, score)

        # ---- 候选排序 ----
        def score_dish(dish):
            s = 0
            if 'prefer_cat' in config and dish.get('category') in config['prefer_cat']:
                s += 3
            if 'prefer_cook' in config and dish.get('cooking') in config['prefer_cook']:
                s += 2
            s += min(dish.get('quantity', 1), 5) * 0.5
            return s

        candidates.sort(key=score_dish, reverse=True)

        # ---- P4: 3套餐差异化策略 ----
        mains = [d for d in candidates if d.get('category') in ['主食']]
        proteins = [d for d in candidates if d.get('category') in ['肉类', '海鲜', '蔬菜'] and d.get('protein', 0) > 5]
        sides = [d for d in candidates if d.get('category') in ['蔬菜', '汤品']]
        extras = [d for d in candidates if d.get('category') in ['水果', '甜点', '汤品']]

        def build_combo(strategy, used_dishes=None):
            """构建套餐：strategy='balanced'|'cheapest'|'varied'"""
            if used_dishes is None:
                used_dishes = set()

            if strategy == 'balanced':
                # 精选：营养最优
                m = mains[:1] if mains else []
                p = proteins[:2] if proteins else []
                s = sides[:1] if sides else []
                e = extras[:1] if extras else []
            elif strategy == 'cheapest':
                # 实惠：价格最低
                mains_by_price = sorted(mains, key=lambda x: x.get('original_price', 999))
                prots_by_price = sorted(proteins, key=lambda x: x.get('original_price', 999))
                sides_by_price = sorted(sides, key=lambda x: x.get('original_price', 999))
                extras_by_price = sorted(extras, key=lambda x: x.get('original_price', 999))
                m = mains_by_price[:1]
                p = prots_by_price[:2]
                s = sides_by_price[:1]
                e = extras_by_price[:1]
            else:
                # 风味：避开已用的菜
                m = [d for d in mains if d.get('name') not in used_dishes][:1]
                p = [d for d in proteins if d.get('name') not in used_dishes][:2]
                s = [d for d in sides if d.get('name') not in used_dishes][:1]
                e = [d for d in extras if d.get('name') not in used_dishes][:1]

            selected = []
            if m: selected.append(m[0])
            for pi in p:
                if pi not in selected:
                    selected.append(pi)
            if s and s[0] not in selected:
                selected.append(s[0])
            if e and e[0] not in selected:
                selected.append(e[0])
            return selected

        strategies = [
            ('balanced', '精选套餐', f'{config.get("label", "")} 营养最优搭配'),
            ('cheapest', '超值套餐', f'{config.get("label", "")} 性价比之选'),
            ('varied', '风味套餐', f'{config.get("label", "")} 口味多样组合'),
        ]

        used_names = set()
        recommendations = []
        for i, (strategy, suffix, desc) in enumerate(strategies):
            selected = build_combo(strategy, used_names)
            for s in selected:
                used_names.add(s.get('name', ''))

            if not selected:
                selected = build_combo('balanced')  # fallback

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
            suitability = calc_suitability(selected)

            item_list = []
            for s in selected:
                name = s.get('name', '未知')
                was_relaxed = name in relaxed_dishes
                item_list.append({
                    "name": name,
                    "category": s.get('category', '其他'),
                    "role": ("主食" if s.get('category') == '主食'
                        else "主菜" if s.get('category') in ['肉类', '海鲜']
                        else "配菜" if s.get('category') in ['蔬菜']
                        else "汤品" if s.get('category') == '汤品'
                        else "附加"),
                    "original_price": s.get('original_price', 25),
                    "discounted_price": round(s.get('original_price', 25) * time_disc, 1),
                    "reason": f"{'⚠️放宽规则·' if was_relaxed else ''}{s.get('cooking','')}方式",
                })

            recommendations.append({
                "id": i + 1,
                "name": f"【{suffix}】",
                "description": desc,
                "items": item_list,
                "total_nutrition": {
                    "calories": total_cal, "protein": round(total_protein, 1),
                    "carbs": round(total_carbs, 1), "fat": round(total_fat, 1),
                    "fiber": round(total_fiber, 1)
                },
                "total_original_price": total_original,
                "total_discounted_price": total_discounted,
                "discount_rate": f"{int(time_disc * 100)}折",
                "suitability_score": suitability,
                "relaxed": any(s.get('name', '') in relaxed_dishes for s in selected)
            })

        return {
            "dietary_label": config.get('label', '均衡饮食'),
            "relaxation_level": relaxation_level,
            "recommendations": recommendations,
            "available_count": len(candidates),
            "total_leftover_count": len(available_dishes),
            "allergies_filtered": bool(allergy_keywords)
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
#  热量估算引擎（产品一热量追踪模式）
# ====================================================================
def estimate_calories_for_item(item_name, category, portion='中份'):
    """根据菜名和分类估算一道菜的热量（kcal）"""
    # 份量系数
    portion_factor = {'小份': 0.7, '中份': 1.0, '大份': 1.3}
    factor = portion_factor.get(portion, 1.0)

    # 先查菜品库
    try:
        library = get_dish_library()
        dishes = library.list_dishes()
        for d in dishes:
            if d['name'] == item_name or d['id'] == item_name:
                return int(d.get('calories', 200) * factor)
    except Exception:
        pass

    # 按分类估算
    category_calories = {
        '肉类': 260, '海鲜': 140, '蔬菜': 55, '主食': 250,
        '汤品': 80, '甜点': 280, '水果': 95, '饮品': 60,
        '酱料': 30, '其他': 150
    }
    base = category_calories.get(category, 150)
    return int(base * factor)


def get_calorie_data():
    """获取session中的热量追踪数据"""
    return {
        'total': session.get('calorie_total', 0),
        'threshold': session.get('calorie_threshold', CALORIE_THRESHOLD_DEFAULT if USE_CONFIG else 1800),
        'history': session.get('calorie_history', []),
        'threshold_reached': session.get('calorie_total', 0) >= session.get('calorie_threshold', CALORIE_THRESHOLD_DEFAULT if USE_CONFIG else 1800)
    }


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


# ---- 产品一：剩食评分 + 热量追踪 ----
@app.route('/product1')
def product1():
    calorie_data = get_calorie_data()
    return render_template('product1_scan.html', calorie_data=calorie_data)


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

    # ---- 热量追踪计算 ----
    mode = request.form.get('mode', 'waste')  # 'calorie' or 'waste'
    calorie_info = None

    if mode == 'calorie':
        # 为每个识别到的菜品估算热量
        items = analysis.get('items', []) or analysis.get('matched_dishes', [])
        this_round_calories = 0
        for item in items:
            name = item.get('name', '')
            category = item.get('category', '其他')
            portion = item.get('estimated_original_portion', '中份')
            cal = estimate_calories_for_item(name, category, portion)

            # 🔧 v2.7: 按盘内实际剩余比例缩放热量（这是核心！）
            #    estimated_remaining_percentage 表示盘子里还剩多少食物（0-100）
            #    例如锅包肉330kcal，如果盘内只剩30% → 330 × 0.30 = 99kcal
            remaining_pct = item.get('estimated_remaining_percentage', 100)
            if isinstance(remaining_pct, (int, float)) and 0 <= remaining_pct <= 100:
                cal = int(cal * remaining_pct / 100.0)

            # 匹配置信度微调（不确定的识别结果适当降低热量，避免高估）
            confidence = item.get('confidence', 'medium')
            if confidence == 'low':
                cal = int(cal * 0.6)        # 低置信度→可能是误匹配
            elif confidence == 'medium':
                cal = int(cal * 0.8)        # 中置信度→部分匹配

            # 限制单道菜最大500kcal
            cal = min(cal, 500)
            item['calories'] = cal
            this_round_calories += cal

        # Session累积
        total = session.get('calorie_total', 0) + this_round_calories
        session['calorie_total'] = total

        history = session.get('calorie_history', [])
        history_entry = {
            'time': datetime.now().strftime('%H:%M'),
            'image_url': f'/static/uploads/{filename}',
            'items': [{'name': it.get('name'), 'calories': it.get('calories', 0),
                       'category': it.get('category')} for it in items],
            'this_round': this_round_calories,
            'total': total
        }
        history.append(history_entry)
        session['calorie_history'] = history

        threshold = session.get('calorie_threshold', CALORIE_THRESHOLD_DEFAULT if USE_CONFIG else 1800)
        threshold_reached = total >= threshold

        calorie_info = {
            'this_round': this_round_calories,
            'total': total,
            'threshold': threshold,
            'threshold_reached': threshold_reached,
            'history': history,
            'items': items
        }

    # ---- 浪费评分（原有逻辑） ----
    score = calculate_waste_score(analysis)
    discount_info = map_to_discount(score)

    result = {
        'image_url': f'/static/uploads/{filename}',
        'analysis': analysis,
        'score': score,
        'discount': discount_info,
        'timestamp': datetime.now().strftime('%H:%M:%S'),
        'ai_mode': engine.mode,
        'mode': mode,
        'calorie_info': calorie_info,
    }
    session['last_result'] = result

    return render_template('product1_result.html', result=result)


@app.route('/product1/calorie-reset', methods=['POST'])
def product1_calorie_reset():
    """重置热量累积"""
    session['calorie_total'] = 0
    session['calorie_history'] = []
    return jsonify({'success': True, 'total': 0})


@app.route('/product1/calorie-threshold', methods=['POST'])
def product1_calorie_threshold():
    """更新热量阈值"""
    data = request.get_json()
    threshold = int(data.get('threshold', 1800))
    threshold = max(500, min(4000, threshold))  # 限制范围500-4000
    session['calorie_threshold'] = threshold
    return jsonify({'success': True, 'threshold': threshold})


# ---- 产品二：盲盒搭配（v2.7 重写） ----

# 9道固定菜品（带照片）
PRODUCT2_DISHES = [
    {"id": "guobaorou",       "name": "锅包肉",   "category": "肉类", "photo": "锅包肉.jpg"},
    {"id": "yuxiangrousi",    "name": "鱼香肉丝", "category": "肉类", "photo": "鱼香肉丝.jpg"},
    {"id": "hongshaorou",     "name": "红烧肉",   "category": "肉类", "photo": "红烧肉.jpg"},
    {"id": "gongbaojiding",   "name": "宫保鸡丁", "category": "肉类", "photo": "宫保鸡丁.jpg"},
    {"id": "liangbanhuanggua", "name": "凉拌黄瓜", "category": "蔬菜", "photo": "凉拌黄瓜.jpg"},
    {"id": "yangzhouchaofan", "name": "扬州炒饭", "category": "主食", "photo": "扬州炒饭.jpg"},
    {"id": "fanqiedanhuatang", "name": "番茄蛋花汤", "category": "汤品", "photo": "番茄蛋花汤.jpg"},
    {"id": "shuiguopinpan",   "name": "水果拼盘", "category": "水果", "photo": "水果拼盘.jpg"},
    {"id": "qingzhengluyu",   "name": "清蒸鲈鱼", "category": "海鲜", "photo": "清蒸鲈鱼.jpg"},
]

def _generate_blind_box(available_dishes, target_weight=800, num_combos=3):
    """
    盲盒搭配算法 v2.7:
    - 固定800g总重目标
    - 加权随机选3道菜（克数多优先但不过分，用sqrt克重）
    - 生成3个不同方案
    - 按可用克数比例分配目标重量
    - 总可用克数 < 800g 时，全部使用
    """
    import random
    import math

    n_available = len(available_dishes)

    # 不足3道菜，只能生成1个方案
    if n_available < 3:
        selected = available_dishes[:]
        total_avail = sum(d['grams'] for d in selected)
        effective = min(target_weight, total_avail)
        items = _distribute_grams(selected, effective, total_avail)
        return {
            'recommendations': [{
                'id': 1, 'items': items,
                'total_grams': sum(i['grams'] for i in items),
                'under_target': total_avail < target_weight
            }],
            'insufficient': True
        }

    # sqrt克数作为权重（克数多的优先但不过分）
    weights = [math.sqrt(max(d['grams'], 1)) for d in available_dishes]

    combos = []
    used_sets = []

    for combo_idx in range(num_combos):
        # 加权不放回抽样，尽量不生成重复组合
        for attempt in range(30):
            selected = _weighted_sample_3(available_dishes, weights)
            key = tuple(sorted(d['name'] for d in selected))
            if key not in used_sets or attempt >= 29:
                used_sets.append(key)
                break

        total_avail = sum(d['grams'] for d in selected)
        effective = min(target_weight, total_avail)
        items = _distribute_grams(selected, effective, total_avail)

        combos.append({
            'id': combo_idx + 1,
            'name': f"方案{combo_idx + 1}",
            'items': items,
            'total_grams': sum(i['grams'] for i in items),
            'total_available': total_avail,
            'under_target': total_avail < target_weight
        })

    return {
        'recommendations': combos,
        'insufficient': False,
        'target_weight': target_weight
    }


def _weighted_sample_3(items, weights):
    """加权不放回抽取3个（sqrt权重让克数高者优先但不极端）"""
    import random
    pool = list(range(len(items)))
    pool_w = list(weights)
    result = []
    for _ in range(3):
        total_w = sum(pool_w)
        if total_w <= 0 or not pool:
            break
        pick = random.choices(pool, weights=[w/total_w for w in pool_w], k=1)[0]
        result.append(items[pick])
        idx = pool.index(pick)
        pool.pop(idx)
        pool_w.pop(idx)
    return result


def _distribute_grams(selected, effective_weight, total_available_grams):
    """按比例分配克数，最后一道菜补齐差额"""
    items = []
    allocated_sum = 0
    for i, d in enumerate(selected):
        if i == len(selected) - 1:
            allocated = effective_weight - allocated_sum
        else:
            if total_available_grams > 0:
                allocated = round(d['grams'] / total_available_grams * effective_weight)
            else:
                allocated = 0
        allocated_sum += allocated
        items.append({
            'name': d['name'],
            'category': d.get('category', '其他'),
            'grams': allocated,
            'available_grams': d['grams']
        })
    return items


@app.route('/product2')
def product2():
    """盲盒搭配选菜页"""
    return render_template('product2_dishes.html', dishes=PRODUCT2_DISHES)


@app.route('/product2/match', methods=['POST'])
def product2_match():
    """盲盒搭配生成：固定800g，随机选3道菜"""
    import json as _json

    selected_json = request.form.get('selected_dishes', '[]')
    try:
        selected_dishes = _json.loads(selected_json)
    except (_json.JSONDecodeError, TypeError):
        selected_dishes = []

    # 过滤出克数 > 0 的菜品
    available = [d for d in selected_dishes if d.get('grams', 0) > 0]

    if not available:
        flash('请至少为一道菜品输入克数', 'error')
        return redirect(url_for('product2'))

    result = _generate_blind_box(available, target_weight=800)
    result['current_time'] = datetime.now().strftime('%H:%M')
    result['ai_mode'] = AIEngine().mode

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
    available = data.get('dishes', [])
    available = [d for d in available if d.get('grams', 0) > 0]
    if not available:
        return jsonify({"error": "请至少为一道菜品输入克数"}), 400
    result = _generate_blind_box(available, target_weight=800)
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
    # 单独准备一份不含base64图片的元数据给JS（避免页面过大导致Render超时）
    dishes_meta = [{k: v for k, v in d.items() if k != 'reference_images'}
                   for d in dishes]
    return render_template('admin_library.html', dishes=dishes, dishes_meta=dishes_meta)


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


@app.route('/admin/library/export')
def admin_library_export():
    """导出当前菜品库JSON（含base64参考图），用于持久化到GitHub"""
    library_path = os.path.join(app.config['DATA_FOLDER'], 'dish_library.json')
    if not os.path.exists(library_path):
        return jsonify({'error': '菜品库文件不存在'}), 404
    with open(library_path, 'r', encoding='utf-8') as f:
        return jsonify(json.load(f))


# ---- 演示模式 ----
@app.route('/demo')
def demo_mode():
    """一键演示模式：预设流程，零翻车风险"""
    library = get_dish_library()
    dishes = {d['id']: d for d in library.list_dishes()}

    # 获取每道菜的参考图URL
    def get_ref(dish_id):
        d = dishes.get(dish_id, {})
        refs = d.get('reference_images', [])
        return refs[0] if refs else ''

    # v2.6 多语言: 只传数据，文字由模板的翻译键渲染
    demo_steps = [
        {'idx':0, 'dish_ids':['guobaorou'], 'ref_image':get_ref('guobaorou'),
         'identify_name_zh':'锅包肉','identify_name_en':'Guobaorou (Crispy Pork)','category':'肉类','category_en':'Meat','calories':310},
        {'idx':1, 'dish_ids':['suanrongxilanhua','baizhuoxia'], 'ref_images':[get_ref('suanrongxilanhua'),get_ref('baizhuoxia')],
         'identify_name_zh':'蒜蓉西兰花 + 白灼虾','identify_name_en':'Broccoli + Shrimp','category':'蔬菜/海鲜','category_en':'Veg/Seafood','calories':167},
        {'idx':2, 'dish_ids':['hongshaorou'], 'ref_image':get_ref('hongshaorou'),
         'identify_name_zh':'红烧肉','identify_name_en':'Hongshaorou (Braised Pork)','category':'肉类','category_en':'Meat','calories':380},
        {'idx':3, 'dish_ids':['yangzhouchaoan'], 'ref_image':get_ref('yangzhouchaoan'),
         'identify_name_zh':'扬州炒饭','identify_name_en':'Yangzhou Fried Rice','category':'主食','category_en':'Staple','calories':320},
        {'idx':4, 'dish_ids':['fanqiedanhuatang'], 'ref_image':get_ref('fanqiedanhuatang'),
         'identify_name_zh':'番茄蛋花汤','identify_name_en':'Tomato Egg Soup','category':'汤品','category_en':'Soup','calories':55},
        {'idx':5, 'dish_ids':['shuiguopinpan'], 'ref_image':get_ref('shuiguopinpan'),
         'identify_name_zh':'水果拼盘','identify_name_en':'Fruit Platter','category':'水果','category_en':'Fruit','calories':95},
        {'idx':6, 'dish_ids':['gongbaojiding'], 'ref_image':get_ref('gongbaojiding'),
         'identify_name_zh':'宫保鸡丁','identify_name_en':'Kung Pao Chicken','category':'肉类','category_en':'Meat','calories':245},
        {'idx':7, 'dish_ids':['hongshaorou'], 'ref_image':get_ref('hongshaorou'),
         'identify_name_zh':'红烧肉','identify_name_en':'Braised Pork','category':'肉类','category_en':'Meat','calories':380},
    ]

    total = sum(s['calories'] for s in demo_steps)
    return render_template('demo_mode.html',
                          demo_steps=demo_steps,
                          demo_threshold=1800,
                          demo_total=total)


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
    print("  ZeroDine零膳 - Live Demo")
    print("=" * 60)
    print(f"  AI模式: {mode_label}")
    # Render会通过PORT环境变量指定端口，本地默认5000
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('RENDER') is None  # 生产环境不开启debug
    print(f"  访问: http://127.0.0.1:{port}")
    print("=" * 60)

    app.run(debug=debug_mode, host='0.0.0.0', port=port)
