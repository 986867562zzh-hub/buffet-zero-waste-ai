# How It Works — Script for Zhang Zhenghao (5 minutes / 6 slides)

---

## Slide 6: AI Architecture Overview (~50 seconds)

> 🖼️ PPT Visual: A flowchart from left to right
> User Photo → AI Engine Router → DeepSeek Vision → Perceptual Hash → PIL Color Analysis
> Below: Output (Dish Name + Calories + Confidence Level)

**Script**:

"Now let me explain the most important part — how the AI actually works.

The process is quite simple. A user takes a photo of their plate with their phone. The image is sent to our server, and it goes through what we call an **AI Engine Router**.

It tries different AI models in order of priority:
- First, it calls the **DeepSeek Vision API**. This is our main AI model. It is very affordable and understands Chinese food really well.
- If DeepSeek is not available, it falls back to our **perceptual hash matcher**. This is an algorithm we built ourselves. It compares image fingerprints with our dish library.
- Finally, if everything else fails, we use basic **PIL color analysis** — it detects food by color, like red-brown areas might be meat, green areas might be vegetables.

No matter what happens, the system always returns three things: **what dish it is, how many calories, and how confident the AI is**.

The key benefit of this multi-layer design is that the system works in any situation — with or without an API key, with or without internet."

---

## Slide 7: AI Engine Details (~50 seconds)

> 🖼️ PPT Visual: Three cards side by side
> DeepSeek Vision | Perceptual Hash | PIL Fallback
> Each card shows: technology, strength, weakness

**Script**:

"Let me break down each layer.

**DeepSeek Vision** is at the top. We send the photo as a base64 encoded string, along with a carefully designed prompt. The API returns structured JSON — dish name, category, and estimated calories. The advantage is very high accuracy, especially for Chinese dishes. The downside is it costs a little bit of money per API call.

**The middle layer is perceptual hash matching.** We built this algorithm ourselves using only the PIL library — no external AI needed. Here is how it works: we resize the image to a tiny 8-by-8 pixel grayscale version, and compare it against all 12 reference dishes in our library. We also combine it with color histogram and edge texture features — three dimensions weighted together. The great thing is it costs zero API fees and runs completely offline.

**The bottom layer is PIL color analysis.** This is traditional image processing. If the photo has reddish-brown areas, it might be meat. Green areas might be vegetables. It is not very precise, but at least it never makes up dish names out of thin air.

These three layers together make sure the system always gives honest, evidence-based results."

---

## Slide 8: Two Core Functions (~50 seconds)

> 🖼️ PPT Visual: Comparison table
> Calorie Tracker (Before Meal) | Waste Scorer (After Meal)
> Each column: Screenshot, input/output, logic

**Script**:

"Our system has two usage modes, and you switch between them with a simple tab.

**The first one is Calorie Tracking** — used before eating. When you go to the buffet and grab a plate of food, you take a photo. The AI identifies what dishes are on the plate and estimates the calories. The key feature is **accumulation** — every time you go back to the buffet and take another photo, the calories add up. When the total reaches your threshold — we set the default at 1800 kilocalories — a cute cartoon character pops up and gently reminds you: 'Your tummy is full now! Maybe finish what you have first?'

Why 1800? Because buffet dining is about enjoyment and indulgence. If we set it too low, customers lose interest. The goal is a friendly reminder, not a strict diet rule.

**The second mode is Waste Scoring** — used after eating. You take a photo of your empty plate, the AI analyzes how much food is left, and gives you a score from 0 to 100. If you score above 95 — a 'Clean Plate Hero' — you get a 15% discount. This creates an economic incentive to reduce food waste.

One function prevents waste before it happens, the other manages it afterwards. Together they form a complete zero-waste solution."

---

## Slide 9: Prompt Evidence & API Configuration (~50 seconds)

> 🖼️ PPT Visual:
> Left: Full DeepSeek API prompt (code block style)
> Right: API parameters + Sample JSON response
> Bottom: Input photo thumbnail → Output JSON screenshot

**Script**:

"This slide is the direct evidence of our AI work — as required by the assignment.

On the left is the **complete prompt** we send to DeepSeek. I want to highlight three important design choices we made:

First, we set the role: 'You are a professional food recognition assistant.' This tells the AI to act as an expert.

Second, we require pure JSON output — no markdown. This is important because our Python code needs to parse the response automatically. If the AI wraps it in markdown code blocks, our parser would break.

Third, we include the instruction: 'Only list foods you actually see. Be honest.' This prevents the AI from guessing or making up dishes that are not in the photo.

On the right are our **API configuration parameters**: temperature is set to 0.1, which means we want consistent and predictable results — not creative ones. Max tokens is 2000, which is enough for detailed food analysis.

At the bottom is a real input-output example. Left side: a photo of Guo Bao Rou, which is a classic Northeastern Chinese dish. Right side: the JSON response from DeepSeek, correctly identifying the dish name, category as meat, and estimated calories at 310 kilocalories."

---

## Slide 10: Code Evidence & Examples (~50 seconds)

> 🖼️ PPT Visual:
> Top left: DeepSeekVision class code (highlight key lines)
> Top right: Perceptual hash algorithm core code
> Bottom: 3 input-output pairs (photo → result)

**Script**:

"Here is some actual code from our project.

On the top left is our **DeepSeekVision class**. You can see it uses the OpenAI-compatible interface — the base URL points to api.deepseek.com. This is why we can use the standard `openai` Python library to call DeepSeek's model. It makes the integration very clean — just a few lines of code.

On the top right is the **perceptual hash algorithm**. This is only about fifteen lines of code. It resizes the image to 8 by 8 pixels, converts it to grayscale, compares each pixel to the average, and generates a 64-bit binary fingerprint. Two images of the same dish will have very similar fingerprints, and we measure this using Hamming distance. The smaller the distance, the more likely it is the same dish.

At the bottom are three real input-output pairs. Guo Bao Rou photo in → AI says Guo Bao Rou, 310 kcal. Hong Shao Rou photo in → AI says Hong Shao Rou, 380 kcal. If the photo is too blurry or unclear, the system returns a low confidence warning and asks the user to try again.

All of this code is available on our GitHub repository — the link is on the last slide."

---

## Slide 11: Iteration Log — v1.0 to v2.5 (~50 seconds)

> 🖼️ PPT Visual: Timeline or roadmap style
> v1.0 (Jun 10): Random generation
> v2.0 (Jun 11): Fixed dish library + closed-set matching
> v2.1-v2.3 (Jun 11-15): Calorie tracking + Perceptual hash + Base64 storage
> v2.4-v2.5 (Jun 15): DeepSeek API + Demo mode + P1-P4 improvements

**Script**:

"Finally, I want to show you our iteration journey. This proves we actually tested, found problems, and improved the system.

**Version 1.0** was built on the night of June 10th. At that time, the AI recognition was using randomly generated results. During user testing, someone pointed out: 'The system is identifying dishes that are not even in the photo. Isn't this fraud?' That feedback hit hard, and we knew we had to change.

So in **Version 2.0**, we completely redesigned the architecture. We created a fixed library of 12 dishes. Each dish has reference photos and detailed visual descriptions. The AI now only matches against these 12 known dishes — it will never invent dishes outside the library.

From v2.1 to v2.3, we added calorie accumulation tracking, replaced color-only matching with perceptual hash, and solved a data persistence problem by storing reference images as base64 in our JSON file, so they never get lost when the server redeploys.

In **v2.4 and v2.5**, we integrated the DeepSeek API for much higher accuracy, built a one-click demo mode for classroom presentations, and fixed several critical issues in the meal recommendation engine — for example, vegetarian users will never get meat recommendations, and allergy information is now actually checked against dish names.

Six versions in six days. We learned a lot from each iteration. This is the real development process."

---

## 🎯 Presentation Tips

1. **Pace yourself**: About 50 seconds per slide. 6 slides × 50s = exactly 5 minutes
2. **Eye contact**: Look at your teacher and classmates, not just the screen
3. **Point with your hand**: When showing code or architecture, physically point to what you're talking about
4. **Don't read word-for-word**: Use the script as a guide, but speak naturally
5. **Transition smoothly**: End each slide with a hook to the next one
6. **Handover clearly**: "That's all for How It Works. Now [teammate C] will give you a live demo!"

## 📸 Screenshots Needed

| Slide | What to Screenshot |
|:--:|------|
| 6 | Create a flowchart in PPT (SmartArt → Process) |
| 7 | Use the AI engine code as background or create 3 cards |
| 8 | Screenshot the calorie tracking page + waste scoring page from the website |
| 9 | Copy-paste the DeepSeek prompt from `app.py` (search for "你是一个专业的美食识别助手") |
| 10 | Screenshot VS Code with `DeepSeekVision` class and `_compute_ahash` function |
| 11 | Create a timeline in PPT (SmartArt → Process → Basic Timeline) |
