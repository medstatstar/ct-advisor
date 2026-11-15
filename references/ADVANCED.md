# ct-advisor Advanced Reference (for developers / debugging)

> 本文件承载从 SKILL.md 下移的**技术内容**（ct-base §4「尽量不涉及命令行」+ §13.3「技术内容整体下移」）。
> 普通使用者无需阅读；日常使用看 README 第 1–5 节即可。
> This file holds the technical material moved out of SKILL.md. Ordinary users don't need it.

---

## 1. Runtime requirements

- **Python 3.10+**（代码使用 `str | None` 等 PEP 604 语法）
- **纯标准库（stdlib-only）**：`urllib` / `json` / `hashlib` / `http.server` 等，**无需安装任何第三方包**
- `requests` **不是必需依赖**（2026-10-15 起传输层已切换为 stdlib `urllib`）。装了不会改变行为；没装时 stderr 会打印
  `[entry] 未检测到 requests，使用 stdlib urllib 传输（功能不受影响）`，属正常提示
- 出站网络：仅需访问 `https://ct-advisor.coze.site/run`（可在 `config.json` 的 `auto_approve_endpoints` 中查看白名单）

---

## 2. Pipeline & entry points

```
ask.py                 ← compat shim (v1.3.19+): forwards argv to entry.py, no decoding
  └─ entry.py          ← the ONLY entry: vague gate / attachment / cache / delegate / plain-text exit
       ├─ serve.py     ← resident orchestration service (127.0.0.1:18771, idle 3600s)
       └─ orchestrate.run_orchestrate  ← (inline fallback)
            └─ adapters.refiner.refine_forward → Coze /run
```

| 文件 | 角色 |
|---|---|
| `scripts/ask.py` | 旧调用兼容壳（v1.3.19+）：剥离已废弃参数（`--raw` / `--timeout`）后原样转发给 `entry.py`；**不解码、不捕获输出**（子进程直接继承父 stdout/stderr） |
| `scripts/entry.py` | 主引擎。vague 闸门、附件处理、答案缓存预检查、委托块（`CT_TOOL_DELEGATE`）自动缝合 |
| `scripts/serve.py` | 常驻编排服务。预热重模块，`/ask` 复用 `sys.modules`；`/version` 暴露代码指纹供自动重启判定 |
| `scripts/orchestrate.py` | 编排：并行触发 Coze + 本地技能预取，`build_output` 决定「包裹答案」或「委托」 |
| `scripts/answer_cache.py` | 答案缓存：`sha256(question\|doc_context\|difficulty)`，TTL 1800s |
| `scripts/code_fingerprint.py` | 代码指纹：`scripts/*.py` + `adapters/**/*.py` 的 mtime 最大值，驱动常驻服务自动重启 |

---

## 3. CLI

```bash
# 正常调用（推荐，也是 agent 唯一允许的动作）
python scripts/ask.py --q "多中心研究中如果一个中心突然要退出怎么处理"
python scripts/ask.py --q "..." --attach "path/to/file.docx"

# 说明：--raw / --timeout 已废弃（entry.py 出口已是明文、内部自管超时），传了会被忽略
python scripts/ask.py --q "..." --raw

# 落盘：把完整 stdout 写入文件，便于复验而不必重跑（避免重复 Coze 调用）
python scripts/entry.py --q "..." --out ./out.txt

# 常驻服务
python scripts/serve.py                    # 手动前台启动（独立终端，可活满空闲窗口）
curl http://127.0.0.1:18771/health
curl http://127.0.0.1:18771/version        # {"version","code_fingerprint","orchestrate_mtime","port"}
curl http://127.0.0.1:18771/shutdown       # 应急：端口被卡住的服务占用时
```

### 环境变量

| 变量 | 默认 | 说明 |
|---|---|---|
| `CT_ADVISOR_PORT` | `18771` | 常驻服务端口 |
| `CT_ADVISOR_IDLE` | `3600` | 空闲超时（秒），超时自动退出 |
| `CT_ADVISOR_DATA_ROOT` | 技能 `config/` | 缓存 / 去重库的数据根目录 |
| `CT_ADVISOR_ANSWER_TTL` | `1800` | 答案缓存 TTL（秒） |

---

### Coze 调用协议（实现细节）

- **端点**：`config.json` → `refiner.endpoint`（默认 `https://ct-advisor.coze.site/run`），须在 `auto_approve_endpoints` 白名单内，否则被授权闸门拦截
- **协议（v1.3.14+）**：**异步提交 + 轮询** —— `POST /async_run` → `GET /task/{id}`；仅当端点不支持异步时才回退同步 `/run`
- **为什么必须异步**：Coze 网关对**同步与流式**调用在 **60.0s** 整硬掐断；而单轮耗时实测跨 3–72 秒（多数 30–70 秒），按预测分流不可靠
- **轮询总时限**：`refiner.timeout = 90` 秒；长任务（complex / 模板类 / 追问）走 `long_timeout = 300` 秒
- **超时行为**：不硬错，回落本地草稿（未经云端精校），stderr 标注 `[coze] FALLBACK_TO_LOCAL_DRAFT`
- **出站脱敏**：`adapters/sanitize.py` 剥离身份证号 / 手机号 / 邮箱后再发送
- **重试语义**：连接阶段失败（代理不可达 / DNS / 拒绝）→ 换路径重试一次；**超时不重试**（Coze 多半已收到，重发即重复）；HTTPError 跳出重试交上层分类

---

## 4. 输出契约（重要）

`entry.py` 的 stdout 恒为 **明文答案 + 三行尾部**（对外出口自 v1.3.21 起不再有 base64；base64 仅保留为 `orchestrate` / `refine_answer` / `serve` 之间的**内部进程间协议**）：

```
{明文答案正文}
<<<CT_ANSWER_END>>>
checksum: {sha256[:16]}
answer_file: {绝对 POSIX 路径，纯 ASCII}
```

- **单一产出点**：标记与 checksum 只在 `_emit_plain()` 一处产生；出口按 **UTF-8 字节直写**（不查控制台代码页、没有开关）
- **`ask.py` 是兼容壳**（v1.3.19+）：只做参数转发，**不解码**——agent 侧零解码
- **解析纪律**：答案正文本身可能引用 `<<<CT_ANSWER_END>>>`（用户恰好在问这套协议）。消费者必须锚定「**最后一个合法尾部**」（标记独占一行 + 紧跟 `checksum:`），**不可**用 `split(MARK, 1)[0]`，否则会把答案从那里切断
- **`answer_file:` 通道**：给出绝对 POSIX 路径且纯 ASCII，所以即使正文被控制台打得七零八落，这一行仍逐字节完好，读文件即可取回原文（与终端代码页无关）；同名同内容时**复用不重写**（避开网络共享 ACL 覆盖拒绝）；`_answers/` 不可写则回退 `%TEMP%/ct-advisor/<sha16>.md`
- **允许「读文件」，禁止「解码乱码串」**：cp936 控制台会把非法 UTF-8 字节替换成 `U+FFFD`，原始字节永久丢失，任何反解或模型补字都过不了 checksum —— 那属于改写答案（违反 ALCOA+）

**退出码**：`0` 成功；非 0 时以 stderr 为准（`entry.py` 顶层兜底会把未捕获异常转成合法的人读提示，stdout 仍可交付）。

---

## 5. 诊断与故障排查

| 现象 | 含义 / 处理 |
|---|---|
| stderr `[ct-advisor] answer-cache hit` | 命中本地答案缓存，**没有**发出 Coze 请求（30 分钟内同问题复用） |
| stderr `[entry] 进入编排（若命中本地答案缓存则不出站）...` | 编排开始；是否真的出站看紧随其后的日志 |
| stderr `[entry] 已后台拉起常驻服务` | 常驻服务不在（被宿主清理或首次运行），已重新拉起 |
| stderr `[entry] 检测到技能代码更新，重启常驻服务` | 代码指纹前移，自动重启以加载新代码（无需手动干预） |
| stderr `[ct-advisor][ERR] code=...` | 机器可读错误信号，见 SKILL.md「Error Self-Heal Protocol」 |
| 答案里出现 `⚠️ 未授权出站到 Coze` | endpoint 不在 `config.json` 的 `auto_approve_endpoints` 白名单 |
| 答案里出现 `⚠️ 无法连接 Coze：未能从 config.json 读到 refiner.endpoint` | `config.json` 缺失或损坏 |
| 答案尾部缺 `<<<CT_ANSWER_END>>>` / `checksum:` | 捕获层截断；按 `answer_file:` 行读取落盘文件（勿手工拼接） |
| 服务端异常 | 服务进程的 stderr 落盘在 **`config/serve.log`**（自动 1MB 截断），优先看这里 |

### 常见误区

- **`serve.log` 里多次「预热完成 / 监听」不等于版本反复重启**：宿主（桌面端 / Bash 工具）会在命令结束时回收 detached 进程，下次调用重新拉起属正常。
- **`entry.py` 字节数与预期不符**：多为换行符口径（CRLF vs LF）差异，不影响行为。
- **不需要手动 `shutdown`**：代码指纹机制会在下次调用时自动重启服务（见 `scripts/code_fingerprint.py`）。

---

## 6. 测试

```bash
python scripts/test_local_guards.py     # 本地守卫离线单测（doc_memory / dedup / scope / forward）
python scripts/test_seven_flows.py      # 七大流程决策链路（mock Coze，无网络）
python scripts/answer_cache.py          # 答案缓存自测
python scripts/code_fingerprint.py      # 代码指纹自测（含采集耗时）
```

---

## 7. 扫描器误报说明

- `adapters/coze/` 为 Coze 私有镜像（契约与节点实现），**不随发布包分发**（`.gitignore` / `.clawhubignore` 已整目录排除）。
- `adapters/coze_token_embedded.py` 内的 token 是**公开混淆凭据**（XOR + base64），非用户私钥，按设计内嵌，勿报为泄露。
- `config/serve.log` / `config/answer_cache/` / `.coze_race_cache/` 均为运行时产物，已在 `.gitignore` 排除。

---

## 8. Session, Context, Cache & Routing Contract (2026-10-22, moved from SKILL.md)

Two new local modules close the gaps the past-30-day Feishu advisorlog exposed (no multi-turn context, 21% redundant sends, ~47% of real questions wrongly tagged "out-of-scope" because they were writing/ops/compliance tasks). **Both run purely locally; the Coze payload is enriched, not replaced.**

### A. `scripts/session_store.py` — unified per-session store

Single JSON store at `config/session_store.json` (cross-process file lock: `msvcrt` on Win / `fcntl` on POSIX; atomic replace; any exception silently degrades to "no-hit / no-record" so it never blocks the main flow). Three capabilities keyed by `session_id`:

| Capability | API | Policy |
|---|---|---|
| Multi-turn context | `history(session_id)` → `[{question, answer_summary}]` | Injected as `conversation_history` into the Coze payload. Pruned by OR-rule: ≤10 rounds **OR** ≤2h, hard cap 24h. Empty `session_id` → single-turn (no history, still global cache). |
| Answer cache | `cache_get(question, doc_context, difficulty)` | Exact sha256 fingerprint (question+attachment+difficulty), 30-min TTL (`CT_ADVISOR_ANSWER_TTL`), **cross-session** — same question anywhere returns the same answer, 0 Coze calls. |
| Near-dup dedup | `dedup_check(session_id, question)` → `(is_dup, prev_answer, secs_ago)` | Same session, 10-min window, `difflib.SequenceMatcher.quick_ratio ≥ 0.90`; on hit the caller short-circuits and replays `prev_answer`. |
| Record | `record(session_id, question, answer, …)` | Called **only after a real outbound** (never on a short-circuit) — writes history + global cache + session dedup. `clear_session(session_id)` starts a fresh session (keeps global cache). |

`entry.py` wires all three in `main()` (via `--session <id>`); the workbench `ct-advisor-proxy.py` imports the same module for `/run` and `/async_run`.

### B. `scripts/scope_guard.py` — domain router (replaces the old out-of-scope gate)

Controlled-vocabulary, multi-label classifier (`classify_domains(q)` → up to 3 of: `compliance / ops / writing / design / stats / safety / registry / data / rws / methodology / medical / device / vet`). `assess(q) → (in_scope, tag, referral)`:

- any domain hit **or** a weak life-science signal → in-scope (no referral);
- only a **clearly non-medical** signal (consumer electronics / finance / FMCG / real-estate / …) → out-of-scope with a **constructive** referral that names the coverage and suggests a next step (never a blank refusal).

The router writes two payload hints consumed by Coze (see C): `scope_hint` (only when out-of-scope) and `domain_hint` (the multi-label list). 15/15 offline selftest pass; **0% out-of-scope on the 68 real advisorlog questions**.

### C. Coze payload contract (request fields the engine should accept)

| Field | Set by | Meaning |
|---|---|---|
| `conversation_history` | entry.py / proxy (`session_store.history`) | Prior rounds (question + answer summary) so the engine can resolve follow-up / continuation without the user re-typing context. **Front-end may also send its own `conversation_history`; the proxy injects the server-side one only when the field is absent.** |
| `scope_hint` | proxy (`scope_guard.assess`) | `"non_medical"` only when out-of-scope — engine should prepend the referral framing. |
| `domain_hint` | proxy (`scope_guard.classify_domains`) | e.g. `["compliance","ops"]` — lets the engine bias retrieval / sibling-skill routing. |
| `query_meta.output_format` | front-end (`auto/doc/outline/table/ppt`) | Expected answer shape; `doc`= deliverable-writing mode (raises C3 length ceiling, allows `##`/`###`+tables); the engine now responds per shape |
| `session_id` | front-end (`X-Session-Id` header) **or** body | Stable per-machine id (mirrors `query_origin`); drives history + dedup. |

**Coze-side `output_format=doc` mode is now live** (user confirmed 2026-10-22 "Plan A: long-form + export button"): `full_analysis_node` injects `query_meta.output_format` into the prompt (previously never reached; only `auto` was effective), the doc mode skips the C14 "no file return" disclaimer and uses a 6000-char defensive safety ceiling; `shared_contract.md` and `full_analysis_cfg.json` `sp` add C3-doc clauses. Context / cache / dedup remain locally enriched and short-circuited by the proxy; the engine only receives a richer request. A new `POST /api/export_docx` (stdlib-only OOXML generation) powers the front-end "📄 Export docx" button — files are generated locally and never round-trip to the cloud, so C14 holds. See `docs/answer_length_format_deviation_20261022.md`.

### D. Workbench proxy local endpoints (no Coze round-trip)

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/history?session_id=` | GET | Returns `{ok, history:[{question, answer_summary}]}` from `session_store`. |
| `/api/turn` | POST | `{session_id, question, answer, doc_context, query_meta}` → `session_store.record(...)` (called by the front-end after a successful answer). |
| `/api/feedback` | POST | `{session_id, run_id, rating, note}` → appends a `type=rating` line to `workbench/feedback_log.jsonl` (satisfaction signal, local only). |
| `/api/export_docx` | POST | `{text, title}` → returns a stdlib-generated OOXML `.docx` as an attachment (local only; the cloud engine still returns text only, so C14 holds). |

Short-circuit return shape: cache/dedup hit on `/async_run` returns `{"task_id": <local>}`; on `/run` returns `{"result":{final_answer, cache_hit:true}}`; `/stream_run` is **never** short-circuited (it streams, proxy only injects context).

## 9. Extended SKILL.md sections (moved verbatim on 2026-11-15)

> ct-base §16.1 requires `SKILL.md` ≤ 200 lines. The sections below were moved out of
> `SKILL.md` **without editing a single line**; they remain authoritative. The entry file
> keeps the HIGHEST PRIORITY action, F33 guardrail, HARD GATE integrity table, Quality Gate,
> Outbound Authorization Gate and Bug Report, and links back here.

### Return path: `entry.py --stitch` (2026-11-09)

Handoff used to be one-way: after the user ran several sibling skills there was no
code-driven way back. `--stitch` closes that loop **without adding a second entry
point or giving the local LLM any decision space**:

```
python scripts/entry.py --stitch '{"question":"...","results":[
  {"tool":"ct-registry","files":["<path>/report.md"]},
  {"tool":"ct-safety","files":["<path>/faers_report.xlsx"]}]}'
python scripts/entry.py --stitch @spec.json     # --q may be omitted in stitch mode
```

`scripts/stitch_results.py` parses `.md/.txt/.log/.json/.csv/.tsv/.xlsx` locally
(stdlib only) and stitches a deterministic summary through the **same**
`_emit_plain` exit (marker / checksum / answer_file). **By default** it never
imports the orchestrator or any HTTP client, never calls Coze, and never sends
skill outputs anywhere — 🔴 F33: outputs may contain Tier-B confidential material,
so the whole path stays on this machine. Reads are bounded by an extension allowlist, a 2 MB
per-file cap, a 20-file cap, a 4 000-char excerpt cap and a credential-filename
denylist. Missing or unparsable outputs are reported, never invented. The summary
is explicitly marked non-audit-grade and never rewrites or infers numbers.

🔴 **HARD GATE unchanged**: `--stitch` is a mode of `entry.py`, not another script
the agent may choose. The agent still runs one command and pipes stdout verbatim;
the handoff answer itself carries the ready-to-use `--stitch` hint, generated in
code by `refine_answer._stitch_hint()`.

**L3 methodology interpretation (opt-in, 2026-11-09)**: adding
`"interpret": true` to the stitch spec asks for a methodology explanation of the
results. `scripts/interpret_results.py` — a **separate** module, so
`stitch_results.py` stays statically free of any network import — sends **only**
a code-built methodology question plus allowlisted **sanitized numeric values**
(max 12 finite numbers, from JSON outputs only) to the pre-authorized Coze
endpoint. The user's original question, raw output text, file names/paths, drug /
protocol names, trial IDs and subject data **never leave the machine** (F33).
The outbound request additionally passes the explicit
`_check_outbound_authorization` gate; if the endpoint is not whitelisted, no
allowlisted numbers exist, or Coze returns an error / `need_tool` / an empty
answer, the cloud interpretation is discarded and only the local summary is
delivered, with the reason stated. Covered by
`scripts/test_interpret_sanitization.py` (27 offline cases).

> **There are no flags to tune the output.** `--out`, `--b64`, `--answer-file` and
> `--no-answer-file` were removed in v1.3.21: every run writes the same bytes to stdout and the
> same bytes to `<skill>/_answers/{checksum}.md`. That file is the **data source of truth** — if
> a terminal shows mojibake (a display-layer problem, never a data problem), read that file and
> deliver from it instead of re-running anything.
>
> **Length is no longer a channel risk.** A 6000-char CJK answer now leaves `entry.py` as
> ≈6,000 characters. Under base64 it was 24,000 — past the PowerShell ~20,000 truncation line
> and hard against the Bash inline ceiling (~30,000 → persisted to a file with a 2 KB preview
> only). Decision table 1c covers the truncation signal.
>
> `scripts/ask.py` still exists but is **not** the entry point: it is a zero-logic forwarder
> that inherits `entry.py`'s stdout/stderr/exit code for stale callers.

### What entry.py does internally (all code, zero LLM) — the canonical pipeline

```
STEP 1  Attachment gate (if --attach) — BOTH paths ship a FILE via doc_context
        ├─ < 5 MB   → doc_memory.build_file_payload(allow_upload=True): upload ORIGINAL file to Coze /upload_file, ship as `doc_context` (mode=file_id; base64-forward fallback on failure)
        └─ > 5 MB   → convert locally (office_to_md.py for OOXML / direct read for txt-like), upload the resulting **.md** through the SAME doc_context channel + ℹ️ notice that cloud answers from the md version
STEP 2  Vague gate (deterministic regex, scripts/route.py — binary: vague | forwarded, the ONLY local gate): vague → clarify_loop.py (≤3 rounds) → questions to user, stop; forwarded → continue (Coze re-judges difficulty with its own LLM; timeout tier via route.timeout_tier)
STEP 3  Forward to Coze — orchestrate.run_orchestrate(payload): Coze async submit (/async_run, ms-level → task_id) + local prefetch (handoff card by default; brief only when explicitly enabled) → poll /task/{id} until terminal → merge (sync /run only as fallback when the async endpoint is unavailable)
STEP 4  Delegate stitch — if Coze returns <<<CT_TOOL_DELEGATE>>>, entry.py auto-runs refine_answer.py --card-inline (code, no LLM); since 2026-11-09 this normally emits a client handoff card (@skill:<slug>) instead of executing the sibling CLI
STEP 5  Output — entry.py writes the answer file (UTF-8), then the same bytes + `<<<CT_ANSWER_END>>>` + `checksum:` + `answer_file:` to stdout.buffer (single protocol, single producer since v1.3.21)
```

> **LLM-forbidden zone**: every STEP above is executed by code. The local LLM
> never picks the channel, never judges difficulty, never decides forwarding.

### Output format

`scripts/entry.py` — stdout is the **plain-text answer plus a trailing integrity line and an
ASCII pointer to the answer file**:

```
{the answer text, as many lines as it needs}
<<<CT_ANSWER_END>>>
checksum: {sha256[:16] of everything before the marker, LF-normalized}
answer_file: C:/Users/<user>/.workbuddy/skills/ct-advisor/_answers/{checksum}.md
```

The marker sits at the **end** on purpose: any channel truncation removes it together with
the checksum, so a damaged capture is obvious at a glance instead of silently passing. The
checksum covers the answer body only (everything from the first byte up to and including the
newline immediately before the marker), so it is trivially reproducible.

`answer_file` is an **absolute ASCII path**, so you can hand it straight to the file-read tool
with no path assembly. The absolute form is used only when it is pure ASCII; if the skill lives
under a CJK path (user name / directory), the value degrades to the relative `_answers/{sha16}.md`
instead — that is the one form guaranteed readable in a garbled console, and you then join it with
the skill root you already know. Either way the file holds **byte-identical** content to the
stdout body.

> **Where base64 no longer lives (v1.3.21)**: nowhere. `orchestrate._finalize`,
> `refine_answer._emit_plain` and `serve./ask` all pass **plain text**; the marker/checksum pair
> is produced in exactly one function (`entry._emit_plain`). If you ever see a base64 envelope in
> any output, it is a leftover from an old resident process — the code fingerprint makes
> `entry.py` restart it automatically, so just re-run once and report it.

Verification code — only needed for a suspected mismatch in row 3:

```python
import hashlib, re
stdout = "...(entry.py output)..."
MARK = "<<<CT_ANSWER_END>>>"
if MARK in stdout:
    body = stdout.split(MARK, 1)[0]                    # everything before the marker
    expected = re.search(r"checksum:\s*([0-9a-f]{16})", stdout).group(1)
    if hashlib.sha256(body.encode("utf-8")).hexdigest()[:16] != expected:
        print("⚠️ answer integrity check failed")      # do not deliver, do not re-run
    else:
        print(body)                                    # deliver verbatim
```

**If the checksum does not match, the local LLM MUST NOT deliver the answer to the user.** This prevents any silent tampering.

> 🔴 **Encoding is no longer a setting you can get wrong (v1.3.21)**: `entry.py` writes the
> payload with `sys.stdout.buffer.write(utf-8 bytes)` — a **constant**, not a negotiation. It does
> not look at `sys.stdout.encoding`, `PYTHONIOENCODING`, or the console code page, and there is no
> flag to change it. Verified under `PYTHONIOENCODING=cp936`: the captured bytes decode as valid
> UTF-8 every time.
>
> What is *not* solved by that, and cannot be: a **terminal** may still render UTF-8 bytes through
> its own code page (`鏈熶复…`). That is a display-layer problem, so the engine does not try to
> detect it — instead every run also writes the identical bytes to
> `<skill>/_answers/{checksum}.md` and prints an **absolute ASCII** `answer_file:` line.
>
> 🔴 **The sanctioned repair is "read the source file", NOT "decode the garbled text"**: if stdout
> looks garbled, do exactly this —
>
> 1. take the path from the `answer_file:` line **as printed**. It is pure ASCII, so it survives the
>    very code page that mangled the answer (verified: in a simulated cp936 capture the whole answer
>    body was destroyed while this line came through byte-intact);
> 2. open it with the file-read tool — file reads are UTF-8 by default and independent of the
>    console code page;
> 3. deliver everything **before** `<<<CT_ANSWER_END>>>` verbatim.
>
> This is **not** a model "fixing" the text. The file never travelled through the console, so its
> bytes are the original ones; the model only moves bytes it did not author — precisely the role
> the HARD GATE allows. That is why reading the file works where every decode attempt fails.
> If `_answers/` is unwritable (network-share ACL refuses overwrite) the engine reuses an identical
> existing file instead of rewriting it, and falls back to `%TEMP%/ct-advisor/{checksum}.md` — the
> `answer_file:` value stays absolute, so the same three steps apply unchanged.
>
> 🔴 **No decoding of the garbled STRING — by anyone (HARD GATE · 2026-10-22)**: "read the file"
> above and "decode the mojibake" are different acts; **only the first is permitted**. Never ask the
> host model to repair / restore / guess echoed garbled text — not you, not a sub-agent, not any
> local model. This is not a capability gap, it is information loss. A cp936
> console is **not** a reversible double-encoding: many UTF-8 bytes are illegal under GBK, so the
> console substitutes `U+FFFD` and the original bytes are gone. Measured on a 127-char / 330-byte
> CJK answer: 13 `U+FFFD` substitutions, every repair chain (`cp936` / `gb18030` / `cp1252` /
> `latin-1` re-encode → UTF-8 decode) failed — even the `checksum:` line could not be recovered.
> Any "repaired" text you produce is invention: unverifiable against the checksum, and a
> rewrite of a clinical answer, which violates ALCOA+ and the HARD GATE. The **only** sanctioned
> recovery is reading `answer_file`; if that file does not exist, report the capture failure and
> stop — never deliver guessed text. (Latin-1 style 1:1 mis-decoding *is* reversible in theory,
> but the verdict is still "read the file", because the file is both cheaper and provably exact.)
>
> Optional hygiene, not a requirement: `[Console]::OutputEncoding = [Text.Encoding]::UTF8` before a
> PowerShell invocation makes the *screen* readable too. Note `$OutputEncoding` is a **different**
> variable (it governs stdin sent to native programs) and setting it alone does nothing; and the
> setting is per-process, so it must be applied in the same shell invocation.


> 🔴 **No host-model fallback (HARD GATE · 2026-10-15)**: ct-advisor is coze-only **by design** — there is no local knowledge base or database, so a host-model direct answer on a clinical question has no domain substrate and is **forbidden as a fallback** (a bare host-model answer was evaluated and rejected: quality cannot be guaranteed without the cloud knowledge base and tool chain). The same tiering rule means attachment / `doc_context` content must **never** leave the Coze channel. The ONLY sanctioned recovery for a broken capture is: **repair the capture → re-send once (≤1, usually served by the local cache)**. Everything else stops and reports.

> 🔴 **Short-circuit output obeys the same contract (2026-10-15 · unified into `session_store.py` 2026-10-22)**: both short-circuit paths — `session_store.cache_get` (exact-fingerprint answer cache, cross-session) and `session_store.dedup_check` (near-duplicate within a session window) — are wired into **both** the `entry.py` main chain AND the workbench `ct-advisor-proxy.py` (`/run` / `/async_run`). A short-circuited answer leaves `entry.py` through the **same plain-text exit** as a fresh Coze call (stderr marks `answer-cache hit` / `dedup short-circuit`; the proxy returns a local pseudo-task so the front-end is oblivious). A cached answer is a legitimate delivery, not an error.

> 🔴 **Single-run discipline (performance · as mandatory as the HARD GATE)**: `entry.py` is one complete Coze remote call and the main time cost of a single Q&A. The default is **one call per question**. **Re-calling `entry.py` purely to "verify" the output is strictly forbidden** — with the plain-text exit there is nothing left to verify locally. The single exception is decision-table row 2: **at most one re-send to repair a broken CAPTURE**, with the reason stated to the user — never for a checksum mismatch on clean text (row 3 → stop) and never without capture evidence. If you need to persist output, it is already on disk at `answer_file` — do not re-run for that either.

**Verification discipline (L3 · 2026-10-22, final in v1.3.21)**: the sha256 check is only needed on a suspected mismatch — the trailing marker already proves completeness in the normal path, and no flag can toggle the output shape any more. **Forbidden**: writing stdout to a temp file for the check, extra tool round-trips, post-hoc temp-file cleanup, and any attempt by the LLM to re-encode or re-transport the answer.

## Performance Optimization & Deployment Notes (L1/L2/L3, 2026-09-26)

This skill has implemented four performance optimizations; see `PERF_SOP.md` for details:
- **L1 Resident orchestration service** (`scripts/serve.py` + `entry.py` client): heavy modules are warmed up once, so local overhead → 0. Idle window raised 600s → 3600s (2026-10-16).
- **L2 Parallel warm-up** (`scripts/orchestrate.py`): eliminates stacked serial imports.
- **L3 Inline verification discipline**: sha256 is computed inline in memory and only on a suspected mismatch — the plain-text exit's trailing marker already proves completeness. Zero LLM round-trips.
- **L4 Single-command + unified session store (2026-10-16 · unified & multi-turn 2026-10-22 · **single path 2026-10-22**)**: `scripts/entry.py` now emits the **final plain-text answer in one call** — no decode step, no second script, and the payload shrinks from 4× (base64 of CJK) back to 1×. `scripts/ask.py` is retained only as a zero-logic forwarder for stale callers. The unified `scripts/session_store.py` (shared by **both** entry.py and the workbench proxy) gives a 30-min cross-session answer cache + a 10-min in-session near-duplicate dedup, so a re-send / repeated question costs **0 Coze calls**; it also injects multi-turn `conversation_history` into the Coze payload so context carries across rounds (previously the history was computed but never injected — root cause of 18% "承接上一轮" manual recaps). Root cause fixed: the `dedup_guard` short-circuit had never been reachable from `entry.py` (guard wired only into the `refine_answer.py` CLI; `query_origin` never set by entry.py), so every re-run was a real Coze round-trip — three of them for a single question in the 2026-10-16 log.
- **L5 Scope broadening via domain router (2026-10-22)**: `scripts/scope_guard.py` was rewritten as a controlled-vocabulary domain router (multi-label: compliance / ops / writing / design / stats / safety / registry / data / rws / methodology / medical / device / vet). The three real high-frequency blocks users actually use — **regulatory response / trial operations / deliverable drafting** — are now first-class in-scope core domains (a writing / outline / template question is NO LONGER treated as out-of-scope); only a clearly non-medical / non-life-science question (e.g. consumer electronics, finance, FMCG) emits a constructive referral. 0% out-of-scope on the 68 real questions from the past-30-day Feishu advisorlog.

**⚠️ Deployment restriction (important)**: the skill directory lives on a network share whose ACL is creator-owner — you can create new files, but **overwriting pre-installed existing files raises `PermissionError 13`**, and deletion is also blocked by a trash hook. Therefore, any change to `scripts/*.py` / `SKILL.md` should be written as a same-directory `.new` copy, then overwritten on the user's local machine with `move /Y` (command in `PERF_SOP.md` §4, or run `scripts/_perf_deploy.py`).

**Version drift**: the resident service caches code; after updating skill files, the old service still runs old code until its idle timeout (3600s since 2026-10-16; override with `CT_ADVISOR_IDLE`). `entry.py` has a built-in `/version` probe that, before reusing an old service, compares a **code fingerprint** — the max mtime across `scripts/*.py` + `adapters/**/*.py`, computed by `scripts/code_fingerprint.py` — against the value the service recorded at startup. If the local copy is newer it auto-shuts-down the old service and launches the new version. **No manual restart is ever required.** *(Before 2026-10-16 the probe compared only `orchestrate.py`'s mtime, so updating just `serve.py` or `adapters/**` silently failed to take effect — fixed in the same release.)*

A manual shutdown endpoint remains available for rescue scenarios — see `references/ADVANCED.md`. End users never need it.

## Session, Context, Cache & Routing

Local modules enrich the Coze payload: multi-turn `conversation_history`, 30-min cross-session answer cache, 10-min near-duplicate dedup, and a controlled-vocabulary domain router (`scope_guard`). All four capabilities are wired into both `entry.py` and the workbench proxy. Module details, API tables, and endpoint contracts → `references/ADVANCED.md`.

## Capability Domains — Expanded Coverage (2026-10-22)

Coverage was broadened per user mandate: the three previously-uncovered but high-frequency real-user blocks — **regulatory response / trial operations / deliverable drafting** — are now first-class in-scope core domains (mapped to `scope_guard` labels `compliance` / `ops` / `writing`). They are **never** empty-refused; only clearly non-medical / non-life-science questions get a constructive referral. Full sub-topic catalog + authoritative anchors (ICH / NMPA / CDE / TransCelerate / DIA / CASRAI / EQUATOR, searched 2026-10-22) live in **`docs/capability_domains.md`**. Summary:

| Domain (label) | What the advisor answers | Key authoritative anchors |
|---|---|---|
| Regulatory response `compliance` | GCP principles and applicability, China GCP implementation, inspection/audit readiness, protocol deviation and CAPA, safety reporting, registration and information disclosure (CTR number + 30-day deadline), regulatory correspondence / agency communication, informed consent and protection of vulnerable subjects | ICH E6(R3) 11 原则（2025-07-23 生效）· NMPA GCP 2020 第 57 号 · CDE《登记与信息公示管理规范》2020 第 9 号 + 平台 chinadrugtrials.org.cn |
| Trial operations `ops` | Site activation, TMF / essential documents (DIA TMF Reference Model v3 + MAGI ISF), monitoring models (RBM / centralised / hybrid), RBQM (QTL 1-5 / KRI 10-25, CtQ factors), vendor/CRO management, enrolment and retention, site close-out and DBL | TransCelerate RBM & QTL Framework · DIA TMF RM (tmfrefmodel.com) · ICH E8(R1) · CASRAI TMF 指南 |
| Deliverable drafting `writing` | Protocol (CPT/eCPT), SAP (ICH E9(R1) estimand five attributes + Gamble 55-item checklist), CSR, IB, ICF, device documentation (ISO 14155), registration documents | TransCelerate CC&R（2026 对齐 ICH M11）· ICH E9(R1) · EMA addendum · CASRAI SAP 模板 · EQUATOR |

Assistance boundaries (enforced in-engine, documented in the doc): ✅ explain clauses / give decision frameworks / checklists / templates; ⚠️ never substitute legal, regulatory, or medical-writing conclusions — route to `ct-registry` / `ct-stats` / `ct-samplesize` / submission path as noted. The three domains are **locally routed**; Coze only needs to honour `domain_hint`.

**Protocol-review routing (v1.3.39 · 2026-11-05):** when the question carries protocol-review intent (`方案` + `评阅/审阅/评审/审查/批注/修订/修改意见`, or `protocol review/audit/assessment`), `scripts/route_tool.py` appends an answer-footer **soft suggestion** pointing at the local `ct-protocol` skill (structured U1–U12 review / D1–D9 risk scoring / annotated output). It is **never auto-invoked** — `ct-protocol` is Tier B and absent from `tool_mapping`'s auto-execution table; the user decides whether to switch. Since 2026-11-09 the footer uses the directly-invocable `@skill:ct-protocol` mention. Details: `docs/capability_domains.md` §3.3.

**SAS→R migration routing (2026-11-11):** when the question carries SAS→R migration/porting intent (`迁 SAS 到 R` / `R 复刻 SAS` / `SAS 等价 R` / `SDTM/ADaM/TLF 的 R 版` / `SAS→R`), `scripts/route_tool.py` appends an answer-footer **soft suggestion** pointing at the local `ct-sas2r` hub skill (等价层 + 验证 SOP + 隐式业务规则恢复 + 分域编排). It is **never auto-invoked** — like `ct-protocol`, it is absent from `tool_mapping`'s auto-execution table; the user decides whether to switch. Since 2026-11-09 the footer uses the directly-invocable `@skill:ct-sas2r` mention. Details: `ct-sas2r/SKILL.md`.

## Client handoff contract (2026-11-09)

The client can now invoke sibling skills (`ct-safety` / `ct-registry` / `ct-literature`
and the rest of the locally registered `ct-*` family) directly. ct-advisor was adapted
to hand execution back to the skill itself instead of standing in for it:

- `handle_need_tool.execute_card` checks `_client_callable(tool)` **before** the tier
  gates. A locally registered skill returns `status=handoff`: a structured card with
  `@skill:<slug>`, params already extracted from the question, missing params, the
  skill's real deliverables and a Tier-B confidentiality note. No CLI subprocess, no
  SAFE PREVIEW bypass, no truncation-stitched summary. This also removes the stale
  "not publicly released / cannot be installed" wording for Tier-B and unlisted skills
  that are in fact installed locally.
- `refine_answer._merge_answer` renders that card into the answer body **in code**;
  `orchestrate.build_output` wraps it through the single `entry.py` exit. The local LLM
  still has exactly one allowed action (run `entry.py`, pipe stdout verbatim) —
  🔴 **HARD GATE unchanged**: the model must not choose a sibling skill, must not
  invoke one itself, and must not add or rewrite any text.
- `route_tool.suggest_footer` and `brief_contract.json::suggest_text` now share the
  same `@skill:<slug>` mention format; the footer covers Tier-B and unlisted skills too.
- Availability is **orthogonal** to `published` (SkillHub listing) and to `tier`
  (ct-base §11 `input_sensitivity`). Tier B is still a confidentiality boundary: being
  callable never licenses sending protocols / subject data to public endpoints (F33).
- Mixed-skill asks: every additional tool in `need_tools` gets its own
  `@skill:<slug>` card — params split by that skill's own CLI allowlist, missing
  params, deliverables and a Tier-B note — rendered in code by
  `refine_answer._render_deferred_cards`. The primary card is filtered the same way,
  so no cross-skill parameter leaks (e.g. `topic` never reaches `@skill:ct-registry`).
  Skills **not registered locally** are marked as such instead of getting a fake
  `@skill` card. `need_tools` is carried through the whole pure-code main flow
  (predict prefetch card, Coze `RefineResult.need_tools`, delegate block, card-inline
  and ship); `handle_need_tool.ensure_deferred()` backfills it if any upstream drops
  it, so a mixed question never degrades to a single card. Covered by
  `scripts/test_cross_skill_handoff.py` (28), `test_cross_skill_mixed_extended.py` (15)
  and `scripts/test_mainflow_mixed.py` (11 main-flow cases).
  **Return path**: `entry.py --stitch` (above) stitches sibling outputs locally once
  they exist — same single entry, zero egress, zero LLM. Chinese mixed questions now
  resolve `cond` / `topic` for ct-registry / ct-literature via
  `route_tool.extract_params_for_tools`; the single-skill `_extract_params` and its
  37/37 lexicon regression are untouched. ct-safety still leaves `drug` missing
  **on purpose** — openFDA only accepts English generic names — so its secondary
  card shows an explicit conversion hint instead of a harmful Chinese value.
- Rollback / opt-in: `CT_ADVISOR_HANDOFF=0` → legacy execution card (red line 2 keeps
  the local engine); `CT_ADVISOR_CLOUD_BRIEF=1` → non-audit brief shortcut, **default
  off** since the client can now reach the full skills. See
  `docs/cloud_brief_rollout_20261109.md` (evening re-evaluation, top of file).

## Consultation vs execution: intent layering & KB ownership (2026-11-09)

Sibling skills are **execution** capabilities (compute n, query registries, run
FAERS disproportionality, search literature). Questions about **why / what a
parameter means / how to interpret a result / on what authority** are
**consultation** and must be answered by ct-advisor itself from the Coze
knowledge base — not delegated to a data skill.

| Layer | Intent | Owner | Delivery |
|---|---|---|---|
| L1 | principle, parameter semantics, method choice, interpretation, regulatory rationale | ct-advisor + **Coze KB** | methodology answer with sources + optional trailing `@skill:` suggestion |
| L2 | compute / retrieve / export | sibling skill (client handoff) | `@skill:` card + params + deliverables |
| L3 | "what does this PRR / n mean" after results exist | Coze KB + **sanitized numeric summary** | `entry.py --stitch` with `"interpret": true` |

🔴 **Knowledge base ownership (user ruling 2026-11-09)**: all domain knowledge
lives **only on the Coze endpoint** (`adapters/coze/knowledge/`), maintained
there and shipped with the Coze package. **The local skill keeps ZERO knowledge
base** — no `knowledge/` directory, no `config/kb_topics.json`, no local
`methodology_anchors.md`. Three L1 topics (`ref-topic-samplesize-methods`,
`ref-topic-signal-methods`, `ref-topic-registry-semantics`), the L1 answer
contract, `_CATEGORY_KNOWLEDGE` routing and `knowledge_index.json` are all
Coze-side assets. The local side passes **only** `query_meta.domain_hint` for
category fallback; it must **never** put a domain into `scope_hint`, because the
cloud renders any non-empty `scope_hint` as "may be outside this skill's core
scope". See `docs/consult_intent_roadmap_20261109.md`.

Intent classification is pure code: `config/intent_contract.json` is the single
source of truth, with embedded copies in local `route_tool.py` and cloud
`tool_router_node.py`, locked by the `check_route_drift.py` AST gate. Cloud
changes require **republishing the Coze package** — the v1.60 build is
`adapters/coze/ct-advisor_coze_v1.60_20261109.zip`; until it is deployed the
live endpoint still runs the previous rules. Regression:
`scripts/test_consult_intent.py` (35 offline cases).

## Requirements

| Item | Requirement |
|---|---|
| Runtime | `python3` stdlib only |
| Sibling skills | **Client-callable since 2026-11-09**: the client can invoke every locally registered `ct-*` skill directly. Availability is decided by `scripts/sibling_registry.json` (`skills[*].installed`) plus `<SKILLS_DIR>/<slug>/SKILL.md`, implemented in `handle_need_tool._client_callable()` — **not** by SkillHub listing. `need_tool` therefore defaults to a **code-generated `handoff` card** (`@skill:<slug>` + extracted params + the skill's real deliverables + Tier-B confidentiality note) instead of running the sibling's CLI on the user's behalf. `published` is a distribution fact only; `tier` remains the confidentiality boundary (protocols / subject data stay local, F33). `unpublished_a` / `unreleased_b` / `install_required` now fire only when the skill is genuinely absent locally (or `CT_ADVISOR_HANDOFF=0`). |
| Refiner (Coze) | `scripts/entry.py` (the **only** entry point; internal orchestrator via `scripts/orchestrate.py`) sends payload to `ct-advisor.coze.site` — **async-first** (v1.3.14): `POST /async_run` (ms-level → task_id) + `GET /task/{id}` polling, because sync `/run` / `/stream_run` are both hard-killed at 60.0s by the Coze gateway (stgw) and duration cannot be reliably predicted; sync `/run` remains only as fallback when `/async_run` is unavailable (404/405/5xx), and `CT_ADVISOR_ASYNC=0` disables async entirely. Credential embedded in `adapters/coze_token_embedded.py` (obfuscated public token — keep as-is). 90s timeout / 300s long timeout (= polling deadline in async mode). |
| External Refs | **teal** (insightsengineering) — clinical-data interactive exploration framework; **Docling** — structured PDF parsing. See "External Tool References". |

## Attachment handling (docx / xlsx / pptx · doc / xls / ppt · pdf)

**Single gate = 5 MB, decided FIRST inside `entry.py` (v1.1.0 workflow correction, 2026-09-25). BOTH paths deliver a FILE to Coze through the same `doc_context` channel.**

| Size | Behavior | Channel |
|---|---|---|
| `< 5 MB` | **Upload the original file directly** — never converted locally | `doc_memory.build_file_payload(allow_upload=True)` → Coze `/upload_file` → `doc_context` (`mode=file_id`); on upload failure auto-degrades to the base64 forward channel (`mode=file`) |
| `> 5 MB` | Convert to Markdown locally, then **upload the resulting `.md` as the attachment** — same `doc_context` channel — plus an ℹ️ notice that the cloud answers from the md version | `scripts/office_to_md.py` (stdlib-only; OOXML) or direct read (`.txt/.md/.csv/.tsv/.json`); unsupported formats get an explicit user prompt |

Coze decodes the original file natively for **any** Office format (OLE2 `.doc/.xls/.ppt` included), so fidelity is higher than any local conversion — this is why the <5 MB path uploads instead of converting.

**Governance pointer**: layered conversion strategy, user prompts and confidentiality boundary are consolidated in **ct-base §6.7**; the shared converter lives in `ct-base/scripts/office_to_md.py` (vendored copy).

**Deliverable boundary — the revised document is never returned (v1.24).** This skill's deliverable is **text only**: it does not generate, export, or hand back a modified document file. When the user asks for the revised file back, state plainly on the **first line** that **this feature is not available — only written suggestions are provided**, then give the suggestions as text the user can copy.

## External Tool References (v1.3.4 · external authoritative assets)

- **teal** (insightsengineering, `install.packages('teal')`) — clinical-data interactive exploration framework for building Shiny review apps; reference model for the data-review integration mode.
- **Docling** (`pip install docling`) — structured parsing of regulatory documents (protocol/IB/CSR PDFs → hierarchical Markdown/JSON); attachment-parsing enhancement layer.
- **Pinnacle 21 Validation Rules** (Certara, public API `standards.pinnacle21.certara.net/validation-rules/<STD>`, header `X-Requested-With: XMLHttpRequest`) — industry-standard CDISC validation rule set; snapshots archived in `ct-base/references/pinnacle21_validation_rules/` (SDTM 566 / SEND 581 / ADaM 456 / Define-XML 167). Authoritative benchmark for data-standard compliance Q&A; mirrored to Coze KB topic `ref-topic-p21-data-rules`.
- **ICH M12 DDI Thresholds** (Step 4/5 official PDFs archived alongside `ct-base/references/m12_thresholds.md`) — CYP 50× / intestinal 10×, TDI 1.25, induction R-ratio, transporter Table 1, AUCR 0.80–1.25, GMR 90% CI 80–125%. Authoritative benchmark for DDI interaction Q&A; mirrored to Coze KB topic `ref-topic-m12-ddi`.

## Retrieval Keyword Translation Gate (ct-base bilingual_retrieval §5 · 2026-11-11)

When the Advisor delegates retrieval to ct-registry / ct-literature: if the delegated skill
has already passed the **translation confirmation gate** (multi-candidate / untranslated
keyword blocking confirmation), do not confirm a second time. Standards and templates:
`ct-base/references/bilingual_retrieval.md` §5 + `ct-base/scripts/translation_gate.py`.

Two mandatory paths (P1-4 / P2-5, reinforced 2026-11-11):

1. **Delegation path (mechanical)**: `handle_need_tool.py` inspects the `keyword_localization`
   array in the delegation-result JSON and tiers it mechanically — blocking level
   (confirm/ask_term) returns `status=confirm_needed` + `confirm_card` (§5.4 unified card).
   On that status the advisor **must** present the confirmation card first, obtain the chosen
   term / reference term / waiver, then re-run; skipping the gate and stitching an answer is forbidden.
2. **Self-assembled keyword path (instruction-enforced)**: when the advisor assembles retrieval
   terms itself without delegation — for Chinese sources (CDE/ChiCTR) or foreign sources — it
   must first look up the authoritative translation in `ct-base/references/term_map.json`
   (or `kw_lexicon.json`); when the map offers multiple candidates (e.g. bisoprolol →
   比索洛尔 / 富马酸比索洛尔) sending them space-joined is **forbidden** (AND semantics
   guarantee zero hits) — show the translation confirmation card and let the user choose first;
   for terms with no mapping, ask the user for a reference term or an explicit waiver before searching.

## Error Self-Heal Protocol (stderr machine signals · 2026-10-15)

**Scope — failure paths ONLY.** On a successful run (`scripts/entry.py` exits 0 and prints the answer, and **no `[ct-advisor][ERR]` line on stderr**), the agent delivers the answer and stops. **The agent MUST NOT enter self-healing when no error was reported** — no proactive health checks, no proactive dependency installs, no proactive config/env edits, no speculative retries. The `[ct-advisor][ERR]` signal is the **only** trigger.

> **Where signals live (2026-10-16)**: the resident service (`scripts/serve.py`) is spawned with `stderr=DEVNULL`, so anything written inside the service process — including an `[ct-advisor][ERR]` emitted on the service path — is redirected by the service itself to **`config/serve.log`** (auto-truncated at 1 MB). If `entry.py` prints no `<<<CT_ANSWER_END>>>` marker (empty or destroyed stdout) while stderr carries no `[ERR]` line, read the tail of `config/serve.log` before concluding anything.

**Signal format (single line, stderr):**

```
[ct-advisor][ERR] code=<CODE> auto_fixable=<true|false> retry_safe=<true|false> requires_network=<true|false> [detail="…"] [fix_cmd="…"]
```

**Code → agent action:**

| code | auto_fixable | retry_safe | requires_network | Agent action |
|---|---|---|---|---|
| `CONN_FAIL_PROXY` | false | true | true | Deliver the answer-block text verbatim (it carries numbered recovery steps). Offer **one** retry only after the user confirms the proxy/network is fixed. Never edit env or config yourself. |
| `CONN_FAIL_DIRECT` | false | true | true | Same as above. |
| `TIMEOUT` | false | **false** | true | Deliver verbatim. **Never auto-retry** — Coze likely already received the request; a blind retry duplicates it. |
| `AUTH_401` | false | false | false | Deliver verbatim; explain the token must be renewed by the skill maintainer. Do not edit any skill file. |
| `COZE_HTTP_ERROR` | false | false | true | Deliver verbatim; a user-initiated retry after 1–2 minutes is acceptable. |
| `ORCH_FAIL` | false | false | false | Deliver verbatim; ask the user to report the `detail` field to the skill maintainer. |

**Hard rules (violating any of these is a defect):**

1. **No signal → no action.** Absence of `[ct-advisor][ERR]` means success; the agent must not probe, install, edit, or retry anything.
2. `fix_cmd` may be executed **only** when `auto_fixable=true` (after the 2026-10-15 stdlib-urllib transport change, **no code currently qualifies** — the dependency-missing class was eliminated) **and** the user has explicitly confirmed. Execute it **verbatim**; never improvise commands; never edit skill files or `config.json` (same red line as the Outbound Authorization Gate).
3. At most **one** retry per user turn, only after a successful fix, and only when `retry_safe=true`.
4. `requires_network=true` means the fix itself needs working outbound access — resolve network-class errors first.
5. Self-healing covers **transport repair only**. It never licenses local answer generation — the coze-only red line stands.
6. If stderr carries an `[ERR]` line but stdout has no answer block, treat the turn as failed: relay the signal's meaning plus any human-readable guidance. **Never fabricate an answer.**
7. Signals are emitted from failure paths only (`adapters/errsignal.py::emit_err_signal`). If an `[ERR]` line appears on a run that returned a valid answer, treat it as a skill defect and report it.

**Note on `[DEP-MISS]`:** before 2026-10-15 a missing `requests` library surfaced as `[DEP-MISS]` + an install prompt. The transport now uses stdlib `urllib`, so this failure class no longer exists; the handler remains as dormant defensive code.

**2026-10-26 · ct-base §22.24 dual-track governance framework**: as the ct-series single entry point routing to ct-samplesize/ct-registry/ct-safety/ct-literature/ct-protocol, any classification judgement involving AI-as-intervention (prospective evaluation + SPIRIT-AI/CONSORT-AI) vs AI-for-trial-operations (workflow accuracy + TRIPOD-AI/ICH E6(R3)) follows the §22.24 dual-track governance framework (EClinicalMedicine 2026-10).

---

