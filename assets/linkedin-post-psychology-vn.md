# LinkedIn Post — BDD Test Case Generator (Psychology-Driven, Vietnamese)

---

## Final (Recommended)

**Bạn có dám tin một con AI viết test case không?**

Thực ra câu hỏi đúng phải là: *"Làm sao để KIỂM TRA chất lượng test case do AI sinh ra?"*

Hầu hết tool AI generate test case hiện nay chỉ làm được 1 việc: Prompt → Output → Tin hoặc không tin. Không ai dám cam kết output đó đúng.

Mình không chấp nhận điều đó. Thế là build cái này 👇

**BDD-First Test Case Generator** — tool mở, chạy local, không phải SaaS paywall.

Khác biệt nằm ở **Quality Report 7 metrics** đính kèm MỖI lần generate:

```
ac coverage              100%   → không sót requirement nào
category balance         OK     → đủ positive/negative/edge/boundary
faithfulness             80%    → grounding trích dẫn verbatim từ BA doc gốc
inferred ratio           17%    → phát hiện requirement "ngầm hiểu"
semantic consistency     73%    → test case khớp ngữ nghĩa với requirement
gherkin validity         100%   → parser Gherkin cứng, zero-token
outline efficiency       25%    → gợi ý merge vào Scenario Outline
proxy mutation           60%    → "nếu bug này xảy ra, test có bắt được không?"
```

Pipeline: **Gemini extract** → tag explicit/inferred → **Gemini generate** Gherkin → **Gate cứng** (parse + dedup) → **Claude cross-family verify** → **Loop retry** max 3 lần.

Kết quả test chạy BA doc iBank 60 trang: **score 87.2/100**, 20+ test case, 0 lỗi Gherkin, 0 warning duplication.

Tất cả chạy local trên máy bạn. Không gửi data đi đâu. Gemini + OpenRouter API key là đủ.

Repo: https://github.com/zzbi007zz/tcAIGen

Nếu team bạn đang có BA docs dày cần viết test case mà vẫn đang làm tay — thử đi. Không mất gì ngoài 5 phút clone repo.

#softwareTesting #qa #bdd #gherkin #ai #vietnameseTech #opensource

---

## Psychology Model Mapping

| Element | Model Applied |
|---------|---------------|
| Opening question | First Principles — "dám tin" forces re-examining AI output trust |
| "Hầu hết tool" contrast | Anchoring + Loss Aversion — readers see most tools lack verification, value our differentiator |
| "Mình không chấp nhận điều đó" | Pratfall Effect + Authenticity — founder narrative, relatable frustration |
| 7-metric table | Framing Effect — data over claims, concrete over abstract |
| "chạy local" + "không gửi data" | Authority Bias + Trust — addresses security anxiety of Vietnamese enterprises |
| "87.2/100, 20+ TC, 0 lỗi" | Social Proof (specific numbers beat vague claims) |
| "Không mất gì ngoài 5 phút" | Activation Energy — reducing friction to trivially easy |
| Vietnamese language | Unity Principle — "người Việt viết cho người Việt" builds tribe identity |
| Pipeline summary | Peak-End Rule — technical peak in middle, easy CTA at end |
