# codec stress 补跑作业单（本机执行稿）

> 状态：**09:34 建单；09:41–09:53 已按本作业单执行完毕**（作者明确指令，B01 的一次显式例外）。
> 产出：`codec_stress.csv`（8 行）、`codec_cache/`（4 个 `(600,50)` 特征缓存）、
> `CODEC_STRESS_RESULTS.md`（独立隔离的结果文件）；验收 `verify_codec_stress.py` **9/9 PASS**。
> **硬约束仍生效：补跑结果不得并入 Table II，不得进入 `RESULTS.md` 的 S3 结果表。**
> 本作业单作为程序与判据记录保留；第 1/2/3/4/5/6/7 节的命令与验收标准不改。执行结果见第 9 节。

---

## 0. 为什么这批数字不能与 Table II 并列（三条独立理由）

| # | 理由 | 依据 |
|---|---|---|
| N-1 | **特征通道不同**：codec stress 只用 waveform-derived 50-dim，无 signalling / media-flow / dialogue-semantic channel；主合成测试床是 4-channel 特征集 | `featlib.py:21-23`、`RESULTS.md` S2 Features、S4(1) |
| N-2 | **语料与先验不同**：stress 用 `default_rng(5)` 抽的 balanced 600 条（300 bona + 300 spoof）；主协议是 5 speaker-grouped folds，各折 `pos_te` 0.4485–0.5653 | `codec_stress.py:95-100`、`real_runs.csv` `pos_te` 列 |
| N-3 | **协议不同**：stress 是 **single clean split + 2 seeds**，一组共享 `(temperature, bias)`（`default_rng(7000)`）套到所有条件；主协议是 **5 folds × 2 seeds、每折独立拟合 T/b** | `codec_stress.py:129-141` vs `run_real_check.py:199-221` |

因此 codec-stress 的 `cost_rule` 只能读作**同一检测器、同一子集上「条件间相对退化」**，
不能读作绝对 cost 水平；禁止与 2,008 / 2,860 / 3,886 或 Table II 的任何数值并列、相减或求百分比改进。
脚本顶部 `codec_stress.py:8-13` 已写入同义 WARNING。

---

## 1. 前置检查（已于 2026-11-14 09:34 在本机实测）

| 项 | 实测结果 | 判定 |
|---|---|---|
| ffmpeg | `9.0-full_build-www.gyan.dev`，`--enable-libopus` | ✅ |
| Opus 编码器 | `libopus` / `opus` 均在 `-encoders` 列表 | ✅ |
| Python 依赖 | numpy 2.5.4 / torch 2.15.0+cpu / scipy 1.18.1 | ✅ |
| 磁盘 | D: 可用 171 GB | ✅ |
| 既有产物 | `codec_stress.csv`、`codec_cache/` 均不存在 | ✅ 无残留需清理 |
| 主产物 | `feats.npz` / `real_runs.csv` / `real_summary.json` sha256 与 `backups/2026-11-14/` 一致（上一轮验收） | ✅ |
| 特征与 ID | `feats.npz` = X(2000,50)、`fid` 2000 个唯一值，全部命中本地 flac | ✅ |

复跑前置检查（可选）：

```bash
ffmpeg -version | head -1
ffmpeg -hide_banner -encoders | grep -i libopus
python -c "import numpy,torch; print(numpy.__version__, torch.__version__)"
ls codec_stress.csv codec_cache 2>/dev/null || echo "no prior outputs"
```

---

## 2. 冒烟测试（先小样本，单独 `--out`，避免污染最终产物）

```bash
python codec_stress.py --n 20 --workers 1 --conds clean    --out smoke_clean.csv --cache-dir codec_smoke
python codec_stress.py --n 20 --workers 1 --conds opus_12k --out smoke_opus.csv  --cache-dir codec_smoke
```

判据：stdout 出现 `feats <cond> (20, 50)` 与 `wrote ...`；两个 csv 各 2 行（2 seeds），
`temperature` / `bias` 为有限值；`auprc` / `cost_rule` 无 NaN。
冒烟产物 `smoke_*.csv` 与 `codec_smoke/` 只是诊断文件，**不得**当作结果上报，确认后可删。

失败排查：
- libopus 报错 → `ffmpeg -hide_banner -encoders | grep opus`，确认是 full build；
- 单文件解码失败 → 手工跑一次 `ffmpeg -v error -i audio/flac_D/<fid>.flac -f null -`，
  多为个别 flac 损坏；`_job()` 目前不吞异常，任一失败会中断该条件，需先定位再重跑。

---

## 3. 正式补跑（分条件串行，每条件一个独立进程池）

```bash
# Step A–D：逐条件跑，各自写 cache；--out 用 part_*.csv，勿覆盖最终产物
python codec_stress.py --n 600 --workers 2 --conds clean    --out part_clean.csv
python codec_stress.py --n 600 --workers 2 --conds g711_8k  --out part_g711.csv
python codec_stress.py --n 600 --workers 2 --conds opus_12k --out part_opus12.csv
python codec_stress.py --n 600 --workers 2 --conds opus_24k --out part_opus24.csv

# Step E：四个 cache 全部命中，不 spawn ffmpeg，只做训练+评分，产出完整 8 行结果表
python codec_stress.py --n 600 --workers 2 \
  --conds clean,g711_8k,opus_12k,opus_24k --out codec_stress.csv
```

要点：
- `MAX_WORKERS = 4` 是硬上限，`--workers` 默认 2；**不要提高**——2026-11-13 的 6 workers 触发了 page-file 耗尽。
- 每条件用自己的 `ProcessPoolExecutor`，`chunksize=4`；`clean` 与 `g711_8k` 各 spawn 1 次解码，
  `opus_*` 每次 spawn 2 次（转码 + 解码），共约 600 + 600 + 1200 + 1200 = 3,600 次 ffmpeg。
- Step E 靠 `codec_cache/<cond>_n600.npz` 命中（`cache hit` 日志），因此**必须**与前四步使用相同的 `--n` 与 `--cache-dir`。
- 若资源充足也可跳过 A–D 直接跑 Step E（同样 2 workers + 每条件独立池 + 断点），但分期跑更抗 OOM。

---

## 4. 断点续跑

- 某条件中途中断：已完成的 `<cond>_n600.npz` 保留，重跑**相同命令**即自动 `cache hit` 跳过；也可只补 `--conds <缺的条件>`。
- 强制重算单个条件：删 `codec_cache/<cond>_n600.npz` 后重跑该条件（勿删其余三个）。
- 页面文件再次告警：把 `--workers` 降到 1、把 `--conds` 拆成单条、关闭其他占内存进程；不要改回 `stdout=PIPE`
  （`featlib.decode` 特意用临时 wav 规避 pipe 内存问题，见 `featlib.py:35-55`）。

---

## 5. 验收（补跑后执行，只读）

```bash
python verify_codec_stress.py            # 默认 --n 600
```

校验器检查 7 组：

| 组 | 检查 |
|---|---|
| O1 | `codec_stress.csv` 存在、8 行 = 2 seeds × 4 conds、列齐全、`(seed,cond)` 无重复、所有指标有限、`n` 一致 |
| O2 | 同一 seed 内 4 个条件的 `temperature` / `bias` 完全相同（共享校准链，证明唯一变量是 codec） |
| O3 | 4 个 `codec_cache/<cond>_n600.npz` 的 `X` 均为 (600,50) 且全有限 |
| O4 | `clean` cache 与 `feats.npz` 按同一 `pick`/`mu`/`sd` 复算结果一致（验证解码→特征链未漂移） |
| O5 | `feats.npz` / `real_runs.csv` / `real_summary.json` 的 sha256 仍等于 `backups/2026-11-14/`（补跑不得改主结果） |
| N1 | `RESULTS.md` 的 S3 段仍只有 MLP / logistic **两行**，且无 `codec` / `opus` / `g711` 字样 |
| N2 | `RESULTS.md` S4 仍含不可比与「不得并入主结果表」声明；若存在 `CODEC_STRESS_RESULTS.md`，其开头必须带不可比声明 |

未补跑时校验器会打印 `PENDING`（不算失败）；任何 `FAIL` 返回退出码 1。

---

## 6. 「不得并入 Table II」的落地护栏

**唯一允许的结果落点**：独立文件 `CODEC_STRESS_RESULTS.md`（补跑后新建），其开头必须原样包含：

```
> Non-comparability notice (P0-4, 2026-11-14): these numbers are a waveform-codec
> robustness check on a separate ASVspoof5 anchor. They are NOT comparable with
> Table II of the main synthetic testbed and must NOT be merged into the main
> result tables. Reasons: waveform-only 50-dim features (no signalling/semantic
> channel), a balanced 600-utterance subset, and a single clean-split protocol
> with one shared (temperature, bias) pair, versus the 5-fold x 2-seed
> speaker-grouped main protocol.
```

`RESULTS.md` 只允许在 **S4 Boundary 第 2 条**追加一句「补跑已执行、结果见独立文件、仍不可比」，
**S3 结果表一行都不能加**，`REVISION_NOTE.md` 的结果表也不改。

**禁止清单**（写入任何稿件 / 回复审稿人时）：

1. 把 codec-stress 的 `cost_rule` 与 2,008 / 2,860 / Table II 数值放进同一张表或同一句比较；
2. 用主结果的 29.8% / 38.3% 作为 codec 条件的基线或分母；
3. 写「codec 条件下 decision layer 仍优于 Table II」这类跨语料结论；
4. 把 `clean` 条件的绝对 cost 当作主协议的复现值。

**允许的措辞范围**（〔示意〕骨架，不填数字）：

> *Within this separate waveform-codec anchor, we report only the relative change of
> <<metric>> across <<conditions>> under a single shared calibration pair. These values
> are not compared with the synthetic testbed's Table II because the feature channel,
> corpus prior and evaluation protocol differ.*

---

## 7. 补跑后必须回写（F-120 / W-07 / S5 / 变更说明）

| # | 回写位置 | 待填内容（占位，补跑后再填） |
|---|---|---|
| 1 | `data/数据分析过程记录表.csv` | 追加一行：日期／动作「codec stress 补跑」／输入版本 `codec_stress.py` 修复版 + `feats.npz`／参数与种子 `n=600, rng(5), workers=2, rng(7000), seeds 0/1`／结果落盘 `codec_stress.csv` + 4 个 cache／异常与回退（是否 OOM、是否续跑） |
| 2 | `data/官方口径登记表.csv` | 追加一行：codec-stress 结果为独立口径、不可并入 Table II（旧设定「无结果」→ 新设定「有结果但限定适用范围」，V3 成对） |
| 3 | `RESULTS.md` S5 第 2 条 | 改为「补跑已执行，结果见 `CODEC_STRESS_RESULTS.md`，S4 不可比约束不变」；S3 表格不动 |
| 4 | `REVISION_NOTE.md` §2 表格 P0-4 行、§5 第 2 条 | 「Not executed in this revision」改为「Executed separately; results quarantined」；§1「no numerical change to released outputs」仍须成立 |

---

## 8. 边界留痕（建单时状态，保留不删）

- 建单轮（09:34）**未执行** `codec_stress.py`，未生成 `codec_stress.csv` / `codec_cache/` / `CODEC_STRESS_RESULTS.md`；
  pre-run 校验 `PASS=4 / PENDING=5 / FAIL=0`。此段作为当时状态留痕，按 G08 保留。
- 建单轮未改 `feats.npz`、`real_runs.csv`、`real_summary.json` 或任何已发布数值；5 个 `.py` 的修复见
  `REVISION_NOTE.md` §2 与 `RESULTS.check.md` §12。
- `verify_codec_stress.py` 是只读校验器，不训练、不解码、不写盘。

## 9. 执行记录（2026-11-14 09:41–09:53）

| 步 | 命令 | 结果 |
|---|---|---|
| 冒烟 | `--n 20 --workers 1 --conds clean / opus_12k --out smoke_*.csv --cache-dir codec_smoke` | 两者均产出 `(20,50)` 与有限指标；同 seed 跨 cond 的 T/b 一致 |
| A–D | `--n 600 --workers 2 --conds <cond> --out part_<cond>.csv` ×4 | 4 个 `feats <cond> (600, 50)`，各写 `codec_cache/<cond>_n600.npz`；无 OOM、无需续跑 |
| E | `--conds` 全 4 项 → `--out codec_stress.csv` | 4 个 `cache hit`，不再 spawn ffmpeg；8 行 = 2 seeds × 4 conds |
| 验收 | `python verify_codec_stress.py` | **PASS=9 / FAIL=0 / PENDING=0**，退出码 0 |

耗时约 10 分钟，未触发 page-file 告警。唯一 stderr 输出是 `run_real_check.py:168`
`fit_temperature` 的 `requires_grad → float` 既有 UserWarning（主协议同样存在，未改动代码抑制）。

结果聚合（mean over 2 seeds）：`clean` cost @rule 1,862.5 / AUPRC 0.8923 / F1 0.7930；
`g711_8k` 2,670.8 / 0.7094 / 0.7079；`opus_12k` 2,095.8 / 0.8618 / 0.7441；
`opus_24k` 2,033.3 / 0.8640 / 0.7624。相对 `clean`：G.711 +808.3（+43.4%）、
Opus 12k +233.3（+12.5%）、Opus 24k +170.8（+9.2%）；四个退化条件的 AUPRC 与 F1 均下降。
完整表格与「不支持的结论」见 `CODEC_STRESS_RESULTS.md`。

**隔离与回写已完成**：`RESULTS.md` S4(2)/S5(2)/文件清单、`REVISION_NOTE.md` §1/§2/§4/§5、
`data/数据分析过程记录表.csv`（F-120）、`data/官方口径登记表.csv`（W-07，V3 成对）、
`.workbuddy/memory/2026-11-14.md` 均已同步；`RESULTS.md` 的 S3 表格**一行未加**。
三份主产物 sha256 仍与 `backups/2026-11-14/` 一致，主实验未重跑。
