# qwenpoc — 地端 Qwen3.8-Flash-Next 能不能跑 AI 機房 3D pipeline？

這個 repo 是一套可以在地端重現的測試：讓模型只透過一個 `bench` 指令操作無頭 Blender，完成 AI 機房建模流程的 10 個關卡，再用程式自動計分。

**結論（雲端實測）**：Qwen 3.8 Flash 即使是條件最好的雲端託管版，也有 2 個關卡不及格——「看現場照片推回佈局」52.6 分、「設計圖對現場照片找差異」60 分（Opus 5.5 為 96.1 與 100）。10 關加權總分 Qwen 62.7、Opus 99.1。地端 Flash-Next 的上下文、精度和速度條件都不會比雲端版好，因此這條流程建議使用 Opus。完整報告：[`report/full_report.html`](report/full_report.html)（下載後用瀏覽器開啟）；簡報：[`report/slides.pdf`](report/slides.pdf)。

這個 repo 的用途是**在地端實測確認**這個推論。

## 快速開始

```bash
sudo bash bench/install.sh && pip install requests pillow numpy scipy shapely
```

```bash
python3 scripts/run_all.py --runs runs/onprem --base-url http://HOST:8000/v1 --model Qwen/Qwen3.8-Flash-Next
```

```bash
bash scripts/make_keys.sh ~/qwenpoc-keys
```

```bash
python3 scripts/score_all.py --runs runs/onprem --keys ~/qwenpoc-keys
```

詳細步驟：人看 [`docs/REPRODUCE.md`](docs/REPRODUCE.md)；交給 coding agent（Codex、Claude Code）時，agent 會自動讀 [`AGENTS.md`](AGENTS.md) / [`CLAUDE.md`](CLAUDE.md)。接手整個專案（背景、完整成績、費用、待辦）請讀 [`docs/AGENT_HANDOFF.md`](docs/AGENT_HANDOFF.md)。

## 10 個關卡

| 階段 | 代號 | 任務 | Opus 5.5 | Qwen 3.8 Flash（雲端） |
|---|---|---|---|---|
| 1 | `s1-easy` | 平面圖 → 3D 機房（16 櫃） | 97.1 | 97.1 |
| 1 | `s1-hard` | 平面圖 → 3D 機房（58 櫃、L 形） | 100 | 100 |
| 1 | `s2` | 參考照片 → 機櫃模型（只量幾何，滿分 40） | 40 | 40 |
| 1 | `s3-easy` | 機櫃擺進機房 | 100 | 100 |
| 1 | `s3-hard` | 機櫃擺進機房（58 櫃） | 100 | 100 |
| 1 | `s1p` | 5 張現場照片 → 推回佈局 | 96.1 | **52.6** |
| 2 | `d1` | 竣工比對：設計圖 vs 7 張現場照片 | 100 | **60.0** |
| 2 | `d2` | 空機房佈局設計（9 條規則、最多機櫃） | 97.2 | 86.8 |
| 2 | `d3` | 6 條冷卻水管 3D 繞行 | 100 | 99.5 |
| 2 | `d5` | 依三視圖復刻 CDU 設備 | 99.97 | 99.05 |

Qwen 每一關都比 Opus 慢 1.8–15 倍；S1P 的最長對話 274,507 token 已超過 Flash-Next 地端原生上限 262,144。

## 公平性

- 兩邊拿到一字不差的任務說明（`harness/prompts/`），同樣的工具、60 次操作上限和時間上限，推理強度都是 high。
- Qwen 的工具限制由 `harness/qwen_runner.py` 強制；Opus 是全新的 Claude Code session，限制靠指令並事後稽核對話紀錄。
- 答案卷不在 repo 裡，由 `scripts/make_keys.sh` 從固定種子重建，並用雜湊比對確認和報告用的版本相同。
- 計分全部用程式（`score/`），`scripts/score_all.py --verify-reference` 可以在你的機器上重算 20 個參考成績。

## 目錄

| 路徑 | 內容 |
|---|---|
| `bench/` | `bench` CLI 與常駐的無頭 Blender 伺服器 |
| `harness/` | 模型執行迴圈 `qwen_runner.py`（支援任何 OpenAI 相容端點）與任務說明 |
| `inputs/`、`ref/` | 各關卡的輸入（圖面、模擬現場照片、起始場景、公開機櫃照片） |
| `gen/`、`oracle/` | 題目產生器與參考解（出題端） |
| `score/` | 各關卡計分程式與檢視圖工具 |
| `scripts/` | 一鍵執行、重建答案卷、計分彙整 |
| `reference/` | 報告所用的雲端 Opus 與 Qwen 執行紀錄 |
| `report/` | 完整報告與第一階段報告（單一 HTML 檔）；簡報 `slides.html`（方向鍵翻頁）與 `slides.pdf`，原始檔在 `report/slides/`，用 `report/build_slides.py` 重建 |

來源：從 `clarencechien/opus55poc` 的原始工作區整理而來（分支 `claude/eloquent-lovelace-4vrek4` 的 commit `b32b206`，目錄 `datacenter/`；分支最新狀態只剩一份指向本 repo 的說明）。
