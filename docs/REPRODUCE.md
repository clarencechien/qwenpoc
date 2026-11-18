# 重現手冊：在地端的 Qwen3.8-Flash-Next 上跑同一套 10 個關卡

對象：負責地端模型的團隊，或代為操作的 coding agent（Codex、Claude Code；agent 請看根目錄的 `AGENTS.md`，步驟相同）。

目的：把報告裡的 10 個關卡接到自架的 Flash-Next 上各跑一次，確認「地端表現不會比雲端託管版好」這個推論。報告和雲端版成績在 `report/full_report.html`。

## 1. 需要準備的

| 項目 | 需求 |
|---|---|
| 模型服務 | OpenAI 相容的 `/v1/chat/completions` 端點，要支援 tool calling 和圖片輸入（vLLM 或 SGLang） |
| 測試機 | Linux、4 核 CPU、16 GB 記憶體即可，不需要 GPU（Blender 只做無頭預覽） |
| 軟體 | Python 3.11 以上；Blender 4.2 LTS 由安裝腳本下載 |
| 時間 | 雲端版跑完 10 關約 5 小時；地端視推論速度而定 |

vLLM 官方 recipe 的啟動參數（請依你們的版本確認）：

```bash
vllm serve Qwen/Qwen3.8-Flash-Next --enable-auto-tool-choice --tool-call-parser qwen3_coder --reasoning-parser qwen3
```

- 原生上下文 262,144 token。要延伸到 1M，recipe 的做法是加 `--max-model-len 1000000`、對應的 `--hf-overrides`，並設 `VLLM_ALLOW_LONG_MAX_MODEL_LEN=1`。
- **建議兩種設定都跑**：雲端版在 S1P 用到 274,507 token（超過原生上限），D1 用到 240,804、D5 用到 233,251（接近上限）。
- 請記下：精度（BF16、FP8 或哪一種量化）、GPU 配置、推論框架與版本、上下文設定。

## 2. 安裝

```bash
git clone https://github.com/clarencechien/qwenpoc && cd qwenpoc
```

```bash
sudo bash bench/install.sh
```

```bash
pip install requests pillow numpy scipy shapely
```

安裝腳本會把 Blender 4.2 裝到 `/opt/blender`、補上無頭渲染要的 EGL 函式庫，並建立 `bench` 指令。用 `bench --help` 確認。

## 3. 先跑一關試試（約 10 分鐘）

```bash
python3 scripts/run_all.py --runs runs/onprem --stages s3-hard --base-url http://HOST:8000/v1 --model Qwen/Qwen3.8-Flash-Next
```

- 端點要金鑰時加 `--api-key-env 變數名稱`。
- 推理強度預設送 `reasoning_effort: high`。伺服器要別的欄位時，用 `--reasoning-effort none --extra-body '{"欄位": 值}'`。
- 完成後 `runs/onprem/s3-hard-r1/run_summary.json` 的 `reason` 應該是 `submitted`。

## 4. 跑全部 10 關

```bash
python3 scripts/run_all.py --runs runs/onprem --base-url http://HOST:8000/v1 --model Qwen/Qwen3.8-Flash-Next
```

| 代號 | 關卡 | 時間上限 |
|---|---|---|
| `s1-easy` / `s1-hard` | 平面圖 → 3D 機房（16 櫃 / 58 櫃 L 形） | 45 分 |
| `s2` | 參考照片 → 機櫃模型 | 45 分 |
| `s3-easy` / `s3-hard` | 把機櫃擺進機房 | 45 分 |
| `s1p` | 5 張現場照片 → 推回佈局 | 60 分 |
| `d1` | 竣工比對：設計圖 vs 7 張現場照片 | 60 分 |
| `d2` | 空機房佈局設計（9 條規則） | 45 分 |
| `d3` | 6 條冷卻水管 3D 繞行 | 45 分 |
| `d5` | 依三視圖復刻 CDU 設備 | 45 分 |

- 每關最多 60 次計次的 Blender 操作。這些限制和模型能用的工具（單一 `bench` 指令、寫檔、讀檔或看圖，圖片縮到長邊 1568 px）由程式強制，**請不要放寬**，否則無法和雲端版比較。
- 中斷後重下同一個指令會跳過已完成的關卡；跑到一半中斷的關卡要先刪掉它的目錄。
- 伺服器回 400 類錯誤（例如超出上下文）時，該關會乾淨地結束，原因記在 `run_summary.json` 的 `reason`，作品照當下狀態計分。這就是要量的結果，不要重跑或幫忙。
- 時間允許的話加 `--repeat 2` 每關跑兩次；雲端版每關只跑了一次。

## 5. 重建答案卷（全部跑完之後）

答案卷不在 repo 裡，用固定的亂數種子重建，放在 repo 外面。**要等所有關卡跑完才建**：模型透過 `bench exec` 執行的 Python 沒有沙箱，理論上讀得到機器上的任何檔案。

```bash
bash scripts/make_keys.sh ~/qwenpoc-keys
```

最後幾行都要是 `ok`（和報告用的答案卷逐位元相同）。可以再確認這台機器的計分結果和報告一致（約 2 分鐘，20 行都要是 `ok`）：

```bash
python3 scripts/score_all.py --verify-reference --keys ~/qwenpoc-keys
```

## 6. 計分

```bash
python3 scripts/score_all.py --runs runs/onprem --keys ~/qwenpoc-keys
```

產生 `runs/onprem/summary.md`：每關的地端分數、雲端 Qwen 和 Opus 的分數、結束原因、用時、操作次數、最長對話 token（≥ 上限 85% 會加粗），以及稽核欄。10 關都到齊時會算出和報告相同的判定：每關都要 ≥ 80%，而且加權總分 ≥ 80。

稽核欄出現 `CHECK` 時，表示某支 Blender 腳本提到執行目錄以外的路徑或答案檔名稱，請打開 `bench_log.jsonl` 對應的行看是不是無害的用途。

## 7. 要回報的數字

| 項目 | 說明 | 雲端版對照 |
|---|---|---|
| 分數 | `summary.md` | 見下表 |
| `reason` | `submitted` 正常交卷；`api_stop…` API 錯誤（含超出上下文）；`time`、`max_turns` 超出上限 | 全部 `submitted` |
| 用時、操作次數 | `run_summary.json` 的 `seconds`、`bench_calls` | 見下表 |
| 最長對話 | `peak_prompt_tokens` | S1P 274,507、D1 240,804、D5 233,251 |
| 部署條件 | 精度、GPU、框架版本、上下文設定、平均每秒輸出 token | — |

雲端託管版（OpenRouter `qwen/qwen3.8-flash`，推理強度 high）和 Opus 5.5 的成績：

| 關卡 | Opus | Qwen 雲端版 | Opus 用時 | Qwen 雲端版用時 |
|---|---|---|---|---|
| S1 easy | 97.1 | 97.1 | 66 秒 | 561 秒 |
| S1 hard | 100 | 100 | 95 秒 | 1,397 秒 |
| S2（幾何，滿分 40） | 40 | 40 | 543 秒 | 1,002 秒 |
| S3 easy | 100 | 100 | 102 秒 | 733 秒 |
| S3 hard | 100 | 100 | 135 秒 | 478 秒 |
| S1P 照片推佈局 | 96.1 | **52.6** | 954 秒 | 3,452 秒 |
| D1 竣工比對 | 100 | **60.0** | 567 秒 | 3,685 秒 |
| D2 佈局設計 | 97.2 | 86.8 | 699 秒 | 2,589 秒 |
| D3 管線繞行 | 100 | 99.5 | 468 秒 | 943 秒 |
| D5 三視圖建模 | 99.97 | 99.05 | 154 秒 | 2,276 秒 |
| **加權總分** | **99.1 通過** | **62.7 不通過** | | |

## 8. 已知狀況

- 雲端版每關只跑 1 次，分數會有波動。
- S2 的參考照片只有 4 張（另外 2 張候選照片當時下載失敗）；S2 的自動分數只量幾何，不評外觀。
- D2 的滿分基準 250 櫃是我們的求解器找到的最好結果（`oracle/d2_solver.py`，重算約 22 分鐘），不保證是理論最佳。
- 雲端版 D3 第一次執行因為單次回覆超過當時 32,000 token 的輸出上限被截斷；runner 已改成上限 64,000 並在截斷時要模型接著寫，報告採用修正後重跑的成績。
- 預覽渲染用 Blender Workbench 的軟體渲染，每張約 1 秒；沒裝 EGL 函式庫時 `bench render` 會失敗，重跑 `bench/install.sh` 即可。
- 想看每一步：`RUN/transcript.jsonl` 是完整對話，`RUN/bench_log.jsonl` 是每次 Blender 操作和執行的腳本。
- 雲端 Opus 和 Qwen 的完整執行紀錄在 `reference/`。
