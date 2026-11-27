# 接手說明：Opus 5.5 vs Qwen 3.8 Flash 機房 3D pipeline 評測

給接手的 agent（Claude Code、Codex 或其他）。讀完這一份就能知道：專案在做什麼、做到哪裡、東西放在哪、哪些規則不能破、還有什麼沒做。

狀態日期：2026-11-27。

**操作 benchmark 的逐步指示**在 `AGENTS.md`，這份不重複。這份補上專案背景、完整成績、費用資料、產出物位置和待辦事項。

---

## 1. 一句話結論

Qwen 3.8 Flash（OpenRouter 雲端託管版，推理強度 high）在 10 關中有 2 關不及格：
- S1P 照片推回佈局：52.6 分
- D1 竣工比對：60 分

Opus 5.5 這兩關是 96.1 和 100。加權總分 Opus 99.1、Qwen 62.7（及格 80）。

報告的立場是「地端 Qwen3.8-Flash-Next 不能用，應使用 Opus」。依據是：
- 雲端版已經不及格。
- 地端原生上下文 262,144，而 S1P 用到 274,507。
- 地端的精度和速度都不會比雲端好。

**這是推論，地端版還沒實測**。實測是本 repo 存在的目的。

## 2. 人與溝通

- 使用者讀繁體中文，回報一律用繁體中文。
- 使用者要的是有立場、易懂的結論，並且要標出缺失和程式問題。
- 不要擅自加內容或改設計；想加東西先問。

## 3. 不能破的規則

1. **答案卷絕不進 repo，也不能在受測模型執行時存在於磁碟上。**
   - 用 `scripts/make_keys.sh` 從種子重建到 repo 外（預設 `~/qwenpoc-keys`）。
   - 雜湊驗證檔是 `scripts/key_hashes.json`。
   - `bench exec` 執行的 Python 沒有沙箱。
2. **不要改受測條件**：`harness/prompts/`、`qwen_runner.py` 的工具規則、`bench/` 的上限、`score/`、`gen/`、`oracle/`、`inputs/`。壞了就停下來回報。
3. **不要花錢在 Modal**。使用者明確說過「先不要花錢在 modal」。
4. **第二評審用 Gemini 時**，只能用使用者自己的 Gemini 金鑰（環境變數 `gemini_key`）直連 API，不走 OpenRouter，3.8 Flash 就夠。使用者嫌過 Gemini 燒太多 token，非必要不要跑。
5. **OpenRouter 金鑰**在環境變數 `or_key`，餘額約 $2.8。每次跑之前先告知預計花費。
6. **不要提交** `runs/`、金鑰、端點憑證，也不要把使用者的 email 或個資送到外部服務。
7. **Opus 當受測者時**，必須是沒看過答案的全新 session。執行期間 `reference/` 和答案卷不能在機器上。做法見 `AGENTS.md` 最後一節和 `scripts/opus_prompt.py`。
8. **git 推送範圍**：
   - `clarencechien/qwenpoc`：使用者要求推到 `main`。
   - `clarencechien/opus55poc`：只推 `claude/eloquent-lovelace-4vrek4`。
   - 不開 PR，除非使用者要求。
   - commit 訊息結尾照該 session 系統提示給的 attribution 行。

## 4. 東西在哪裡

| 位置 | 內容 |
|---|---|
| `clarencechien/qwenpoc`（本 repo，`main`） | 可重現的評測套件、參考執行紀錄、報告與簡報。給地端團隊或 agent 用 |
| `clarencechien/opus55poc`，分支 `claude/eloquent-lovelace-4vrek4`，目錄 `datacenter/` | 原始工作區：完整執行目錄（含 `.blend`、渲染圖、檢視圖）、報告產生器 `report/build_full.py`、`report/build_phase1.py`、Gemini 評審 `judge/`、計畫書 `PLAN.md` |
| `report/full_report.html` | 完整報告（第一＋第二階段），單一檔案、圖片內嵌。原始產生器在 opus55poc 的 `datacenter/report/build_full.py`（需要完整的 runs，本 repo 沒有） |
| `report/slides.pdf`、`report/slides.html` | 17 頁簡報。原始檔在 `report/slides/`，用 `python3 report/build_slides.py` 重建（PDF 需要 Node.js 和 playwright） |
| `report/phase1.html` | 第一階段報告（舊版，已被完整報告取代） |
| claude.ai Artifacts（使用者私人） | 完整報告 `https://claude.ai/artifact/6u5KKzPH9atAQJ7ks4cLrf`；簡報（Slides 類型）`https://claude.ai/artifact/SLQE28476GJziUTeg4DN79`。只有使用者能開，接手的 agent 未必有權限；以 repo 裡的檔案為準 |
| `reference/` | 20 筆參考執行紀錄：分數、`run_summary.json`、`transcript.jsonl`、`bench_log.jsonl`、受測模型寫的程式。只保留計分需要的 `.blend` |
| `docs/REPRODUCE.md` | 給人看的中文重現手冊 |

### 簡報的線上版與 repo 版

- Slides artifact 的原始檔就是 `report/slides/` 的內容。
- 線上版圖片用 `/_blob/<id>`，對照表在 `report/slides/images/blob_map.json`。
- 要改簡報時，改 `report/slides/` 再重建。若也要更新線上版，需要使用者那邊的 Artifact 工具。
- 設計規則：
  - 全部淺色主題。
  - 每頁底部一條深色「結論帶」（`.take`），關鍵字用 `.k`。
  - Opus 藍 `#2B50C8`、Qwen 橘 `#C2601A`，用標籤 `.chip`。
  - 失敗用紅 `#B3302A`。
- 這組配色已用 dataviz 驗證工具檢查過色盲可辨識。

## 5. 10 關成績（參考執行）

| 代號 | 關卡 | Opus | Qwen | Opus 用時 | Qwen 用時 | Qwen 最長對話 token |
|---|---|---|---|---|---|---|
| s1-easy | 平面圖 → 3D 機房（16 櫃） | 97.1 | 97.1 | 66 秒 | 561 秒 | 48,564 |
| s1-hard | 平面圖 → 3D 機房（58 櫃，L 形） | 100 | 100 | 95 秒 | 1,397 秒 | 125,525 |
| s2 | 參考照片 → 機櫃模型（只量幾何，滿分 40） | 40 | 40 | 543 秒 | 1,002 秒 | 74,815 |
| s3-easy | 機櫃擺進機房 | 100 | 100 | 102 秒 | 733 秒 | 64,342 |
| s3-hard | 機櫃擺進機房（58 櫃） | 100 | 100 | 135 秒 | 478 秒 | 52,408 |
| s1p | 5 張現場照片 → 推回佈局 | 96.14 | **52.64** | 954 秒 | 3,452 秒 | **274,507** |
| d1 | 竣工比對：設計圖 vs 7 張現場照片 | 100 | **60.0** | 567 秒 | 3,685 秒 | **240,804** |
| d2 | 空機房佈局設計（9 條規則，基準 250 櫃） | 97.2 | 86.8 | 699 秒 | 2,589 秒 | 97,797 |
| d3 | 6 條冷卻水管 3D 繞行 | 100 | 99.49 | 468 秒 | 943 秒 | 103,804 |
| d5 | 依三視圖復刻 CDU | 99.97 | 99.05 | 154 秒 | 2,276 秒 | **233,251** |

**判定規則**：每關 ≥ 80%，而且加權總分 ≥ 80。
- 正確性 70 分，權重依序 3/5/5/2/5/15/15/10/5/5。
- 效率 30 分 = 各關「最快用時 ÷ 自己用時」的平均。
- 結果：Opus 99.1 通過；Qwen 62.7 不通過。
- 換 6 種配分方式，Qwen 都不通過。
- 計算程式在 `scripts/score_all.py`，報告版在 opus55poc 的 `build_full.py`。

## 6. 費用（新整理，尚未放進報告和簡報）

### Qwen：OpenRouter 實際扣款

10 關合計 **$1.53**，讀入 5,386 萬 token、輸出 93 萬 token。

| 關卡 | s1-easy | s1-hard | s2 | s3-easy | s3-hard | s1p | d1 | d2 | d3 | d5 |
|---|---|---|---|---|---|---|---|---|---|---|
| 美元 | 0.040 | 0.137 | 0.084 | 0.060 | 0.047 | 0.429 | 0.259 | 0.091 | 0.108 | 0.269 |

來源是各執行目錄的 `run_summary.json`（`cost_usd`、`tokens`）。重算：

```bash
python3 -c "import json;R=['easy/s1-r2-high','hard/s1-r1-high','easy/s2-r2-high','easy/s3-r2-high','hard/s3-r1-high','photo-hard/s1p-r1-high','phase2/d1-r1-high','phase2/d2-r1-high','phase2/d3-r2-high','phase2/d5-r1-high'];print(sum(json.load(open(f'reference/qwen3.8-flash/{r}/run_summary.json'))['cost_usd'] for r in R))"
```

### Opus：用 API 牌價換算（實際是 Claude 方案額度，沒有帳單）

10 關合計約 **$18.0**，讀入 2,619 萬 token、輸出 33 萬 token、共 212 次請求。

- **牌價**（claude-opus-5-5，每百萬 token）：輸入 $4、輸出 $20、快取寫入（5 分鐘）$5、快取讀取 $0.20。
- **資料來源**：主控 session 的子代理對話紀錄 `~/.claude/projects/-home-user-opus55poc/8df66769-71ef-578c-ad75-d39b6e4f4633/subagents/agent-*.jsonl`。
  - 只在原 session 的容器裡有，不在任何 repo。
  - 計算方式：取 `message.model == "claude-opus-5-5"` 的 assistant 訊息，依 `message.id` 去重後加總 `usage`。

| 關卡 | 請求 | 快取寫入 | 快取讀取 | 輸入 | 輸出 | 美元 | 最長一次請求（含 Claude Code 開銷） |
|---|---|---|---|---|---|---|---|
| s1-easy | 6 | 77,774 | 365,888 | 12 | 4,945 | 0.56 | 77,776 |
| s1-hard | 8 | 82,691 | 541,287 | 16 | 9,382 | 0.71 | 82,693 |
| s2 | 29 | 227,900 | 3,370,704 | 60 | 55,178 | 2.92 | 150,025 |
| s3-easy | 13 | 91,430 | 989,903 | 26 | 9,253 | 0.84 | 91,432 |
| s3-hard | 13 | 103,156 | 1,129,163 | 26 | 11,643 | 0.97 | 103,158 |
| s1p | 58 | 213,011 | 8,727,077 | 116 | 85,779 | 4.53 | 213,013 |
| d1 | 47 | 181,621 | 6,152,953 | 96 | 44,174 | 3.02 | 181,623 |
| d2 | 15 | 107,721 | 1,825,089 | 30 | 66,804 | 2.24 | 159,952 |
| d3 | 9 | 111,843 | 725,063 | 18 | 33,373 | 1.37 | 111,845 |
| d5 | 14 | 90,759 | 1,074,312 | 28 | 9,713 | 0.86 | 90,761 |

**解讀時注意：**
- **Claude Code 本身的開銷。** 每個 Opus 子代理的第一次請求就有約 6.4 萬 token，是系統說明和工具定義，之後每次請求都重讀。這約佔 $6（每關首次快取寫入約 $0.32，加上 212 次 × 6.4 萬 × $0.20/M 的讀取）。
  - 若用和 Qwen 一樣精簡的 API 程式跑 Opus，估計約 **$12**，即每關 $1.2。這是推算，沒有實測。
- **報告裡 Opus 的「最長對話」也含這 6.4 萬。** 例如 S1P 的 213K，扣掉後實際任務內容約 15 萬，仍遠低於 Qwen 的 27.5 萬。
- **輸出 token 已包含推理。** Qwen 的 `tokens.reasoning` 是輸出的子集。
- **比較**：Opus 約貴 12 倍（精簡程式約 8 倍），但 Qwen 有 2 關不及格，而且每關慢 1.8–15 倍。

## 7. 已知狀況與揭露事項（報告第 8 節都有寫）

- 每關每個模型只跑 1 次。
- Opus 的工具限制靠指令，事後逐筆稽核，第二階段沒有讀取執行目錄以外的檔案。Qwen 的限制由程式強制。
- Opus 跑 S1P 時，Qwen 的答案曾誤留在磁碟約 2 分鐘。兩邊錯的地方完全不同，沒有被使用的跡象。
- Qwen 的 D3 第一次執行因為單次回覆超過當時 32,000 輸出上限被截斷（`reference/qwen3.8-flash/phase2/d3-r1-high`，0 分）。runner 已改為上限 64,000、截斷時要模型接著寫，報告採用重跑的 `d3-r2-high`。
- **S2 自動分數只量幾何，不評外觀。**
  - 外觀缺失是人工看渲染圖和 `score/audit_s2.py` 找的。
  - Gemini 4 Argon 的外觀分數分不出高下（93–94）。
  - 外觀應做人工盲測，還沒做。
- **程式碼審查**（Gemini 4 Carbon）只做了 S3 hard 一關。其餘因 Gemini 費用先停。
- **D2 的基準 250 櫃**是 `oracle/d2_solver.py` 找到的最好結果（重算約 22 分鐘），不保證是理論最佳。
- **出題者與計分程式作者也是 Claude**（主控 session）。計分全用程式對答案卷。

## 8. 待辦（依優先順序）

1. **地端實測**：照 `AGENTS.md` 把 10 關接到地端 Qwen3.8-Flash-Next。
   - 原生 262K 和 YaRN 1M 兩種設定各跑一次（輸出到不同目錄）。
   - 記錄精度、GPU、框架版本、上下文設定。
   - 這是驗證報告推論的唯一方法。
2. **費用放進報告和簡報**：第 6 節的表格。**使用者還沒同意**，做之前先問。
   - 簡報可加一頁「成本」，放在 speed 頁之後。
   - 報告可在第 1 節成績總覽加一欄。
3. **多跑幾次降低運氣成分**：`scripts/run_all.py --repeat 2`。雲端 Qwen 要花 OpenRouter 額度，先問。
4. **S2 外觀人工盲測**：把兩邊的 Cycles 渲染圖（opus55poc 的 `runs/*/easy/s2-*/review_cycles/`）匿名排版，請人評。
5. **其餘關卡的程式碼審查**：要用 Gemini，先問使用者是否接受費用。
6. 簡報如需 PPTX，從 Slides artifact 的 Share › Export 匯出（使用者操作）。

## 9. 快速驗證環境是否正常

```bash
sudo bash bench/install.sh && pip install requests pillow numpy scipy shapely
bash scripts/make_keys.sh ~/qwenpoc-keys                       # 最後 7 行都要是 ok
python3 scripts/score_all.py --verify-reference --keys ~/qwenpoc-keys   # 20 行都要是 ok，約 2 分鐘
rm -rf ~/qwenpoc-keys                                          # 要跑受測模型前先移掉答案卷
```

2026-11-18 在雲端容器用新的 `run_all.py` 經 OpenRouter 實跑 s3-hard 一關作為冒煙測試：100 分、804 秒、19 次操作、$0.09。整條流程正常。
