"""
ZeroDine零膳 - 基本测试
pytest: 测试评分引擎、折扣映射、热量估算等核心逻辑
"""
import sys
import os
import json
import math

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 从 app 导入核心函数
from app import calculate_waste_score, map_to_discount, estimate_calories_for_item


class TestWasteScore:
    """测试剩食评分引擎"""

    def test_perfect_score(self):
        """空餐盘 = 100分"""
        analysis = {"items": []}
        assert calculate_waste_score(analysis) == 100.0

    def test_no_items_field(self):
        """没有 items 字段应返回 100"""
        analysis = {}
        assert calculate_waste_score(analysis) == 100.0

    def test_partial_waste(self):
        """部分剩余应扣分"""
        analysis = {
            "items": [
                {"name": "米饭", "category": "主食", "estimated_remaining_percentage": 30},
                {"name": "青菜", "category": "蔬菜", "estimated_remaining_percentage": 10},
            ]
        }
        score = calculate_waste_score(analysis)
        assert 0 < score < 100
        assert isinstance(score, float)

    def test_high_waste(self):
        """大量剩余应得低分"""
        analysis = {
            "items": [
                {"name": "红烧肉", "category": "肉类", "estimated_remaining_percentage": 90},
                {"name": "米饭", "category": "主食", "estimated_remaining_percentage": 80},
            ]
        }
        score = calculate_waste_score(analysis)
        assert score < 30  # 大量剩余得分应该很低


class TestDiscountMapping:
    """测试折扣映射"""

    def test_top_discount(self):
        """最优得分对应最高折扣"""
        result = map_to_discount(96)
        assert result["discount"] == 0.85
        assert result["stars"] == 5

    def test_good_score(self):
        """85分以上得4星9折"""
        result = map_to_discount(90)
        assert result["discount"] == 0.90
        assert result["stars"] == 4

    def test_medium_score(self):
        """70-85分得3星95折"""
        result = map_to_discount(75)
        assert result["discount"] == 0.95
        assert result["stars"] == 3

    def test_low_score(self):
        """低于30分无折扣"""
        result = map_to_discount(20)
        assert result["discount"] == 1.0
        assert result["stars"] == 0

    def test_boundary_values(self):
        """边界值测试"""
        assert map_to_discount(95)["stars"] == 5
        assert map_to_discount(85)["stars"] == 4
        assert map_to_discount(70)["stars"] == 3
        assert map_to_discount(50)["stars"] == 2
        assert map_to_discount(30)["stars"] == 1
        assert map_to_discount(29)["stars"] == 0


class TestCalorieEstimation:
    """测试热量估算"""

    def test_known_dish(self):
        """已知菜品应返回合理值"""
        cal = estimate_calories_for_item("白米饭", "主食")
        assert 100 < cal < 500

    def test_unknown_dish(self):
        """未知菜品应基于分类估算"""
        cal = estimate_calories_for_item("神秘新菜", "肉类")
        assert 50 < cal < 800

    def test_portion_factor(self):
        """份量系数应正确影响热量"""
        small = estimate_calories_for_item("白米饭", "主食", "小份")
        large = estimate_calories_for_item("白米饭", "主食", "大份")
        assert small < large


class TestConfig:
    """测试配置导入"""

    def test_config_import(self):
        """config.py 应可正常导入"""
        try:
            from config import (
                CALORIE_THRESHOLD_DEFAULT,
                CATEGORY_WEIGHTS,
                WASTE_SCORE_GRADES,
            )
            assert CALORIE_THRESHOLD_DEFAULT == 1800
            assert "肉类" in CATEGORY_WEIGHTS
            assert len(WASTE_SCORE_GRADES) > 0
        except ImportError:
            assert False, "config.py 导入失败"
