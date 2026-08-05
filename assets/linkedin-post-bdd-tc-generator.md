# BDD-First Test Case Generator — LinkedIn Post (Vietnamese)

---

## Bản nháp 1: Ngắn gọn, va chạm

**Viết test case manual tốn hàng giờ. AI generate thì sợ hallucination. Có cách nào vừa nhanh vừa tin được không?**

Mình vừa build xong một tool mở: **BDD-First Test Case Generator** — không chỉ generate Gherkin test case từ BA docs, mà còn đính kèm **quality report chứng minh chất lượng đầu ra.**

📌 **Hoạt động thế nào?**
- Upload tài liệu BA (.txt/.md/.docx/.pdf, tối đa 50MB) + optional screenshots
- Pipeline tự động: extract requirements → tag `explicit`/`inferred` → detect gaps giữa design & requirement → generate Gherkin test cases với `Scenario Outline` + Examples table
- **Gate cứng**: 100% Gherkin phải parse được (zero-token, không tốn API cost)
- **Cross-family verify**: Gemini generate, Claude/GPT verify — không dùng cùng một model family
- Loop retry tối đa 3 lần, budget $0.50

📊 **6 metrics quality report:**
- AC Coverage (target: >85%)
- Category Balance (positive/negative/edge/boundary)
- Faithfulness (token overlap groundtruth — chống hallucination)
- Inferred Ratio (tracking requirement nào được suy luận thay vì nêu rõ)
- Gherkin Validity (hard gate)
- Duplication check (>92% similarity)

⚡ **Tích hợp đầy đủ:**
- CLI: `python -m apps.cli run doc.txt --verbose`
- REST API (FastAPI): 8 endpoints
- Web UI (Next.js): drag-drop upload, progress bar, gap report, quality dashboard, export .feature zip + .xlsx

🛠 **Tech stack:** FastAPI + Pydantic v2 + Gemini 2.5 Flash + OpenRouter (Claude/GPT) + Next.js 14
🧪 **132 tests, coverage >80%, CI pipeline sẵn sàng**

Repo: https://github.com/zzbi007zz/tcAIGen

Định vị đơn giản: *"The test case generator that proves its output quality."*

Ai đang làm QA/BA/PO mà muốn tự động hóa khâu viết test case thì thử nhé. Góp ý, issue, PR đều welcome.

#testing #qa #bdd #gherkin #ai #automation #vietnameseTech

---

## Bản nháp 2: Story-driven, dài hơn

**8 tiếng viết test case cho 1 module. 50 test case. Rồi khách hàng đổi requirement. Viết lại từ đầu.**

Bài toán quen thuộc với anh chị em QA phải không?

Mình từng ngồi BA docs 60 trang, extract requirement bằng tay, map từng feature vào màn hình, viết Gherkin, check dup, check coverage... xong 2 ngày. Rồi PO đổi 3 cái acceptance criteria. Lại 1 buổi sửa.

Thế là mình build **BDD-First Test Case Generator.**

Ý tưởng đơn giản: *"Nếu AI generate test case thì phải có bằng chứng chứng minh nó đúng."*

**Pipeline 6 bước:**
1. **Ingest** — đọc BA doc (.txt/.docx/.pdf) kể cả tiếng Việt
2. **Extract** — Gemini phân tích, tag từng requirement là `explicit` (nêu rõ) hay `inferred` (suy luận)
3. **Vision + Merge** — nếu có screenshots, detect UI elements và map vào feature → báo cáo gap (requirement có nhưng design thiếu, hoặc ngược lại)
4. **Generate** — sinh Gherkin test case, dùng `Scenario Outline` cho boundary test, bắt buộc có `grounding_source` trên từng case
5. **Gate + Verify** — Parser Gherkin cứng (zero-token, miễn phí), sau đó Claude cross-family verify kết quả của Gemini
6. **Loop** — retry tối đa 3 lần với feedback, budget $0.50 tổng

**Kết quả không phải là 1 list test case — mà là 1 quality report kèm theo:**
- Score /100
- AC Coverage: requirement nào thiếu test case?
- Category Balance: tỷ lệ positive/negative/edge/boundary
- Faithfulness: "câu quote trong test case có thực sự có trong tài liệu gốc không?"
- Inferred Ratio: bao nhiêu % test case từ requirement suy luận (cảnh báo rủi ro hallucination)
- Duplication: test case nào trùng >92%?

**So điểm:** Chạy thử với BA doc "iBank early closure & calculation" cho ra **score 100/100**, 20 test case, zero warning, faithfulness 1.0, Gherkin validity 100%.

Tool mở hoàn toàn (MIT), chạy local với Gemini API key. Có CLI, REST API, và Web UI (Next.js) kéo thả.

Repo: https://github.com/zzbi007zz/tcAIGen

Star, fork, góp ý thoải mái nhé. Nếu team bạn đang làm ngân hàng, fintech, insurtech mà có BA docs dày cộp cần viết test case — thử đi, tiết kiệm kha khá thời gian đấy.

#qualityAssurance #softwareTesting #bdd #gherkin #testAutomation #aiTesting #vietnameseQA

---

## Bản nháp 3: Technical, cho dân engineering

Build một con AI test case generator thì dễ. **Build một con chứng minh được chất lượng đầu ra mới khó.**

Đây là tcAssistant — BDD-First Test Case Generator mình vừa open source:

🔗 github.com/zzbi007zz/tcAIGen

**Khác biệt so với các tool AI generate test case thông thường:**

❌ Hầu hết tool: Prompt → Output → Tin tưởng mù quáng
✅ Tool này: Prompt → **Gate cứng** → **Cross-family Verify** → **Loop retry** → **Quality Report 6 metrics** → Output

Pipeline kỹ thuật:
```
BA Doc → ingest → extract (Gemini, tag explicit/inferred)
  ├→ vision (Gemini Vision, visible elements only)
  ├→ merge (3 gap types detection)
  └→ generate → gate (Gherkin parse + dedup, FREE)
       └→ verify (OpenRouter Claude, cross-family)
            └→ loop (max 3 iter, $0.50 budget)
                 ├→ .feature files export
                 └→ QualityReport (score + 6 metrics + warnings)
```

Stack: FastAPI + Pydantic v2 | Next.js 14 + React 18 | Gemini 2.5 Flash | OpenRouter | pytest 132 tests

Anh em QA/Dev muốn xem cách pipeline verify-then-loop hoạt động hoặc muốn tích hợp vào CI pipeline của team — vào repo đọc docs nhé. MIT license, mở hoàn toàn.

#opensource #ai #softwareTesting #fastapi #nextjs #gherkin #bdd #testing
