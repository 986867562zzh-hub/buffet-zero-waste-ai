"""
ZeroDine零膳 v2.6 — 多语言翻译
支持: zh-CN(简体中文) / zh-TW(繁體中文) / en(English)
用法: from translations import get_text; get_text('key', 'zh-TW')
"""
from flask import session

# 语言配置
LANGUAGES = {
    'zh-CN': '简体中文',
    'zh-TW': '繁體中文',
    'en': 'English'
}

def get_lang():
    """获取当前会话语言"""
    lang = session.get('lang', 'zh-CN') if session else 'zh-CN'
    return lang if lang in LANGUAGES else 'zh-CN'

# ═══════════════════════════════════════════
# 翻译字典: key → {zh-CN, zh-TW, en}
# ═══════════════════════════════════════════
T = {
    # ── 导航栏 ──
    'nav.home': {'zh-CN':'首页','zh-TW':'首頁','en':'Home'},
    'nav.waste_score': {'zh-CN':'剩食评分','zh-TW':'剩食評分','en':'Waste Score'},
    'nav.meal_match': {'zh-CN':'剩菜搭配','zh-TW':'剩菜搭配','en':'Meal Match'},
    'nav.blind_box': {'zh-CN':'盲盒搭配','zh-TW':'盲盒搭配','en':'Blind Box'},
    'nav.dish_library': {'zh-CN':'菜品库','zh-TW':'菜品庫','en':'Dish Library'},
    'nav.role_customer': {'zh-CN':'食客','zh-TW':'食客','en':'Diner'},
    'nav.role_hotel': {'zh-CN':'酒店','zh-TW':'酒店','en':'Hotel'},
    'nav.theme_toggle': {'zh-CN':'切换暗色/亮色模式','zh-TW':'切換暗色/亮色模式','en':'Toggle dark/light mode'},
    'nav.skip_to_main': {'zh-CN':'跳到主要内容','zh-TW':'跳到主要內容','en':'Skip to main content'},
    'footer.title': {'zh-CN':'ZeroDine零膳 — AI视觉识别驱动的自助餐零废弃方案','zh-TW':'ZeroDine零膳 — AI視覺識別驅動的自助餐零廢棄方案','en':'ZeroDine — AI Vision-Driven Buffet Zero-Waste Solution'},
    'footer.school': {'zh-CN':'澳门科技大学 · 智慧旅游专题研究 · 黃穎祚老师','zh-TW':'澳門科技大學 · 智慧旅遊專題研究 · 黃穎祚老師','en':'Macau University of Science and Technology · Smart Tourism · Prof. Huang Yingzuo'},

    # ── 首页 ──
    'index.title': {'zh-CN':'ZeroDine零膳 — 首页','zh-TW':'ZeroDine零膳 — 首頁','en':'ZeroDine — Home'},
    'index.hero_title': {'zh-CN':'ZeroDine<span style="color:#ffa502;">零膳</span>','zh-TW':'ZeroDine<span style="color:#ffa502;">零膳</span>','en':'Zero<span style="color:#ffa502;">Dine</span>'},
    'index.hero_subtitle': {'zh-CN':'取之有度，食之无剩，ZeroDine 守护每一份食材。','zh-TW':'取之有度，食之無剩，ZeroDine 守護每一份食材。','en':'Take what you need, leave no waste. ZeroDine protects every ingredient.'},
    'index.hero_desc': {'zh-CN':'基于 <strong>固定菜品库 + AI视觉匹配</strong> 技术<br>减少食物浪费 · 智能折扣激励 · 剩菜二次利用','zh-TW':'基於 <strong>固定菜品庫 + AI視覺匹配</strong> 技術<br>減少食物浪費 · 智能折扣激勵 · 剩菜二次利用','en':'Powered by <strong>Fixed Menu Library + AI Vision Matching</strong><br>Reduce food waste · Smart discount incentives · Leftover reuse'},
    'index.stat_waste': {'zh-CN':'食物浪费','zh-TW':'食物浪費','en':'Food Waste'},
    'index.stat_discount': {'zh-CN':'最高折扣','zh-TW':'最高折扣','en':'Max Discount'},
    'index.stat_plans': {'zh-CN':'盲盒方案','zh-TW':'盲盒方案','en':'Blind Box Plans'},
    'index.demo_badge': {'zh-CN':'🎬 新功能','zh-TW':'🎬 新功能','en':'🎬 New'},
    'index.demo_title': {'zh-CN':'一键演示模式','zh-TW':'一鍵演示模式','en':'One-Click Demo'},
    'index.demo_desc': {'zh-CN':'预设6步完整流程，零翻车风险，适合课堂展示','zh-TW':'預設6步完整流程，零翻車風險，適合課堂展示','en':'Pre-set 6-step workflow, zero risk, perfect for classroom demos'},
    'index.product1_badge': {'zh-CN':'产品一','zh-TW':'產品一','en':'Product 1'},
    'index.product1_title': {'zh-CN':'剩食评分折扣系统','zh-TW':'剩食評分折扣系統','en':'Leftover Scoring & Discount'},
    'index.product1_desc': {'zh-CN':'消费者用餐后拍摄餐盘照片，AI视觉识别剩余食物，自动生成浪费评分。光盘行动 = 最高<strong>85折</strong>优惠！用经济激励减少食物浪费。','zh-TW':'消費者用餐後拍攝餐盤照片，AI視覺識別剩餘食物，自動生成浪費評分。光盤行動 = 最高<strong>85折</strong>優惠！用經濟激勵減少食物浪費。','en':'Take a photo of your plate after dining. AI identifies leftovers and generates a waste score. Clean Plate = up to <strong>15% off</strong>! Economic incentives to reduce food waste.'},
    'index.product1_feat1': {'zh-CN':'GPT-4o Vision 智能图像识别','zh-TW':'GPT-4o Vision 智能圖像識別','en':'AI-Powered Image Recognition'},
    'index.product1_feat2': {'zh-CN':'多维度加权评分算法','zh-TW':'多維度加權評分算法','en':'Multi-Dimensional Scoring'},
    'index.product1_feat3': {'zh-CN':'5级折扣自动映射','zh-TW':'5級折扣自動映射','en':'5-Tier Discount Mapping'},
    'index.product1_feat4': {'zh-CN':'历史记录与环保积分','zh-TW':'歷史記錄與環保積分','en':'History & Eco Points'},
    'index.product2_badge': {'zh-CN':'产品二','zh-TW':'產品二','en':'Product 2'},
    'index.product2_title': {'zh-CN':'盲盒搭配系统','zh-TW':'盲盒搭配系統','en':'Blind Box Composer'},
    'index.product2_desc': {'zh-CN':'厨房端输入每道剩余菜品的克数，系统<strong>加权随机搭配3道菜</strong>，固定800g总重，生成3种盲盒方案供厨师选择配餐。','zh-TW':'廚房端輸入每道剩餘菜品的克數，系統<strong>加權隨機搭配3道菜</strong>，固定800g總重，生成3種盲盒方案供廚師選擇配餐。','en':'Kitchen staff enter grams of leftover dishes. System <strong>randomly picks 3 dishes</strong> with weighted selection, fixed 800g total, generating 3 blind box options for chefs.'},
    'index.product2_feat1': {'zh-CN':'固定800g盲盒搭配','zh-TW':'固定800g盲盒搭配','en':'Fixed 800g Blind Box'},
    'index.product2_feat2': {'zh-CN':'加权随机3菜组合','zh-TW':'加權隨機3菜組合','en':'Weighted 3-Dish Picks'},
    'index.product2_feat3': {'zh-CN':'克重比例智能分配','zh-TW':'克重比例智能分配','en':'Proportional Gram Distribution'},
    'index.product2_feat4': {'zh-CN':'厨房出餐单可打印','zh-TW':'廚房出餐單可打印','en':'Printable Kitchen Order'},
    'index.start_btn': {'zh-CN':'开始体验','zh-TW':'開始體驗','en':'Get Started'},
    # v2.7 角色分流
    'index.role_title': {'zh-CN':'请选择您的身份','zh-TW':'請選擇您的身份','en':'Select Your Role'},
    'index.role_customer': {'zh-CN':'🍽️ 我是食客','zh-TW':'🍽️ 我是食客','en':'🍽️ I\'m a Diner'},
    'index.role_customer_desc': {'zh-CN':'用餐后拍照上传餐盘，AI识别剩食并评分，光盘行动拿折扣','zh-TW':'用餐後拍照上傳餐盤，AI識別剩食並評分，光盤行動拿折扣','en':'Take a photo of your plate after dining. AI scores your leftovers and rewards clean plates with discounts.'},
    'index.role_customer_btn': {'zh-CN':'📸 拍照评分','zh-TW':'📸 拍照評分','en':'📸 Scan & Score'},
    'index.role_hotel': {'zh-CN':'🏨 我是酒店','zh-TW':'🏨 我是酒店','en':'🏨 I\'m Hotel Staff'},
    'index.role_hotel_desc': {'zh-CN':'输入剩余菜品克数，AI随机搭配3菜800g盲盒，管理菜品库','zh-TW':'輸入剩餘菜品克數，AI隨機搭配3菜800g盲盒，管理菜品庫','en':'Enter leftover grams. AI randomly picks 3 dishes for an 800g blind box. Manage dish library.'},
    'index.role_hotel_btn': {'zh-CN':'🎲 盲盒搭配','zh-TW':'🎲 盲盒搭配','en':'🎲 Blind Box'},
    'index.role_hotel_library': {'zh-CN':'📋 菜品库管理','zh-TW':'📋 菜品庫管理','en':'📋 Dish Library'},
    'index.workflow_title': {'zh-CN':'系统工作流程','zh-TW':'系統工作流程','en':'System Workflow'},
    'index.wf_step1_title': {'zh-CN':'📸 拍照上传','zh-TW':'📸 拍照上傳','en':'📸 Photo Upload'},
    'index.wf_step1_desc': {'zh-CN':'消费者/餐厅拍摄照片上传系统','zh-TW':'消費者/餐廳拍攝照片上傳系統','en':'Customer/staff upload photos'},
    'index.wf_step2_title': {'zh-CN':'🤖 AI识别分析','zh-TW':'🤖 AI識別分析','en':'🤖 AI Analysis'},
    'index.wf_step2_desc': {'zh-CN':'固定菜品库闭集匹配，精准识别12道菜','zh-TW':'固定菜品庫閉集匹配，精準識別12道菜','en':'Fixed-menu closed-set matching, 12 dishes'},
    'index.wf_step3_title': {'zh-CN':'📊 盲盒生成','zh-TW':'📊 盲盒生成','en':'📊 Blind Box'},
    'index.wf_step3_desc': {'zh-CN':'加权随机选菜·800g总重约束·3方案输出','zh-TW':'加權隨機選菜·800g總重約束·3方案輸出','en':'Weighted picks · 800g target · 3 options'},
    'index.wf_step4_title': {'zh-CN':'🏷️ 出餐打印','zh-TW':'🏷️ 出餐打印','en':'🏷️ Print Order'},
    'index.wf_step4_desc': {'zh-CN':'菜品克数清单·厨房直接配菜','zh-TW':'菜品克數清單·廚房直接配菜','en':'Gram list · kitchen ready'},
    'index.tech_title': {'zh-CN':'技术架构','zh-TW':'技術架構','en':'Tech Architecture'},
    'index.tech1_title': {'zh-CN':'AI视觉识别','zh-TW':'AI視覺識別','en':'AI Vision'},
    'index.tech1_desc': {'zh-CN':'DeepSeek Vision API<br>闭集菜品库匹配<br>结构化JSON输出','zh-TW':'DeepSeek Vision API<br>閉集菜品庫匹配<br>結構化JSON輸出','en':'DeepSeek Vision API<br>Closed-set matching<br>Structured JSON'},
    'index.tech2_title': {'zh-CN':'评分算法','zh-TW':'評分算法','en':'Scoring Algorithm'},
    'index.tech2_desc': {'zh-CN':'加权食物分类评分<br>多级折扣映射<br>实时计算响应','zh-TW':'加權食物分類評分<br>多級折扣映射<br>實時計算響應','en':'Weighted food scoring<br>Multi-tier discounts<br>Real-time response'},
    'index.tech3_title': {'zh-CN':'盲盒引擎','zh-TW':'盲盒引擎','en':'Blind Box Engine'},
    'index.tech3_desc': {'zh-CN':'sqrt克重加权随机<br>固定800g总重约束<br>3方案智能生成','zh-TW':'sqrt克重加權隨機<br>固定800g總重約束<br>3方案智能生成','en':'Weighted random selection<br>Fixed 800g target<br>3-plan generation'},
    'index.tech4_title': {'zh-CN':'云端部署','zh-TW':'雲端部署','en':'Cloud Deployment'},
    'index.tech4_desc': {'zh-CN':'Python Flask<br>Render.com 24/7在线<br>全平台响应式','zh-TW':'Python Flask<br>Render.com 24/7在線<br>全平台響應式','en':'Python Flask<br>Render.com 24/7 online<br>Responsive design'},

    # ── 面包屑 ──
    'breadcrumb.home': {'zh-CN':'首页','zh-TW':'首頁','en':'Home'},
    'breadcrumb.product1': {'zh-CN':'产品一：智能拍照识别','zh-TW':'產品一：智能拍照識別','en':'Product 1: Smart Photo Recognition'},
    'breadcrumb.product2': {'zh-CN':'产品二：剩菜智能搭配系统','zh-TW':'產品二：剩菜智能搭配系統','en':'Product 2: Leftover Meal Composer'},
    'breadcrumb.result': {'zh-CN':'分析结果','zh-TW':'分析結果','en':'Analysis Result'},
    'breadcrumb.match_result': {'zh-CN':'搭配结果','zh-TW':'搭配結果','en':'Matching Result'},
    'breadcrumb.demo': {'zh-CN':'🎬 演示模式','zh-TW':'🎬 演示模式','en':'🎬 Demo Mode'},

    # ── Product1 ──
    'p1.title': {'zh-CN':'拍照识别 - 热量追踪 & 剩食评分','zh-TW':'拍照識別 - 熱量追蹤 & 剩食評分','en':'Photo Recognition - Calorie Tracker & Waste Score'},
    'p1.tab_calorie': {'zh-CN':'热量追踪','zh-TW':'熱量追蹤','en':'Calorie Tracker'},
    'p1.tab_calorie_sub': {'zh-CN':'拿菜前拍一拍','zh-TW':'拿菜前拍一拍','en':'Snap before taking'},
    'p1.tab_waste': {'zh-CN':'剩食评分','zh-TW':'剩食評分','en':'Waste Score'},
    'p1.tab_waste_sub': {'zh-CN':'用餐后查浪费','zh-TW':'用餐後查浪費','en':'Check waste after meal'},
    'p1.calorie_title': {'zh-CN':'🔥 本次用餐热量累积','zh-TW':'🔥 本次用餐熱量累積','en':'🔥 Meal Calorie Accumulation'},
    'p1.calorie_unit': {'zh-CN':'kcal','zh-TW':'kcal','en':'kcal'},
    'p1.threshold_label': {'zh-CN':'提醒阈值','zh-TW':'提醒閾值','en':'Alert Threshold'},
    'p1.history_title': {'zh-CN':'拿菜记录','zh-TW':'拿菜記錄','en':'Meal History'},
    'p1.no_history': {'zh-CN':'还没有拍照记录哦~ 快去拿菜吧！','zh-TW':'還沒有拍照記錄哦~ 快去拿菜吧！','en':'No photos yet. Go grab some food!'},
    'p1.reset_btn': {'zh-CN':'重新开始','zh-TW':'重新開始','en':'Reset'},
    'p1.calorie_badge': {'zh-CN':'热量追踪','zh-TW':'熱量追蹤','en':'Calorie Tracker'},
    'p1.calorie_scan_title': {'zh-CN':'📸 拍下你拿的菜','zh-TW':'📸 拍下你拿的菜','en':'📸 Snap Your Plate'},
    'p1.calorie_scan_desc': {'zh-CN':'每次去自助餐台拿菜时拍一张，系统自动识别菜品并计算热量。当累积热量接近阈值时，会温柔提醒你别拿太多哦~','zh-TW':'每次去自助餐台拿菜時拍一張，系統自動識別菜品並計算熱量。當累積熱量接近閾值時，會溫柔提醒你別拿太多哦~','en':'Take a photo each time you visit the buffet. The system identifies dishes and tracks calories. A gentle reminder pops up when you approach your limit~'},
    'p1.upload_hint': {'zh-CN':'点击上传或拖拽餐盘照片','zh-TW':'點擊上傳或拖拽餐盤照片','en':'Click or drag to upload plate photo'},
    'p1.upload_format': {'zh-CN':'JPG / PNG / WebP，最大16MB','zh-TW':'JPG / PNG / WebP，最大16MB','en':'JPG / PNG / WebP, max 16MB'},
    'p1.take_photo_btn': {'zh-CN':'拍一张','zh-TW':'拍一張','en':'Take Photo'},
    'p1.identify_calorie_btn': {'zh-CN':'识别热量','zh-TW':'識別熱量','en':'Count Calories'},
    'p1.waste_title': {'zh-CN':'剩食评分折扣系统','zh-TW':'剩食評分折扣系統','en':'Leftover Scoring & Discount'},
    'p1.waste_desc': {'zh-CN':'拍摄用餐后的餐盘照片，AI识别剩余食物并生成浪费评分。光盘行动最高可享<strong class="text-success">85折</strong>！','zh-TW':'拍攝用餐後的餐盤照片，AI識別剩餘食物並生成浪費評分。光盤行動最高可享<strong class="text-success">85折</strong>！','en':'Take a photo of your plate after dining. AI identifies leftovers and generates a waste score. Clean Plate = up to <strong class="text-success">15% off</strong>!'},
    'p1.waste_scan_title': {'zh-CN':'请拍摄餐后餐盘','zh-TW':'請拍攝餐後餐盤','en':'Please photograph your plate'},
    'p1.waste_upload_hint': {'zh-CN':'点击上传或拖拽照片到此处','zh-TW':'點擊上傳或拖拽照片到此處','en':'Click or drag photo here'},
    'p1.select_photo_btn': {'zh-CN':'选择照片','zh-TW':'選擇照片','en':'Select Photo'},
    'p1.reselect_btn': {'zh-CN':'重新选择','zh-TW':'重新選擇','en':'Reselect'},
    'p1.analyze_btn': {'zh-CN':'开始分析','zh-TW':'開始分析','en':'Analyze'},
    'p1.discount_rules_title': {'zh-CN':'折扣规则','zh-TW':'折扣規則','en':'Discount Rules'},
    'p1.discount_tier1_label': {'zh-CN':'85折','zh-TW':'85折','en':'15% Off'},
    'p1.discount_tier1_desc': {'zh-CN':'95-100分 光盘英雄','zh-TW':'95-100分 光盤英雄','en':'95-100pts Clean Plate Hero'},
    'p1.discount_tier2_label': {'zh-CN':'9折','zh-TW':'9折','en':'10% Off'},
    'p1.discount_tier2_desc': {'zh-CN':'85-94分 少量剩余','zh-TW':'85-94分 少量剩餘','en':'85-94pts Light Leftovers'},
    'p1.discount_tier3_label': {'zh-CN':'95折','zh-TW':'95折','en':'5% Off'},
    'p1.discount_tier3_desc': {'zh-CN':'70-84分 中等剩余','zh-TW':'70-84分 中等剩餘','en':'70-84pts Moderate Leftovers'},

    # ── Product1 Result ──
    'p1r.result_title_calorie': {'zh-CN':'热量追踪','zh-TW':'熱量追蹤','en':'Calorie Tracker'},
    'p1r.result_title_waste': {'zh-CN':'剩食评分','zh-TW':'剩食評分','en':'Waste Score'},
    'p1r.your_plate': {'zh-CN':'你拿的菜','zh-TW':'你拿的菜','en':'Your Plate'},
    'p1r.your_leftover': {'zh-CN':'你的餐盘','zh-TW':'你的餐盤','en':'Your Plate'},
    'p1r.analysis_time': {'zh-CN':'分析时间','zh-TW':'分析時間','en':'Analysis Time'},
    'p1r.this_round_cal': {'zh-CN':'🔥 本次拿菜热量','zh-TW':'🔥 本次拿菜熱量','en':'🔥 This Round Calories'},
    'p1r.cumulative': {'zh-CN':'累积热量','zh-TW':'累積熱量','en':'Cumulative'},
    'p1r.threshold_reached_title': {'zh-CN':'已达提醒阈值！','zh-TW':'已達提醒閾值！','en':'Threshold Reached!'},
    'p1r.threshold_reached_msg': {'zh-CN':'肚肚已经圆滚滚啦！先吃完这些，不够再来拿嘛~ 🥰','zh-TW':'肚肚已經圓滾滾啦！先吃完這些，不夠再來拿嘛~ 🥰','en':'Your belly is full! Finish these first, then come back for more~ 🥰'},
    'p1r.dish_detail': {'zh-CN':'本盘菜品热量明细','zh-TW':'本盤菜品熱量明細','en':'Plate Calorie Details'},
    'p1r.table_dish': {'zh-CN':'菜品','zh-TW':'菜品','en':'Dish'},
    'p1r.table_category': {'zh-CN':'类别','zh-TW':'類別','en':'Category'},
    'p1r.table_portion': {'zh-CN':'份量','zh-TW':'份量','en':'Portion'},
    'p1r.table_calories': {'zh-CN':'热量','zh-TW':'熱量','en':'Calories'},
    'p1r.table_total': {'zh-CN':'本盘合计','zh-TW':'本盤合計','en':'Plate Total'},
    'p1r.ai_detail': {'zh-CN':'AI识别详情','zh-TW':'AI識別詳情','en':'AI Analysis Details'},
    'p1r.overall_waste': {'zh-CN':'整体浪费率','zh-TW':'整體浪費率','en':'Overall Waste Rate'},
    'p1r.retry_btn': {'zh-CN':'再拍一张','zh-TW':'再拍一張','en':'Take Another'},
    'p1r.try_match_btn': {'zh-CN':'体验剩菜搭配','zh-TW':'體驗剩菜搭配','en':'Try Meal Composer'},
    'p1r.retry_waste_btn': {'zh-CN':'重新分析','zh-TW':'重新分析','en':'Re-analyze'},
    'p1r.cute_title': {'zh-CN':'🐉 饱饱啦~','zh-TW':'🐉 飽飽啦~','en':'🐉 So full~'},
    'p1r.cute_btn': {'zh-CN':'好的，我知道了','zh-TW':'好的，我知道了','en':'OK, Got it'},
    'p1r.cute_reset': {'zh-CN':'重置继续拿','zh-TW':'重置繼續拿','en':'Reset & Continue'},

    # ── Product2 选菜 ──
    'p2.title': {'zh-CN':'剩菜智能搭配 - 选菜搭配','zh-TW':'剩菜智能搭配 - 選菜搭配','en':'Leftover Meal Composer - Select Dishes'},
    'p2.banner_title': {'zh-CN':'今日剩菜智能搭配','zh-TW':'今日剩菜智能搭配','en':'Today\'s Leftover Meal Composer'},
    'p2.banner_desc': {'zh-CN':'<strong>Step 1:</strong> 勾选今日剩余菜品并填写份数 → <strong>Step 2:</strong> 选择饮食需求 → <strong>Step 3:</strong> AI智能搭配折扣套餐','zh-TW':'<strong>Step 1:</strong> 勾選今日剩餘菜品並填寫份數 → <strong>Step 2:</strong> 選擇飲食需求 → <strong>Step 3:</strong> AI智能搭配折扣套餐','en':'<strong>Step 1:</strong> Select leftover dishes & quantity → <strong>Step 2:</strong> Choose dietary needs → <strong>Step 3:</strong> AI composes discount meal combos'},
    'p2.flow_label': {'zh-CN':'流程','zh-TW':'流程','en':'Flow'},
    'p2.flow_text': {'zh-CN':'✅ 选菜 → 🎯 需求 → 🍱 搭配','zh-TW':'✅ 選菜 → 🎯 需求 → 🍱 搭配','en':'✅ Select → 🎯 Needs → 🍱 Match'},
    'p2.step1_title': {'zh-CN':'Step 1: 勾选今日剩余菜品','zh-TW':'Step 1: 勾選今日剩餘菜品','en':'Step 1: Select Today\'s Leftovers'},
    'p2.step1_hint': {'zh-CN':'勾选菜品并填写剩余份数（1-15份），点击卡片即可选中','zh-TW':'勾選菜品並填寫剩餘份數（1-15份），點擊卡片即可選中','en':'Check dishes and enter remaining servings (1-15). Click card to select.'},
    'p2.select_all': {'zh-CN':'全选','zh-TW':'全選','en':'Select All'},
    'p2.clear_all': {'zh-CN':'清空','zh-TW':'清空','en':'Clear All'},
    'p2.cat_meat': {'zh-CN':'肉类','zh-TW':'肉類','en':'Meat'},
    'p2.cat_seafood': {'zh-CN':'海鲜','zh-TW':'海鮮','en':'Seafood'},
    'p2.cat_veggie': {'zh-CN':'蔬菜','zh-TW':'蔬菜','en':'Veggie'},
    'p2.cat_staple': {'zh-CN':'主食','zh-TW':'主食','en':'Staple'},
    'p2.cat_soup': {'zh-CN':'汤品','zh-TW':'湯品','en':'Soup'},
    'p2.qty_label': {'zh-CN':'份','zh-TW':'份','en':'servings'},
    'p2.selected_count': {'zh-CN':'道已选','zh-TW':'道已選','en':' selected'},
    'p2.step2_title': {'zh-CN':'Step 2: 选择饮食需求','zh-TW':'Step 2: 選擇飲食需求','en':'Step 2: Choose Dietary Needs'},
    'p2.consumer_badge': {'zh-CN':'消费者端','zh-TW':'消費者端','en':'Consumer'},
    'p2.allergy_label': {'zh-CN':'过敏原（可选）','zh-TW':'過敏原（可選）','en':'Allergies (optional)'},
    'p2.allergy_placeholder': {'zh-CN':'花生, 海鲜, 牛奶（逗号分隔）','zh-TW':'花生, 海鮮, 牛奶（逗號分隔）','en':'peanut, seafood, milk (comma separated)'},
    'p2.match_btn_empty': {'zh-CN':'AI智能搭配（请先选菜）','zh-TW':'AI智能搭配（請先選菜）','en':'AI Match (Select dishes first)'},
    'p2.match_btn': {'zh-CN':'AI智能搭配（','zh-TW':'AI智能搭配（','en':'AI Match ('},
    'p2.match_btn_suffix': {'zh-CN':'道菜品可选）','zh-TW':'道菜品可選）','en':' dishes available)'},
    'p2.match_footer': {'zh-CN':'DeepSeek AI 根据你的饮食需求，从选中的剩余菜品中智能搭配套餐','zh-TW':'DeepSeek AI 根據你的飲食需求，從選中的剩餘菜品中智能搭配套餐','en':'DeepSeek AI composes meal combos from selected leftovers based on your dietary needs'},
    'p2.loading_title': {'zh-CN':'AI 智能搭配中...','zh-TW':'AI 智能搭配中...','en':'AI Composing Meals...'},
    'p2.loading_sub': {'zh-CN':'DeepSeek 正在分析营养并生成套餐','zh-TW':'DeepSeek 正在分析營養並生成套餐','en':'DeepSeek analyzing nutrition & generating combos'},
    # v2.7 盲盒搭配
    'p2.blind_box_title': {'zh-CN':'固定800g 盲盒搭配','zh-TW':'固定800g 盲盒搭配','en':'Fixed 800g Blind Box'},
    'p2.blind_box_desc': {'zh-CN':'厨房端：输入每道菜的剩余克数，系统随机选3道菜搭配成800g盲盒','zh-TW':'廚房端：輸入每道菜的剩餘克數，系統隨機選3道菜搭配成800g盲盒','en':'Kitchen: Enter remaining grams per dish. System randomly picks 3 dishes for an 800g blind box.'},
    'p2.gram_input': {'zh-CN':'输入克数','zh-TW':'輸入克數','en':'Enter grams'},
    'p2.total_grams_label': {'zh-CN':'已选总克数','zh-TW':'已選總克數','en':'Total selected'},
    'p2.gram_unit': {'zh-CN':'g','zh-TW':'g','en':'g'},
    'p2.match_btn': {'zh-CN':'🎲 生成盲盒搭配','zh-TW':'🎲 生成盲盒搭配','en':'🎲 Generate Blind Box'},
    'p2.match_btn_disabled': {'zh-CN':'请至少输入一道菜的克数','zh-TW':'請至少輸入一道菜的克數','en':'Enter grams for at least one dish'},
    'p2.insufficient_warning': {'zh-CN':'选中的菜品少于3道，盲盒将包含所有可用菜品','zh-TW':'選中的菜品少於3道，盲盒將包含所有可用菜品','en':'Fewer than 3 dishes selected, blind box includes all available'},
    'p2.loading_title': {'zh-CN':'🎲 随机搭配中...','zh-TW':'🎲 隨機搭配中...','en':'🎲 Generating...'},
    'p2.loading_sub': {'zh-CN':'正在从可用菜品中随机选取3道菜','zh-TW':'正在從可用菜品中隨機選取3道菜','en':'Randomly picking 3 dishes...'},

    # ── Product2 Result ──
    'p2r.title': {'zh-CN':'搭配结果 - 剩菜智能搭配','zh-TW':'搭配結果 - 剩菜智能搭配','en':'Results - Leftover Meal Composer'},
    'p2r.dietary_label': {'zh-CN':'🏷️ 饮食需求','zh-TW':'🏷️ 飲食需求','en':'🏷️ Dietary Needs'},
    'p2r.allergy_avoid': {'zh-CN':'规避','zh-TW':'規避','en':'Avoid'},
    'p2r.ai_vision': {'zh-CN':'AI视觉识别','zh-TW':'AI視覺識別','en':'AI Vision'},
    'p2r.photos_to_dishes': {'zh-CN':'张照片 → ','zh-TW':'張照片 → ','en':' photos → '},
    'p2r.leftover_count': {'zh-CN':'道剩菜','zh-TW':'道剩菜','en':' leftover dishes'},
    'p2r.available_from': {'zh-CN':'从','zh-TW':'從','en':'From '},
    'p2r.available_filter': {'zh-CN':'道AI识别剩余菜品中，筛选出','zh-TW':'道AI識別剩餘菜品中，篩選出','en':' AI-identified dishes, '},
    'p2r.available_count': {'zh-CN':'道可用菜品','zh-TW':'道可用菜品','en':' available'},
    'p2r.recommend_title': {'zh-CN':'AI 为您推荐','zh-TW':'AI 為您推薦','en':'AI Recommends'},
    'p2r.recommend_suffix': {'zh-CN':'套搭配方案','zh-TW':'套搭配方案','en':' meal combos'},
    'p2r.best_badge': {'zh-CN':'最佳推荐','zh-TW':'最佳推薦','en':'Best Pick'},
    'p2r.suitability': {'zh-CN':'适配度','zh-TW':'適配度','en':'Match'},
    'p2r.score_unit': {'zh-CN':'分','zh-TW':'分','en':' pts'},
    'p2r.detail_title': {'zh-CN':'📋 搭配明细','zh-TW':'📋 搭配明細','en':'📋 Combo Details'},
    'p2r.original_price': {'zh-CN':'原价','zh-TW':'原價','en':'Original'},
    'p2r.discount_price': {'zh-CN':'折扣价','zh-TW':'折扣價','en':'Discount'},
    'p2r.save_label': {'zh-CN':'省','zh-TW':'省','en':'Save '},
    'p2r.nutrition_title': {'zh-CN':'📊 营养分析','zh-TW':'📊 營養分析','en':'📊 Nutrition'},
    'p2r.nut_calories': {'zh-CN':'热量','zh-TW':'熱量','en':'Calories'},
    'p2r.nut_protein': {'zh-CN':'蛋白质','zh-TW':'蛋白質','en':'Protein'},
    'p2r.nut_carbs': {'zh-CN':'碳水化合物','zh-TW':'碳水化合物','en':'Carbs'},
    'p2r.nut_fat': {'zh-CN':'脂肪','zh-TW':'脂肪','en':'Fat'},
    'p2r.nut_fiber': {'zh-CN':'膳食纤维','zh-TW':'膳食纖維','en':'Fiber'},
    'p2r.pickup_time': {'zh-CN':'取餐时间','zh-TW':'取餐時間','en':'Pickup Time'},
    'p2r.pickup_note': {'zh-CN':'起可到店取餐','zh-TW':'起可到店取餐','en':' available for pickup'},
    'p2r.order_btn': {'zh-CN':'立即下单','zh-TW':'立即下單','en':'Order Now'},
    'p2r.retry_btn': {'zh-CN':'换一种需求','zh-TW':'換一種需求','en':'Try Another'},
    'p2r.try_waste_btn': {'zh-CN':'体验剩食评分','zh-TW':'體驗剩食評分','en':'Try Waste Score'},
    'p2r.order_success': {'zh-CN':'下单成功！','zh-TW':'下單成功！','en':'Order Placed!'},
    'p2r.order_thanks': {'zh-CN':'感谢您为减少食物浪费做出贡献 🌱','zh-TW':'感謝您為減少食物浪費做出貢獻 🌱','en':'Thank you for reducing food waste 🌱'},
    'p2r.order_id': {'zh-CN':'订单号','zh-TW':'訂單號','en':'Order ID'},
    'p2r.order_combo': {'zh-CN':'套餐','zh-TW':'套餐','en':'Combo'},
    'p2r.order_price': {'zh-CN':'金额','zh-TW':'金額','en':'Amount'},
    'p2r.order_location': {'zh-CN':'取餐地点','zh-TW':'取餐地點','en':'Pickup Location'},
    'p2r.order_location_val': {'zh-CN':'酒店自助餐厅前台','zh-TW':'酒店自助餐廳前台','en':'Hotel Buffet Front Desk'},
    'p2r.order_time_warn': {'zh-CN':'请于 <strong>30分钟</strong> 内到店取餐','zh-TW':'請於 <strong>30分鐘</strong> 內到店取餐','en':'Please pick up within <strong>30 minutes</strong>'},
    'p2r.order_ok': {'zh-CN':'我知道了','zh-TW':'我知道了','en':'Got it'},
    # v2.7 盲盒搭配结果
    'p2r.blind_box_result': {'zh-CN':'🎲 盲盒搭配结果','zh-TW':'🎲 盲盒搭配結果','en':'🎲 Blind Box Result'},
    'p2r.dish': {'zh-CN':'菜品','zh-TW':'菜品','en':'Dish'},
    'p2r.grams': {'zh-CN':'所需克数','zh-TW':'所需克數','en':'Grams Needed'},
    'p2r.total_grams': {'zh-CN':'总重量','zh-TW':'總重量','en':'Total Weight'},
    'p2r.insufficient_note': {'zh-CN':'可用菜品不足3道，仅搭配以下菜品','zh-TW':'可用菜品不足3道，僅搭配以下菜品','en':'Fewer than 3 dishes available'},
    'p2r.under_target_note': {'zh-CN':'总可用克数不足800g，已全部使用','zh-TW':'總可用克數不足800g，已全部使用','en':'Total available < 800g, all used'},
    'p2r.regenerate_btn': {'zh-CN':'🔄 重新生成','zh-TW':'🔄 重新生成','en':'🔄 Regenerate'},
    'p2r.print_btn': {'zh-CN':'🖨️ 打印出餐单','zh-TW':'🖨️ 打印出餐單','en':'🖨️ Print Order'},
    'p2r.back_btn': {'zh-CN':'← 返回选菜','zh-TW':'← 返回選菜','en':'← Back to Selection'},

    # ── 演示模式 ──
    'demo.title': {'zh-CN':'演示模式 - 自助餐热量追踪','zh-TW':'演示模式 - 自助餐熱量追蹤','en':'Demo - Buffet Calorie Tracker'},
    'demo.badge': {'zh-CN':'🎬 演示模式','zh-TW':'🎬 演示模式','en':'🎬 Demo Mode'},
    'demo.heading': {'zh-CN':'自助餐热量追踪 — 完整演示','zh-TW':'自助餐熱量追蹤 — 完整演示','en':'Buffet Calorie Tracker — Full Demo'},
    'demo.desc': {'zh-CN':'模拟一位顾客在自助餐厅的真实用餐流程','zh-TW':'模擬一位顧客在自助餐廳的真實用餐流程','en':'Simulating a real customer dining experience at a buffet'},
    'demo.steps_title': {'zh-CN':'演示步骤','zh-TW':'演示步驟','en':'Demo Steps'},
    'demo.calorie_cumulative': {'zh-CN':'🔥 累积热量','zh-TW':'🔥 累積熱量','en':'🔥 Cumulative Calories'},
    'demo.threshold_warning': {'zh-CN':'⚠️ 接近阈值','zh-TW':'⚠️ 接近閾值','en':'⚠️ Near Threshold'},
    'demo.prev_btn': {'zh-CN':'上一步','zh-TW':'上一步','en':'Previous'},
    'demo.next_btn': {'zh-CN':'下一步','zh-TW':'下一步','en':'Next'},
    'demo.finish_btn': {'zh-CN':'完成演示','zh-TW':'完成演示','en':'Finish Demo'},
    'demo.final_title': {'zh-CN':'🐉 饱饱啦~','zh-TW':'🐉 飽飽啦~','en':'🐉 So Full~'},
    'demo.final_ok': {'zh-CN':'好的，我知道啦','zh-TW':'好的，我知道啦','en':'OK, Got It'},
    'demo.final_retry': {'zh-CN':'重新演示','zh-TW':'重新演示','en':'Restart Demo'},

    # ── 通用 ──
    'common.ai_analyzing': {'zh-CN':'AI 分析中...','zh-TW':'AI 分析中...','en':'AI Analyzing...'},
    'common.please_wait': {'zh-CN':'请稍候，正在 AI 分析...','zh-TW':'請稍候，正在 AI 分析...','en':'Please wait, AI is analyzing...'},
    'common.loading': {'zh-CN':'处理中...','zh-TW':'處理中...','en':'Processing...'},
    'common.confirm': {'zh-CN':'确定','zh-TW':'確定','en':'Confirm'},
    'common.cancel': {'zh-CN':'取消','zh-TW':'取消','en':'Cancel'},

    # ── Product1 拍照页深度文字 ──
    'p1.breadcrumb': {'zh-CN':'产品一：智能拍照识别','zh-TW':'產品一：智能拍照識別','en':'Product 1: Smart Photo Recognition'},
    'p1.mode_calorie': {'zh-CN':'热量追踪','zh-TW':'熱量追蹤','en':'Calorie Tracker'},
    'p1.mode_calorie_sub': {'zh-CN':'拿菜前拍一拍','zh-TW':'拿菜前拍一拍','en':'Snap before taking'},
    'p1.mode_waste': {'zh-CN':'剩食评分','zh-TW':'剩食評分','en':'Waste Score'},
    'p1.mode_waste_sub': {'zh-CN':'用餐后查浪费','zh-TW':'用餐後查浪費','en':'Check waste after meal'},
    'p1.calorie_title': {'zh-CN':'🔥 本次用餐热量累积','zh-TW':'🔥 本次用餐熱量累積','en':'🔥 Meal Calorie Total'},
    'p1.threshold_label': {'zh-CN':'提醒阈值','zh-TW':'提醒閾值','en':'Alert Threshold'},
    'p1.history_title': {'zh-CN':'📋 拿菜记录','zh-TW':'📋 拿菜記錄','en':'📋 History'},
    'p1.history_count': {'zh-CN':'次','zh-TW':'次','en':' times'},
    'p1.no_history': {'zh-CN':'还没有拍照记录哦~ 快去拿菜吧！','zh-TW':'還沒有拍照記錄哦~ 快去拿菜吧！','en':'No photos yet. Go grab some food!'},
    'p1.reset_btn': {'zh-CN':'重新开始','zh-TW':'重新開始','en':'Reset'},
    'p1.calorie_badge': {'zh-CN':'热量追踪','zh-TW':'熱量追蹤','en':'Calorie Tracker'},
    'p1.scan_title': {'zh-CN':'📸 拍下你拿的菜','zh-TW':'📸 拍下你拿的菜','en':'📸 Snap Your Plate'},
    'p1.scan_desc': {'zh-CN':'每次去自助餐台拿菜时拍一张，系统自动识别菜品并计算热量。当累积热量接近阈值时，会温柔提醒你别拿太多哦~','zh-TW':'每次去自助餐台拿菜時拍一張，系統自動識別菜品並計算熱量。當累積熱量接近閾值時，會溫柔提醒你別拿太多哦~','en':'Take a photo each time you visit the buffet. The system identifies dishes and tracks calories. A gentle reminder pops up when you approach your limit.'},
    'p1.upload_hint': {'zh-CN':'点击上传或拖拽餐盘照片','zh-TW':'點擊上傳或拖拽餐盤照片','en':'Click or drag to upload plate photo'},
    'p1.upload_format': {'zh-CN':'JPG / PNG / WebP，最大16MB','zh-TW':'JPG / PNG / WebP，最大16MB','en':'JPG / PNG / WebP, max 16MB'},
    'p1.take_photo_btn': {'zh-CN':'拍一张','zh-TW':'拍一張','en':'Take Photo'},
    'p1.identify_btn': {'zh-CN':'识别热量','zh-TW':'識別熱量','en':'Count Calories'},
    'p1.ai_analyzing': {'zh-CN':'AI识别中...','zh-TW':'AI識別中...','en':'AI Analyzing...'},
    'p1.reselect_btn': {'zh-CN':'重选','zh-TW':'重選','en':'Reselect'},
    'p1.waste_title': {'zh-CN':'剩食评分折扣系统','zh-TW':'剩食評分折扣系統','en':'Leftover Scoring & Discount'},
    'p1.waste_desc': {'zh-CN':'拍摄用餐后的餐盘照片，AI识别剩余食物并生成浪费评分。光盘行动最高可享<strong class="text-success">85折</strong>！','zh-TW':'拍攝用餐後的餐盤照片，AI識別剩餘食物並生成浪費評分。光盤行動最高可享<strong class="text-success">85折</strong>！','en':'Take a photo of your plate after dining. AI identifies leftovers and generates a waste score. Clean Plate = up to <strong class="text-success">15% off</strong>!'},
    'p1.waste_scan_title': {'zh-CN':'请拍摄餐后餐盘','zh-TW':'請拍攝餐後餐盤','en':'Please Photograph Your Plate'},
    'p1.waste_upload_hint': {'zh-CN':'点击上传或拖拽照片到此处','zh-TW':'點擊上傳或拖拽照片到此處','en':'Click or drag photo here'},
    'p1.select_photo_btn': {'zh-CN':'选择照片','zh-TW':'選擇照片','en':'Select Photo'},
    'p1.start_analysis': {'zh-CN':'开始分析','zh-TW':'開始分析','en':'Analyze'},
    'p1.discount_rules': {'zh-CN':'折扣规则','zh-TW':'折扣規則','en':'Discount Rules'},
    'p1.discount_tier1': {'zh-CN':'85折','zh-TW':'85折','en':'15% Off'},
    'p1.discount_tier1_desc': {'zh-CN':'95-100分 光盘英雄','zh-TW':'95-100分 光盤英雄','en':'95-100 Clean Plate Hero'},
    'p1.discount_tier2': {'zh-CN':'9折','zh-TW':'9折','en':'10% Off'},
    'p1.discount_tier2_desc': {'zh-CN':'85-94分 少量剩余','zh-TW':'85-94分 少量剩餘','en':'85-94 Light Leftovers'},
    'p1.discount_tier3': {'zh-CN':'95折','zh-TW':'95折','en':'5% Off'},
    'p1.discount_tier3_desc': {'zh-CN':'70-84分 中等剩余','zh-TW':'70-84分 中等剩餘','en':'70-84 Moderate Leftovers'},

    # ── Product1 结果页深度文字 ──
    'p1r.your_plate': {'zh-CN':'你拿的菜','zh-TW':'你拿的菜','en':'Your Plate'},
    'p1r.your_leftover': {'zh-CN':'你的餐盘','zh-TW':'你的餐盤','en':'Your Plate'},
    'p1r.analysis_time': {'zh-CN':'分析时间','zh-TW':'分析時間','en':'Analysis Time'},
    'p1r.closed_set_badge': {'zh-CN':'🔒 菜品库匹配模式','zh-TW':'🔒 菜品庫匹配模式','en':'🔒 Menu-Locked Mode'},
    'p1r.this_round_cal': {'zh-CN':'🔥 本次拿菜热量','zh-TW':'🔥 本次拿菜熱量','en':'🔥 This Round'},
    'p1r.cumulative': {'zh-CN':'累积热量','zh-TW':'累積熱量','en':'Cumulative'},
    'p1r.threshold_reached_title': {'zh-CN':'已达提醒阈值！','zh-TW':'已達提醒閾值！','en':'Threshold Reached!'},
    'p1r.threshold_reached_msg': {'zh-CN':'肚肚已经圆滚滚啦！先吃完这些，不够再来拿嘛~ 🥰','zh-TW':'肚肚已經圓滾滾啦！先吃完這些，不夠再來拿嘛~ 🥰','en':'Belly is full! Finish these first, then come back for more~'},
    'p1r.calorie_detail': {'zh-CN':'本盘菜品热量明细','zh-TW':'本盤菜品熱量明細','en':'Calorie Breakdown'},
    'p1r.table_dish': {'zh-CN':'菜品','zh-TW':'菜品','en':'Dish'},
    'p1r.table_category': {'zh-CN':'类别','zh-TW':'類別','en':'Category'},
    'p1r.table_portion': {'zh-CN':'份量','zh-TW':'份量','en':'Portion'},
    'p1r.table_calories': {'zh-CN':'热量','zh-TW':'熱量','en':'Calories'},
    'p1r.table_total': {'zh-CN':'本盘合计','zh-TW':'本盤合計','en':'Total'},
    'p1r.ai_detail_title': {'zh-CN':'AI识别详情','zh-TW':'AI識別詳情','en':'AI Analysis'},
    'p1r.overall_waste': {'zh-CN':'整体浪费率','zh-TW':'整體浪費率','en':'Overall Waste'},
    'p1r.table_food': {'zh-CN':'食物名称','zh-TW':'食物名稱','en':'Food'},
    'p1r.table_remain': {'zh-CN':'剩余比例','zh-TW':'剩餘比例','en':'Remaining'},
    'p1r.table_weight': {'zh-CN':'权重','zh-TW':'權重','en':'Weight'},
    'p1r.retry_btn': {'zh-CN':'再拍一张','zh-TW':'再拍一張','en':'Take Another'},
    'p1r.retry_waste_btn': {'zh-CN':'重新分析','zh-TW':'重新分析','en':'Re-analyze'},
    'p1r.try_match_btn': {'zh-CN':'体验剩菜搭配','zh-TW':'體驗剩菜搭配','en':'Try Meal Composer'},
    'p1r.cute_title': {'zh-CN':'🐉 饱饱啦~','zh-TW':'🐉 飽飽啦~','en':'🐉 So Full~'},
    'p1r.cute_ok': {'zh-CN':'好的，我知道了','zh-TW':'好的，我知道了','en':'OK, Got It'},
    'p1r.cute_reset': {'zh-CN':'重置继续拿','zh-TW':'重置繼續拿','en':'Reset & Continue'},
    'p1r.score_unit': {'zh-CN':'/ 100分','zh-TW':'/ 100分','en':'/ 100'},
    'p1.preview_alt': {'zh-CN':'预览','zh-TW':'預覽','en':'Preview'},
    'p1.invalid_file': {'zh-CN':'请选择JPG/PNG/GIF/WebP格式的图片','zh-TW':'請選擇JPG/PNG/GIF/WebP格式的圖片','en':'Please select JPG/PNG/GIF/WebP format'},
    'p1.ai_recognizing': {'zh-CN':'AI识别中...','zh-TW':'AI識別中...','en':'AI Analyzing...'},
    'p1.ai_analyzing_long': {'zh-CN':'AI正在识别...','zh-TW':'AI正在識別...','en':'AI is analyzing...'},
    'p1.history_empty': {'zh-CN':'还没有拍照记录哦~ 快去拿菜吧！','zh-TW':'還沒有拍照記錄哦~ 快去拿菜吧！','en':'No photos yet. Go grab some food!'},
    'p1.reset_confirm': {'zh-CN':'确定要重新开始热量累积吗？之前的记录会被清除哦~','zh-TW':'確定要重新開始熱量累積嗎？之前的記錄會被清除哦~','en':'Reset calorie tracking? Previous records will be cleared.'},
    'p1.reset_done': {'zh-CN':'已重置~ 去拿菜吧！','zh-TW':'已重置~ 去拿菜吧！','en':'Reset! Go grab some food!'},

    # ── Product2 result remaining ──
    'p2r.info_banner': {'zh-CN':'从 <strong>TOTAL</strong> 道AI识别剩余菜品中，筛选出 <strong>AVAIL</strong> 道可用菜品','zh-TW':'從 <strong>TOTAL</strong> 道AI識別剩餘菜品中，篩選出 <strong>AVAIL</strong> 道可用菜品','en':'From <strong>TOTAL</strong> identified dishes, <strong>AVAIL</strong> available'},
    'p2r.role_staple': {'zh-CN':'主食','zh-TW':'主食','en':'Staple'},
    'p2r.role_main': {'zh-CN':'主菜','zh-TW':'主菜','en':'Main'},
    'p2r.role_side': {'zh-CN':'配菜','zh-TW':'配菜','en':'Side'},
    'p2r.role_soup': {'zh-CN':'汤品','zh-TW':'湯品','en':'Soup'},
    'p2r.source_manual': {'zh-CN':'手动选择','zh-TW':'手動選擇','en':'Manual Selection'},

    # ── 演示模式 8步 ──
    'demo.title': {'zh-CN':'演示模式 - 自助餐热量追踪','zh-TW':'演示模式 - 自助餐熱量追蹤','en':'Demo - Buffet Calorie Tracker'},
    'demo.badge': {'zh-CN':'🎬 演示模式','zh-TW':'🎬 演示模式','en':'🎬 Demo Mode'},
    'demo.heading': {'zh-CN':'自助餐热量追踪 — 完整演示','zh-TW':'自助餐熱量追蹤 — 完整演示','en':'Buffet Calorie Tracker — Full Demo'},
    'demo.desc': {'zh-CN':'模拟一位顾客在自助餐厅的真实用餐流程','zh-TW':'模擬一位顧客在自助餐廳的真實用餐流程','en':'Simulating a real buffet dining experience'},
    'demo.steps_title': {'zh-CN':'演示步骤','zh-TW':'演示步驟','en':'Demo Steps'},
    'demo.calorie_label': {'zh-CN':'🔥 累积热量','zh-TW':'🔥 累積熱量','en':'🔥 Cumulative'},
    'demo.warning': {'zh-CN':'⚠️ 接近阈值','zh-TW':'⚠️ 接近閾值','en':'⚠️ Near Limit'},
    'demo.step_badge': {'zh-CN':'Step ','zh-TW':'Step ','en':'Step '},
    'demo.ai_identified': {'zh-CN':'✅ AI识别：','zh-TW':'✅ AI識別：','en':'✅ AI: '},
    'demo.dish_label': {'zh-CN':'菜品','zh-TW':'菜品','en':'Dish'},
    'demo.cat_label': {'zh-CN':'分类','zh-TW':'分類','en':'Category'},
    'demo.cal_label': {'zh-CN':'热量','zh-TW':'熱量','en':'Calories'},
    'demo.this_round': {'zh-CN':'🔥 本轮 +','zh-TW':'🔥 本輪 +','en':'🔥 +'},
    'demo.cumulative_label': {'zh-CN':'，累计 ','zh-TW':'，累計 ','en':', total '},
    'demo.cal_start': {'zh-CN':'🔥 开始热量累积！本轮 ','zh-TW':'🔥 開始熱量累積！本輪 ','en':'🔥 Starting! This round: '},
    'demo.cal_continue': {'zh-CN':'，累计 ','zh-TW':'，累計 ','en':', total '},
    'demo.prev_btn': {'zh-CN':'上一步','zh-TW':'上一步','en':'Previous'},
    'demo.next_btn': {'zh-CN':'下一步','zh-TW':'下一步','en':'Next'},
    'demo.finish_btn': {'zh-CN':'完成演示','zh-TW':'完成演示','en':'Finish'},
    'demo.final_title': {'zh-CN':'🐉 饱饱啦~','zh-TW':'🐉 飽飽啦~','en':'🐉 So Full~'},
    'demo.final_ok': {'zh-CN':'好的，我知道啦','zh-TW':'好的，我知道啦','en':'OK, Got It'},
    'demo.final_retry': {'zh-CN':'重新演示','zh-TW':'重新演示','en':'Restart Demo'},
    'demo.final_msg_1': {'zh-CN':'累积约 <strong>TOTAL</strong> kcal，再拿可能吃不下，别让我变成浪费的小可怜呀~ 💚','zh-TW':'累積約 <strong>TOTAL</strong> kcal，再拿可能吃不下，別讓我變成浪費的小可憐呀~ 💚','en':'About <strong>TOTAL</strong> kcal accumulated. Don\'t make me a waste monster~ 💚'},
    'demo.final_msg_2': {'zh-CN':'肚肚已经圆滚滚啦！<strong>TOTAL</strong> kcal 够啦，先吃完这些嘛~ 🥰','zh-TW':'肚肚已經圓滾滾啦！<strong>TOTAL</strong> kcal 夠啦，先吃完這些嘛~ 🥰','en':'Belly is round and full! <strong>TOTAL</strong> kcal is enough~ 🥰'},
    'demo.final_msg_3': {'zh-CN':'吃到八分饱最舒服哦~ <strong>TOTAL</strong> kcal 差不多啦！✨','zh-TW':'吃到八分飽最舒服哦~ <strong>TOTAL</strong> kcal 差不多啦！✨','en':'80% full is the sweet spot~ <strong>TOTAL</strong> kcal is perfect! ✨'},

    # 演示步骤标题/描述 (idx 0-7)
    'demo.step0_title': {'zh-CN':'第一盘：拿了一份锅包肉','zh-TW':'第一盤：拿了一份鍋包肉','en':'Plate 1: Guobaorou (Crispy Pork)'},
    'demo.step0_desc': {'zh-CN':'刚进餐厅，先来份经典东北菜','zh-TW':'剛進餐廳，先來份經典東北菜','en':'Just arrived, starting with a classic'},
    'demo.step1_title': {'zh-CN':'第二盘：蒜蓉西兰花 + 白灼虾','zh-TW':'第二盤：蒜蓉西蘭花 + 白灼蝦','en':'Plate 2: Broccoli + Shrimp'},
    'demo.step1_desc': {'zh-CN':'荤素搭配，营养均衡','zh-TW':'葷素搭配，營養均衡','en':'Balanced meat and veggie combo'},
    'demo.step2_title': {'zh-CN':'第三盘：来点红烧肉','zh-TW':'第三盤：來點紅燒肉','en':'Plate 3: Braised Pork'},
    'demo.step2_desc': {'zh-CN':'忍不住想尝尝硬菜','zh-TW':'忍不住想嚐嚐硬菜','en':'Couldn\'t resist the signature dish'},
    'demo.step3_title': {'zh-CN':'第四盘：扬州炒饭走起','zh-TW':'第四盤：揚州炒飯走起','en':'Plate 4: Yangzhou Fried Rice'},
    'demo.step3_desc': {'zh-CN':'主食不能少','zh-TW':'主食不能少','en':'Gotta have some carbs'},
    'demo.step4_title': {'zh-CN':'第五盘：番茄蛋花汤','zh-TW':'第五盤：番茄蛋花湯','en':'Plate 5: Tomato Egg Soup'},
    'demo.step4_desc': {'zh-CN':'喝碗汤暖暖胃','zh-TW':'喝碗湯暖暖胃','en':'A warm bowl of soup'},
    'demo.step5_title': {'zh-CN':'第六盘：水果拼盘收尾','zh-TW':'第六盤：水果拼盤收尾','en':'Plate 6: Fruit Platter'},
    'demo.step5_desc': {'zh-CN':'饭后水果，完美收官','zh-TW':'飯後水果，完美收官','en':'Fresh fruit to finish'},
    'demo.step6_title': {'zh-CN':'第七盘：又馋了，来份宫保鸡丁','zh-TW':'第七盤：又饞了，來份宮保雞丁','en':'Plate 7: Kung Pao Chicken'},
    'demo.step6_desc': {'zh-CN':'没忍住又去拿了一盘...','zh-TW':'沒忍住又去拿了一盤...','en':'Couldn\'t help going back for more...'},
    'demo.step7_title': {'zh-CN':'第八盘：再夹两块红烧肉解馋','zh-TW':'第八盤：再夾兩塊紅燒肉解饞','en':'Plate 8: More Braised Pork!'},
    'demo.step7_desc': {'zh-CN':'最后放纵一下！热量即将超标 ⚠️','zh-TW':'最後放縱一下！熱量即將超標 ⚠️','en':'Final indulgence! Calorie limit approaching! ⚠️'},
}

# ═══════════════════════════════════════════
# 12道菜品名翻译
# ═══════════════════════════════════════════
DISH_NAMES = {
    '锅包肉': {'zh-CN':'锅包肉','zh-TW':'鍋包肉','en':'Guobaorou (Crispy Pork)'},
    '鱼香肉丝': {'zh-CN':'鱼香肉丝','zh-TW':'魚香肉絲','en':'Yuxiang Rousi (Shredded Pork)'},
    '红烧肉': {'zh-CN':'红烧肉','zh-TW':'紅燒肉','en':'Hongshaorou (Braised Pork)'},
    '宫保鸡丁': {'zh-CN':'宫保鸡丁','zh-TW':'宮保雞丁','en':'Kung Pao Chicken'},
    '清蒸鲈鱼': {'zh-CN':'清蒸鲈鱼','zh-TW':'清蒸鱸魚','en':'Steamed Bass'},
    '白灼虾': {'zh-CN':'白灼虾','zh-TW':'白灼蝦','en':'Boiled Shrimp'},
    '蒜蓉西兰花': {'zh-CN':'蒜蓉西兰花','zh-TW':'蒜蓉西蘭花','en':'Garlic Broccoli'},
    '凉拌黄瓜': {'zh-CN':'凉拌黄瓜','zh-TW':'涼拌黃瓜','en':'Cucumber Salad'},
    '扬州炒饭': {'zh-CN':'扬州炒饭','zh-TW':'揚州炒飯','en':'Yangzhou Fried Rice'},
    '蒸红薯': {'zh-CN':'蒸红薯','zh-TW':'蒸紅薯','en':'Steamed Sweet Potato'},
    '番茄蛋花汤': {'zh-CN':'番茄蛋花汤','zh-TW':'番茄蛋花湯','en':'Tomato Egg Soup'},
    '水果拼盘': {'zh-CN':'水果拼盘','zh-TW':'水果拼盤','en':'Fruit Platter'},
}

# 菜品分类翻译
CATEGORY_NAMES = {
    '肉类': {'zh-CN':'肉类','zh-TW':'肉類','en':'Meat'},
    '海鲜': {'zh-CN':'海鲜','zh-TW':'海鮮','en':'Seafood'},
    '蔬菜': {'zh-CN':'蔬菜','zh-TW':'蔬菜','en':'Vegetable'},
    '主食': {'zh-CN':'主食','zh-TW':'主食','en':'Staple'},
    '汤品': {'zh-CN':'汤品','zh-TW':'湯品','en':'Soup'},
    '甜点': {'zh-CN':'甜点','zh-TW':'甜點','en':'Dessert'},
    '水果': {'zh-CN':'水果','zh-TW':'水果','en':'Fruit'},
    '饮品': {'zh-CN':'饮品','zh-TW':'飲品','en':'Beverage'},
    '蔬菜/海鲜': {'zh-CN':'蔬菜/海鲜','zh-TW':'蔬菜/海鮮','en':'Veg/Seafood'},
}

# 烹饪方式翻译
COOKING_NAMES = {
    '炒': {'zh-CN':'炒','zh-TW':'炒','en':'Stir-fried'},
    '蒸': {'zh-CN':'蒸','zh-TW':'蒸','en':'Steamed'},
    '煮': {'zh-CN':'煮','zh-TW':'煮','en':'Boiled'},
    '炸': {'zh-CN':'炸','zh-TW':'炸','en':'Deep-fried'},
    '烤': {'zh-CN':'烤','zh-TW':'烤','en':'Roasted'},
    '炖': {'zh-CN':'炖','zh-TW':'燉','en':'Braised'},
    '凉拌': {'zh-CN':'凉拌','zh-TW':'涼拌','en':'Cold-tossed'},
    '生食': {'zh-CN':'生食','zh-TW':'生食','en':'Raw'},
    '清炒': {'zh-CN':'清炒','zh-TW':'清炒','en':'Sautéed'},
}

# 13种饮食需求翻译
DIETARY_TYPES = {
    "fat_loss": {
        "zh-CN": {"name":"减脂瘦身","desc":"低热量高蛋白，严格控碳控脂"},
        "zh-TW": {"name":"減脂瘦身","desc":"低熱量高蛋白，嚴格控碳控脂"},
        "en": {"name":"Fat Loss","desc":"Low cal, high protein, strict carb/fat control"}
    },
    "muscle_gain": {
        "zh-CN": {"name":"增肌塑形","desc":"高蛋白中碳水，为肌肉合成供能"},
        "zh-TW": {"name":"增肌塑形","desc":"高蛋白中碳水，為肌肉合成供能"},
        "en": {"name":"Muscle Gain","desc":"High protein, moderate carbs for muscle building"}
    },
    "low_carb_keto": {
        "zh-CN": {"name":"低碳水/生酮","desc":"极低碳水，酮体供能模式"},
        "zh-TW": {"name":"低碳水/生酮","desc":"極低碳水，酮體供能模式"},
        "en": {"name":"Low Carb/Keto","desc":"Ultra-low carb, ketosis mode"}
    },
    "vegan": {
        "zh-CN": {"name":"纯素食","desc":"无任何动物来源食材"},
        "zh-TW": {"name":"純素食","desc":"無任何動物來源食材"},
        "en": {"name":"Vegan","desc":"No animal-derived ingredients"}
    },
    "diabetic_friendly": {
        "zh-CN": {"name":"糖尿病友好","desc":"低GI食物，控制血糖"},
        "zh-TW": {"name":"糖尿病友好","desc":"低GI食物，控制血糖"},
        "en": {"name":"Diabetic Friendly","desc":"Low GI foods, blood sugar control"}
    },
    "senior_friendly": {
        "zh-CN": {"name":"银发族易咀嚼","desc":"软烂易消化，低盐低脂"},
        "zh-TW": {"name":"銀髮族易咀嚼","desc":"軟爛易消化，低鹽低脂"},
        "en": {"name":"Senior Friendly","desc":"Soft, easy to digest, low salt/fat"}
    },
    "kids_meal": {
        "zh-CN": {"name":"儿童营养餐","desc":"营养均衡，色彩丰富"},
        "zh-TW": {"name":"兒童營養餐","desc":"營養均衡，色彩豐富"},
        "en": {"name":"Kids Meal","desc":"Balanced nutrition, colorful"}
    },
    "high_protein": {
        "zh-CN": {"name":"高蛋白","desc":"蛋白质>35g，运动人群"},
        "zh-TW": {"name":"高蛋白","desc":"蛋白質>35g，運動人群"},
        "en": {"name":"High Protein","desc":"Protein >35g, for athletes"}
    },
    "mediterranean": {
        "zh-CN": {"name":"地中海饮食","desc":"多蔬果鱼类，健康脂肪"},
        "zh-TW": {"name":"地中海飲食","desc":"多蔬果魚類，健康脂肪"},
        "en": {"name":"Mediterranean","desc":"Rich in veggies, fish, healthy fats"}
    },
    "high_fiber": {
        "zh-CN": {"name":"高纤维","desc":"膳食纤维>12g，肠道健康"},
        "zh-TW": {"name":"高纖維","desc":"膳食纖維>12g，腸道健康"},
        "en": {"name":"High Fiber","desc":"Fiber >12g, gut health"}
    },
    "quick_work_lunch": {
        "zh-CN": {"name":"快捷工作餐","desc":"方便饱腹，上班族首选"},
        "zh-TW": {"name":"快捷工作餐","desc":"方便飽腹，上班族首選"},
        "en": {"name":"Quick Work Lunch","desc":"Convenient & filling, office-friendly"}
    },
    "light_salad": {
        "zh-CN": {"name":"轻食沙拉系","desc":"清爽低负担"},
        "zh-TW": {"name":"輕食沙拉系","desc":"清爽低負擔"},
        "en": {"name":"Light & Fresh","desc":"Light and refreshing"}
    },
    "comfort_food": {
        "zh-CN": {"name":"暖胃家常味","desc":"热汤热菜，中式家常"},
        "zh-TW": {"name":"暖胃家常味","desc":"熱湯熱菜，中式家常"},
        "en": {"name":"Comfort Food","desc":"Hot soup & dishes, homestyle"}
    },
}

def dish_name(cn_name, lang=None):
    """翻译菜品名"""
    if lang is None: lang = get_lang()
    entry = DISH_NAMES.get(cn_name, {})
    return entry.get(lang, cn_name)

def cat_name(cn_cat, lang=None):
    """翻译分类名"""
    if lang is None: lang = get_lang()
    entry = CATEGORY_NAMES.get(cn_cat, {})
    return entry.get(lang, cn_cat)

def cook_name(cn_cook, lang=None):
    """翻译烹饪方式"""
    if lang is None: lang = get_lang()
    entry = COOKING_NAMES.get(cn_cook, {})
    return entry.get(lang, cn_cook)

def dietary_name(dtype_id, lang=None):
    """翻译饮食需求名"""
    if lang is None: lang = get_lang()
    entry = DIETARY_TYPES.get(dtype_id, {})
    return entry.get(lang, entry.get('zh-CN', {'name':dtype_id,'desc':''}))

def get_text(key, lang=None):
    """获取翻译文本"""
    if lang is None:
        lang = get_lang()
    entry = T.get(key, {})
    return entry.get(lang, entry.get('zh-CN', key))
