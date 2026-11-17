# RESULTS 边界诚实＋一致性核查｜本轮唯一交付物

- 组名：**语义攻击·论文作战组**（返修／补充实验轮沿用此组名）
- 轮次：2026-11-13，过程确认轮之后的首个交付轮
- 交付物定义：对 `RESULTS.md` 的边界诚实＋一致性核查报告，附可直接贴进稿件的补充实验段〔示意〕骨架与待补清单
- 边界：不改数据、不代跑实验、不代写论文正文（rules 二·1 / B01 / B02）；codec stress 的执行由作者本机完成

## 一、派单行（RD6 五要素）

| 环节 | 席位 | 收 | 交回 | 验收条号 |
|---|---|---|---|---|
| X-05 数据分析 | 谢析数 | 核 10 runs 数字自洽与结论可追溯、登记可复现过程记录 | 过程记录表＋结论句回查表＋结果报告骨架〔示意〕＋待补证据清单 | F-118／F-120／K-303／三·1 |
| X-09 格式核查 | 严校稿 | 对 `RESULTS.md` 做术语／编号／单位／图表四组一致性比对与边界诚实段体检 | 一致性核查报告（两列比对）＋待改条目清单 | C-100／C-300／C-400／三·2 |

主持人不改写两席专业结论，只做汇编与转呈；分歧按 G04 仲裁留痕。

## 二、总编排已核项（不属任何席位的专业结论）

| # | 核对动作 | 结果 |
|---|---|---|
| C-1 | `real_runs.csv` 结构 | 20 行 = 5 folds × 2 seeds × 2 models，`(seed,fold,model)` 组合各一次，无重复、无缺格 |
| C-2 | Δ 自洽 | `real_summary.json` `mlp.delta.mean` = 852.74，等于 `cost05` 2860.34 − `cost_rule` 2007.60 |
| C-3 | 29.8% 口径 | 852.74 / 2860.34 = 29.81%，与 `RESULTS.md:20` 一致 |
| C-4 | paired bootstrap CI | `delta_ci95` = [665.3, 1036.1]，与 `RESULTS.md:10` 的 [665, 1036] 一致 |
| C-5 | 60% prior 重加权 | `exp60` 2337.0 → 1583.0，与 `RESULTS.md:14` 一致 |
| C-6 | 断点 | 工作区无 `codec_stress.csv`；`RESULTS.md:18` 记 host page-file 耗尽于 ffmpeg 并发 spawn |
| C-7 | speaker 口径 | `protocols/ASVspoof5.dev.track_1.tsv` 全量 140,950 行、unique speaker = **785**（与 `RESULTS.md:3` 一致）；但 `feats.npz` 的 `spk` 字段 unique = **628**，即抽样子集覆盖的 speaker 数。二者所指不同，报告未区分 → 已转呈两席判定 |
| C-8 | 抽样池 | `audio/flac_D` 实际含 47,400 条 flac，非 dev 全集 140,950；`RESULTS.md:3` 写的 shard 名为 `flac_D_aa`，与实际目录名 `audio/flac_D` 不一致 → 已转呈两席判定 |
| C-9 | 攻击族分布 | `feats.npz` 的 `attack`：A09–A16 各 125、bonafide 1000，共 9 个标签；`X` 形状 (2000, 50)；与 `RESULTS.md:4-5` 一致 |
| C-10 | 抽样方式 | `extract_feats.py:43-59` 用 `default_rng(2026)` 按文件名排序后 shuffle，bona 取前 1000、每攻击取前 125；**非按 speaker 分层** → 与 5 speaker-grouped folds 的可复现性表述是否需交代，已转呈 X-05 判定 |

## 三、总编排盘点已登记风险（供两席核对，未改代码）

- **R1** `codec_stress.py:86-94` 用 raw logits → sigmoid 直接套 `THR_RULE=0.2`，缺主协议 `run_real_check.py:210-212` 的 temperature+bias calibration；阈值语义不等价，stress 结果不可与 Table II／主结果直接并列。
- **R2** `run_real_check.py:162-170` `fold_split()` 是只有 `pass` 的占位死代码（main 未调用），保留易误用。
- **R3** `RESULTS.md:20-22` 已写明 corpus 与 feature channel 不同、绝对 cost 与 Table II 不可比；属边界诚实，建议保留。

## 四、谢析数（X-05）回件

> 原样转呈，主持人未改写任何专业结论。核查方式声明：只读，未写盘、未执行实验脚本，仅复核 csv→json 聚合算术；回查日期 2026-11-13。

**【1】过程记录表（数据→特征→切分→校准→评估→聚合）**

① **数据** — 输入：`protocols/ASVspoof5.dev.track_1.tsv`（140,950 行）、`audio/flac_D`（47,400 条 flac）。脚本 `extract_feats.py:7-8,11-20,41-60`。参数：`default_rng(2026)`、`n_bona=1000`、`per_attack=125`、`workers=10`。产物 `feats.npz`（X(2000,50) float64 / y / spk / attack / fid；X 全有限）。异常：报告 L3 写 shard `flac_D_aa`，脚本 AUDIO 为 `…\audio\flac_D`；抽样池 47,400 ≠ 协议全量 140,950；报告 L3「785 speakers」为协议全量 unique speaker，`feats.npz` 的 `spk` unique=628（子集覆盖数），切分按 628 分组，二者层级不同且报告未区分 → 仅登记数据事实，口径判定转呈。原始只读=协议与 flac；派生可再生=`feats.npz`（seed 2026 + 同目录内容）；2,000 条 fid 选样清单未单独落盘。

② **特征** — 输入：解码后 waveform。脚本 `featlib.py:25-45 decode`（ffmpeg → 16 kHz mono PCM）、`:48-77` 滤波组/DCT、`:80-106 features`；`extract_feats.py:23-29,82-83`。参数：SR=16000、N_FFT=512、HOP=160、N_MELS=40、fmax=7600；MEL_GROUPS=linspace(0,40,26) → 25 组；MFCC 取 2..16 共 15 维；50 维 = 10 + 25 + 15；无随机种子。产物 `feats.npz["X"]`。异常：`featlib.py:3-9` 字典声明第 4–7 维为「centroid mean/std, spectral flux mean/std」，但 `features()` 的 `:96` 与 `:102` 第 6、7 维为同一 flux mean 计算式，未见 flux std 实现 → 字段字典与脚本实现不一致（有效维数需复核）。报告 L5 未细化到 std，不构成报告口径直接矛盾；派生字典回查缺口列入待补。本席只登记，不改特征设定。

③ **切分** — 脚本 `run_real_check.py:185-195`（内联，main 内）；`fold_split():162-170` 具名函数未调用。参数：`seeds=2`、`folds=5`、`default_rng(1000+seed)`、按 `np.unique(spk)` 分 5 组、标准化 mu/sd 取训练折、`train_model` 种子 `seed*100+k`。产物：`n_te`/`pos_te` 落 `real_runs.csv` 第 4–5 列；无独立切分索引文件。异常：报告 L6「5 speaker-grouped folds × 2 seeds」与内联实现一致；但 `fold_split()` 为只有 `pass` 的占位死代码、main 未调用，按函数名回查会落空 → 复跑指向 `main():185-192`。te/tr/cal/fit 索引未落盘。

④ **校准** — 脚本 `run_real_check.py:199-205`（15% holdout）、`:147-159 fit_temperature`、`:210-212`（T,b → p）、`:213-215`（isotonic 对照）。参数：`default_rng(7000+seed*10+k)`；`ncal=max(64, int(0.15*len(Xtr)))`；LBFGS lr=0.5 / max_iter=80；`p=sigmoid(z/T+b)`。产物：p / p_iso 不落盘（仅内存）；`ece`/`ece_iso`/`cost_iso` 落 csv 第 8、14、15 列。异常：报告 L6「15% calibration holdout」在实现中为 15% 且有 64 条下限 → 口径未明示（非矛盾，属参数登记缺项）。另：`codec_stress.py:86-94` 评分链为 raw logits→sigmoid→THR_RULE，缺 `:210-212` 的 T+b，与主协议不同源；该分支 `RESULTS.md:17-18` 记未跑完（page-file space），无产物。若补跑产出数值须另立派生口径登记，设定偏离需请示苏决批注，超出本席。

⑤ **评估** — 脚本 `run_real_check.py:17-75`、`:217-234`、`:238-243`。参数：`C_FP=5.0`、`C_FN=20.0`、`THR_RULE=0.2`；`pred05=p>=0.5`、`predr=p>=0.2`、`prediso=p_iso>=0.2`；`exp60` prior=0.60、`exp22` prior=`float(yte.mean())`；epochs=40、Adam lr=2e-3、batch=128、Dropout 0.1。产物 `real_runs.csv`（20 行 = 10 mlp + 10 lr，20 列）。异常：csv 第 18–19 列 / json 的 `exp22_05`、`exp22_rule` 实际先验为各折实测正例率 `yte.mean()`（`pos_te` 各行 0.4485–0.5653），非固定 0.22 → 派生字段名与取值口径不一致，命名规则待补。`codec_stress.py` 未跑完，无对应结果文件。

⑥ **聚合** — 脚本 `summarise.py:4-12`（按 model 分组，st.mean / st.pstdev）、`:14-24`（paired bootstrap）、`:27-28` 写 json。参数：14 个 keys；sd=`st.pstdev`（总体，ddof=0）；bootstrap `random.seed(11)` / 4000 次重抽 / d=cost05−cost_rule 仅取 mlp / CI 分位 0.025/0.975。产物 `real_summary.json`（mlp/lr 各 14 键 mean/sd/n=10；`delta_ci95=[665.3,1036.1]`）。异常：本席只读复核 csv→json 的 14 键 × 2 模型 mean/sd 全部一致。报告 L13 写「standard deviation」而实现为 pstdev（总体，ddof=0），bootstrap 种子 11 / 4000 次 / CI 仅覆盖 mlp 未落报告 → 口径未明示。**报告 L11 logistic ECE = 0.087 (0.019) 与 `real_summary.json` `lr.ece.mean=0.077240`（sd 0.018685→0.019）不一致；`lr.ece_iso.mean=0.082315`、`mlp.ece_iso.mean=0.086127` 亦无一为 0.087 → 回查不到一致落盘字段，标「待补证据」**。报告 L20「29.8%」为派生比值 852.7355/2860.3400 = 29.812%，未落盘为字段。报告 L14「2,337 → 1,583」对应 `mlp.exp60_05.mean=2337.0158`、`mlp.exp60_rule.mean=1582.5178`（取整为 1,583），可回查。

派生集命名与登记说明：原始只读＝`protocols/*`、`audio/flac_D`；派生可再生＝`feats.npz`←`extract_feats.py`(seed 2026)、`real_runs.csv`←`run_real_check.py`(seeds=2/folds=5)、`real_summary.json`←`summarise.py`(seed 11)、`RESULTS.md`←人工汇总。本工作区未见 `data/数据分析过程记录表.csv` 与 `data/官方口径登记表.csv`，故 W-07「登记在先、入库在后」与 F-120 六列流水尚未落表；本轮以「文件:行号／json 字段名／csv 列名」替代流水行号。三处已登记风险的 X-05 视角：R1→见④（不同源校准链）；R2→见③（占位死代码未被 main 调用）；R3→`RESULTS.md:20-22` 为已登记边界，数值锚点 `mlp.cost_rule.mean=2007.6045`，机制表述不属本席。

**【2】结论句回查表（RESULTS.md 抽 5 句）**

| 句 | 结论句 | 回指位置 | 判定 |
|---|---|---|---|
| C1 | L14「Expected cost re-weighted to the paper's 60% attack prior: 2,337 → 1,583 per 1,000」 | `mlp.exp60_05.mean=2337.0158`、`mlp.exp60_rule.mean=1582.5178`；csv `exp60_05`/`exp60_rule`；`run_real_check.py:230-231`；`summarise.py:5-6` | 可回查（1,583 为 1582.5178 取整） |
| C2 | L20「on real speech the decision layer cuts cost by 29.8%」 | `mlp.cost05.mean=2860.3400`、`mlp.cost_rule.mean=2007.6045`、`mlp.delta.mean=852.7355`；csv `cost05`/`cost_rule`/`delta` | 可回查（29.8% = 852.7355/2860.3400 = 29.812%，派生比值、未落盘，需附计算式） |
| C3 | L20-21「while F1 falls slightly」 | `mlp.f1_05.mean=0.77031` → `mlp.f1_rule.mean=0.75930`（下降）；`lr.f1_05.mean=0.67603` → `lr.f1_rule.mean=0.68620`（上升，见 L11 表内 0.676→0.686） | **部分可回查**——MLP 方向成立、lr 行方向相反；句子适用范围的限定属写作/统计席，本席不下结论 |
| C4 | L21「i.e. the same qualitative result as the simulation」 | 工作区内未见仿真结果文件、Table II 数值或论文定位；仅命中 `RESULTS.md:21` 与 `codec_stress.py:6` 的文字提及 | **待补证据** |
| C5 | L21-22「the absolute level of cost (~2,000 per 1,000 calls) is not comparable to Table II, because the corpus and the feature channel differ」 | ~2,000 回查到 `mlp.cost_rule.mean=2007.6045`、csv `cost_rule`；feature channel 差异回查到 `RESULTS.md:5`、`featlib.py:11-13`；「Table II」在工作区无对应文件或定位 | **部分可回查 + 待补证据**（Table II 数值与出处） |

附注：`RESULTS.md:11` logistic ECE=0.087 在 json 中回查不到一致字段，已列入【1】⑥ 与【4】D2；本席只标回查缺口，不作一致性判定。

**【3】结果报告骨架〔示意〕**（每段仅一句功能句，不含结论数字、不代写正文）

- **S1 动机**：承担「在真实语音锚点上复核 decision layer 相对 0.5 阈值」的问题设定与对照对象登记，不承载数值与机制判断。
- **S2 数据协议**：承担语料、子集、特征、切分、校准、代价与阈值全部可复跑参数及其落盘位置的逐行登记。
- **S3 结果**：承担按检测器与指标陈列落盘数值、离散度与区间的表格，只报数值与区间、不含解读句。
- **S4 边界**：承担语料与特征通道差异、未跑完分支、不等价评分链等适用范围限定项的列示。
- **S5 待补**：承担缺项、补录件与所解锁段落的逐条编号登记，与流水行号一一对应。

**【4】待补证据清单**（编号｜缺什么｜补哪样→解锁哪一段）

| 编号 | 缺什么 | 补哪样 → 解锁哪一段 |
|---|---|---|
| D1 | 仿真结果、Table II 数值及其出处（表号/页码/版本）不在工作区 | 补「仿真结果表或 Table II 定位 + 对应数值 + 版本」→ S1 动机、C4 定性对照回查、S4 不可比句的外部锚点 |
| D2 | 派生数字与表内数字无落盘对照：29.8% 为 delta/cost05 派生比值未落盘；L11 的 0.087 在 json 中无一致字段（候选 `lr.ece.mean=0.077240`、`lr.ece_iso.mean=0.082315`、`mlp.ece_iso.mean=0.086127`） | 补「派生计算式登记行 + 表内数值↔json 字段对照行」→ S3 逐格倒查与 C2 精确回查 |
| D3 | 原始分片标识与抽样池未登记：报告 shard `flac_D_aa` 与脚本 `audio\flac_D` 不一致，抽样池 47,400 ≠ 协议全量 140,950，2,000 条 fid 选样清单未单独落盘 | 补「原始分片清单 + seed 2026 下 fid 选样落盘列表」→ S2 数据协议与 `feats.npz` 复跑。口径判定不属本席，转呈 |
| D4 | 说话人层级口径未区分：协议全量 unique speaker=785、`feats.npz` spk unique=628 | 补「corpus-level / subset-level 各一行定义 + 切分按 628 分组的登记行」→ S2 切分参数回查。判定不属本席 |
| D5 | 50 维字段字典与实现对照缺行：`featlib.py:3-9` 声明 flux std，`:96/:102` 实现为 flux mean 重复 | 补「逐维字典↔实现对照行（含重复维处置决定）」→ S2 特征段；若涉改特征设计，超出本席，交总编排转设计席与苏决批注 |
| D6 | 聚合参数未完全登记：`summarise.py:11` 用 `st.pstdev`（总体，ddof=0）、`:16-24` bootstrap seed=11 / 4000 次 / 仅 mlp | 补「sd 定义、bootstrap 种子与次数、CI 覆盖范围」三行 → S3 离散度与区间复跑。是否改统计口径属统计席，本席不擅自改设定 |
| D7 | 校准链偏离与未跑完分支缺登记：`codec_stress.py:86-94` 缺 T+b 校准（R1）、`RESULTS.md:17-18` 记未跑完；`fold_split():162-170` 为占位死代码（R2） | 补「独立派生口径登记行 + 补跑/不补跑的批注行 + 切分指向 `main():185-192` 的说明行」→ S4 边界与 S5 剩余项；设定偏离需苏决批注，批注原文进同一行 |
| D8 | 派生字段命名规则缺说明：`exp22_05`/`exp22_rule` 实际先验为 `yte.mean()`（`:232-233`），非 0.22 | 补「命名规则说明行或字段改名记录」→ S2 派生命名与 S3 该两列回查 |
| D9 | 校准 holdout 口径明示缺行：`ncal=max(64, int(0.15*len(Xtr)))`（`:202`），报告只写 15% | 补「下限 64 的登记行」→ S2 校准参数复跑 |
| D10 | 过程流水与许可登记缺表：工作区无 `data/数据分析过程记录表.csv`（F-120 六列）与 `data/官方口径登记表.csv`（W-07） | 补「六列流水行（日期／动作／输入版本／参数与种子／结果落盘位置／异常与回退决定）+ W-07 许可行」→ 全篇按行号倒查与返修时新旧设定对照行成对出现。本轮未写盘，以文件:行号替代 |

红线自检说明（X-05 原述）：未代写论文正文、未代跑实验、未编造数据；涉及格式/选题/统计的判断一律标「转呈/不属本席」；未改设定，需改设定或补采集的诉求已标「交总编排转设计席与苏决批注」；不含可识别个人信息与原始 fid／spk 取值，异常数据形态只报「待补」不带原值；结果只报数值与区间，未作因果话术。

**自检：6/6**（字段齐／格式对／无占位未清／无承诺用语／无编造／无越界；待补项已逐条编号列明，非未清占位）

**【补充段】X-05 对总编排转呈事实的落表与判断**（接原回件末尾；原四块文字不覆盖、不删除，补充行与原行并列登记）

**0）事实复核与条号约定** — 转呈 3 条事实本席独立只读复核一致：协议 140,950 行 / unique speaker 785（与 `RESULTS.md:3` 一致）；`feats.npz` X(2000,50)、attack 取值 9 个（bonafide 1000 + A09–A16 各 125，与 L4 一致；注意 y 为 2 类、attack 为 9 取值，两者层级不同）；抽样池 `audio/flac_D` 47,400 条 flac，`extract_feats.py:43-59` 用 `default_rng(2026)`、按文件名排序后 shuffle，未使用 spk，非按 speaker 分层。
新增只读核实一处：**抽样池 = 47,400 条 flac ∩ 协议 140,950 行 = 47,400（0 条 flac 不在协议内）；协议中 93,550 条 fid 本地无 flac**。即池为 dev 全集的本地分片，而非全集。
条号约定（本席契约验收判据，为回查方便自编号，非外部条号）：V1 抽任一结果表图能倒查到流水行号／缺失与剔除的每个决定有理由码；V2 数据使用许可行（`data/官方口径登记表.csv` W-07）登记在先、入库在后；V3 返修补跑时新旧设定对照行成对出现。交付 F-120 六列流水、F-118 五段结果包；禁区 B02 不删样本、脱敏先行。本回件内临时理由码：RC-01 输入版本层级未区分、RC-02 抽样设计未登记。

**1）过程记录表增补行**（六列同原表；挂验收条号）

| 增补行 | 输入版本 | 脚本 | 参数与种子 | 产物 | 异常与回退 |
|---|---|---|---|---|---|
| ①-A 数据／抽样池 | 协议 140,950 行 + `audio/flac_D` 47,400 条 flac | `extract_feats.py:7-8,41-42,46-49` | `os.listdir` 取 .flac 文件名构造 set 后 `sorted(files)` 升序；meta 取自 track_1.tsv 全量；池 = 两者交集 47,400 | 内存 bona / by_attack 列表（不落盘） | 报告 L3「shard `flac_D_aa`」与本地目录名不一致；池非 dev 全集（缺 93,550 条 fid）→ V1/V2/F-120，RC-01；口径判定不属本席，转呈 |
| ①-B 数据／抽样实现 | 同上 | `extract_feats.py:43,50-59` | `default_rng(2026)` 单实例连续消耗——`:54 rng.shuffle(bona)` → `:57-59` 按 `sorted(by_attack.items())` 顺序对 8 个攻击列表各 shuffle 一次；bona 取前 1000、每攻击取前 125；`n_bona=1000`、`per_attack=125`、`limit=0`；spk 不参与抽样 | `ids`（2,000 条 fid，仅内存）→ `feats.npz` | 抽样非按 speaker 分层；628 为抽样结果派生量、非固定设计参数；fid 选样清单未落盘 → V1/V3/F-120，RC-02；若改为按 speaker 分层抽样，属重做设计／补采集，超出本席，交总编排转郑设研与苏决批注 |
| ③-A 切分／分组母集 | `feats.npz` 的 `spk`（628 个取值） | `run_real_check.py:185-189` | `np.unique(spk)` → `default_rng(1000+seed).shuffle` → `array_split(5)`；seeds=2、folds=5；同一 spk 只落 1 折 | `real_runs.csv` 第 4–5 列 n_te（352–467）与 pos_te（0.4485–0.5653） | 分组母集为子集内 628 个 speaker，非报告 L3 的 785；报告 L6「5 speaker-grouped folds」的母集层级未交代 → V1/V3/F-120；n_te / pos_te 波动为各折 speaker 样本数不均的落盘表现（数据事实），是否影响估计精度属统计席，本席不下结论 |

**2）两个判断（X-05 视角，不代其他席位结论）**

**Q1「抽样池与子集覆盖 speaker 数是否需要在报告口径中交代」**：按 V1，需要以数据登记形式交代，且必须成对登记两个层级——corpus-level 785（协议全量）与 subset-level 628（抽样子集、fold 分组母集），并登记池 47,400 条 flac 与本地缺失的 93,550 条 fid。理由：`RESULTS.md:3` 的 785 与 `RESULTS.md:6` 的 speaker-grouped folds 指向不同母集，不登记则任何引用 L3／L6 的结果行缺输入版本，无法倒查到流水行号（RC-01）。但「是否写入 RESULTS.md 正文、写在哪一句、用何措辞」属报告口径／格式席，本席只提出登记需求与理由码，不代为决定措辞、不改设定；本轮不写盘，故以本补充段的流水行登记替代。

**Q2「是否影响 speaker-grouped folds 的可复现性」**：分两层作答。
- (a) **下游折划分不受影响、可复现**：`run_real_check.py:185-189` 的输入是 `feats.npz` 已落盘的 spk（628 个），与抽样是否分层无关；`feats.npz` 与 seed 固定则 5 折划分确定，同一 spk 仍只落 1 折。当前工作区内「在 feats.npz 版本上向下游复跑」成立。
- (b) **端到端可复跑（协议+flac → 2,000 条 → 折）当前不成立**：依赖 47,400 条 flac 的文件名集合与 sorted 顺序、`default_rng(2026)` 的连续状态与 8 次 shuffle 的先后顺序、协议 label／attack 字段；fid 选样清单未落盘，且抽样非按 speaker 分层使 628 为派生量。任一环节变化会改变 fid 集合与 628，进而改变 5 折分组。按 V3，返修补跑须把「旧设定：seed 2026／47,400 池／非分层／sorted 顺序」与「新设定」逐项成对登记。
- (c) 非分层本身不破坏 speaker-grouped 结构，但「哪些 speaker 进入子集」这一步未受控；若要改为按 speaker 分层抽样，属重做设计／补采集，超出本席，交总编排转郑设研与苏决批注，批注原文进同一行。

**3）待补证据清单增补**（修订项与原项并列保留，符合 V3 成对；新项续号）

| 编号 | 缺什么 | 补哪样 → 解锁哪一段 |
|---|---|---|
| D3′（修订 D3；V1/V2/F-120） | 抽样池的可核对登记——池 = 47,400 条 flac ∩ 协议 = 47,400，协议另有 93,550 条 fid 本地无 flac；报告 shard `flac_D_aa` 与本地 `audio\flac_D` 不一致；2,000 条 fid 选样清单未落盘 | 补「原始分片清单 + 47,400 条 fid 池落盘 + seed 2026 下选样 fid 清单 + W-07 许可行（登记在先、入库在后）」→ S2 数据协议、V2、`feats.npz` 端到端复跑 |
| D4′（修订 D4；V1/V3/F-120） | speaker 层级口径与分组母集——协议 785 / 子集 628，抽样非按 speaker 分层 | 补「785 与 628 各一行层级定义 + 分组母集=628 的登记行 + 返修时新旧 628 对照行」→ S2 切分参数倒查与 V3 成对对照 |
| D11（新增；V1/V3/F-120） | 抽样 RNG 消耗顺序与排序规则——`extract_feats.py:42`（set 后 sorted）、`:43`（default_rng(2026)）、`:54`（shuffle bona）、`:57-59`（按攻击名升序连续 shuffle 8 次，共用同一 rng 状态）、numpy 版本 | 补「排序规则 + rng 状态消耗顺序 + 环境版本」登记行 → S2 抽样可复跑与 V3 新旧设定对照 |
| D12（新增；V1/F-120） | 各折规模落盘说明——`real_runs.csv` 第 4–5 列 n_te 352–467、pos_te 0.4485–0.5653，来自 628 个 speaker 分 5 组后样本数不均 | 补「每折 speaker 数 / 每折样本数」一行 → S3 按折倒查；是否影响统计精度属统计席，本席不下结论 |

**4）边界与自检（X-05 原述）**：本补充段仍为纯文本，未写盘、未改任何文件、未运行实验脚本；只读复核协议、目录清单、`feats.npz`、`real_runs.csv` 与脚本源码。未删任何原有行或样本（B02）；不含原始 fid／spk 取值与可识别信息（脱敏先行）；未作因果话术；报告措辞、格式判定、统计精度、抽样设计变更均标「不属本席／转呈／需苏决批注」。原回件【1】①、③、D3、D4 及四块结论维持不变，与本补充段并列可查。

**自检：6/6**（原回件 6/6 不变；补充段同项复核 6/6）

## 五、严校稿（X-09）回件

> 原样转呈，主持人未改写任何专业结论。只读声明：仅只读文件与目录列举，未运行任何 .py／实验脚本，未修改/新建文件；判定口径为「通过 / 待改 / 待补」，来源不可回查时写「未核实」，归入「待补（未核实）」。

### 一、四组一致性核查报告

**【组 1 · 术语】**

| # | 左：RESULTS.md 写法（定位） | 右：应核对来源 / 字段 | 判定 |
|---|---|---|---|
| 1 | :1「decision layer vs 0.5 threshold」；:20「the decision layer」；:8–11 表头「@rule」；:6「decision p ≥ 0.2」 | `run_real_check.py:4-5`「two decoders (0.5 threshold vs the cost rule p >= c_FP/(c_FP+c_FN))」；`:12-13` C_FP/C_FN、THR_RULE=0.2；`codec_stress.py:90` R.THR_RULE | **待补** — 四种写法指同一解码器，稿内无一处等价声明；「cost rule」一词未出现在 RESULTS.md |
| 2 | :4「bona fide」/「spoof」；:3「8 attack families」；:20「real speech」 | dev.track_1.tsv 首 15 行标签 bonafide / spoof、A09–A16；`extract_feats.py:50,75` | **通过** — 稿内 bona fide / spoof 各一次、无 genuine/bonafide 等同义混用。注（仅提示、非稿内不一致）：protocol 字面标签连写「bonafide」，稿内分写「bona fide」，属跨源写法差异 |
| 3 | :8 表头 AUPRC / AUROC / ECE / F1 @0.5 / F1 @rule | `real_runs.csv:1` 表头 auprc,auroc,ece,f1_05,f1_rule；json 同名键；`run_real_check.py:17,35,45,56`；`summarise.py:5-6` | **通过** — 缩写一一对应，全篇无 AP / ROC-AUC / accuracy 等别名 |
| 4 | :6「temperature+bias calibration」；表头「ECE」 | `run_real_check.py:147-159` fit_temperature(a=logT,b)；json:18-22,48-51,90-94,120-124 ece_iso/cost_iso；csv 同名字段 | **待补** — 稿内「calibration」仅指 temperature+bias；json/csv 另有 isotonic 对照（ece_iso / cost_iso）未进表，ECE 列对应哪种校准未声明（是否纳入报告属原席取舍，本席不判） |
| 5 | :13「paired bootstrap 95% interval over the 10 MLP runs」；:10「[665, 1,036]」 | `summarise.py:14-24`（seed 11、4000 次、仅 mlp 的 10 个 delta、delta_ci95）；json:146-149 [665.3, 1036.1] | **通过** — 「bootstrap / 95% interval」用法单一，无 confidence/credible 混用；口径披露不全另见组 4 与边界诚实 B5 |
| 6 | :1「Real-data anchor」；:5「the paper's four-channel 50-dim space」；:14「the paper's 60% attack prior」；:20「the simulation」 | `run_real_check.py:1` docstring 同名；工作区目录列举中无稿件 / 论文 / simulation 文件 | **待补（未核实）** — the paper / the simulation / Table II 的引用对象不在本轮材料内 |
| 7 | :5 同行「50-d vector」与「50-dim space」；「four-channel」 | `featlib.py:1`「50-d」、:3「50-dimensional」、:11「4-channel 50-feature vector」 | **待改** — 同一行内 50-d / 50-dim 两种缩写；four-channel（稿）与 4-channel（代码）数字体例不一 |

组 1 结论：指标缩写与 bona fide/spoof、bootstrap 用法统一；「decision layer = @rule = p≥0.2 = cost rule」等价声明、calibration 指代、外部引用可指性、50-d/50-dim 缩写 4 处待补/待改。

**【组 2 · 编号】**

| # | 左：RESULTS.md 写法 | 右：应核对来源 / 字段 | 判定 |
|---|---|---|---|
| 1 | :22「Table II」 | :8–11 仅一张无编号、无表题的表；目录列举无稿件/论文文件；`protocols/` 为 8 个 tsv/csv | **待补（未核实）** — 引用不可指；本稿内不存在编号 II 的表 |
| 2 | :3「8 attack families A09–A16」 | dev.track_1.tsv 首 15 行可见 A09,A10,A11,A12,A14,A15,A16；`extract_feats.py:53` 按 attack 标签分组；A13 未在前 15 行出现 | **通过**（算术自洽 8 连号）；**待补（未核实）** — A13 与「恰 8 族」全量核对未做（不跑脚本） |
| 3 | :4「2,000 utterances, 1,000 bona fide + 1,000 spoof (125 per family)」 | `extract_feats.py:34-35` 默认 n_bona=1000、per_attack=125；8×125=1000；csv 每 seed 五折 n_te 合计恰 2,000（seed0: 406+406+378+380+430；seed1: 379+467+406+396+352） | **通过** — 数量链自洽，且与折合计吻合 |
| 4 | :6「5 speaker-grouped folds × 2 seeds」；:13「Means over 10 runs」「10 MLP runs」 | `run_real_check.py:176-177`；`:185-190`；csv 20 数据行＝2 seed×5 fold×2 model；json 各键 n=10 | **通过** |
| 5 | :6「15% calibration holdout inside each training fold」 | `run_real_check.py:199-205` ncal=max(64,int(0.15*len(Xtr)))，hi[:ncal] 为 cal | **通过** — 与代码一致（含 64 下限，本规模不触发；逐 fold 精确值未核实） |
| 6 | :3「785 speakers」「shard `flac_D_aa`」；:4「speaker IDs from the protocol」 | dev.track_1.tsv spk 列 D_xxxx；`extract_feats.py:7,19`；`extract_feats.py:8` / `codec_stress.py:13` AUDIO=…\audio\flac_D；audio/ 实为 flac_D（47,400 个 .flac） | **待补** — 「785 speakers」无本轮可回查来源（feats.npz 为二进制、未跑脚本）→ 未核实；「flac_D_aa」与本地「audio/flac_D」不一致，需注明对应关系；「speaker IDs from the protocol」通过。**〔G04 仲裁见第九节〕** |
| 7 | :5「50-d vector … (duration, log-energy, centroid/flux/roll-off, ZCR, 25 log-mel bands, 15 MFCCs)」 | `featlib.py:3-9` 显式 1–10 十个标量 + 11–35 二十五个 log-mel + 36–50 十五个 MFCC＝50；`:101-105` f 列表 10+25+15 | **待补** — 括号枚举按字面加总为 46（1+1+3+1+25+15），与「50-d」及 featlib 的 10 标量口径不闭合，需对齐枚举口径（不涉数据改动） |
| 8 | :3「ASVspoof5 dev」 | `extract_feats.py:7` 仅引用 ASVspoof5.dev.track_1.tsv；protocols/ 内确有该文件 | **通过** — protocol 指向可回查；train/eval/track_2 文件未被本实验引用，稿内亦未声称使用 |

组 2 结论：8 族 / 2,000 / 125 / 5×2 / 10 runs / 15% 数量链自洽且可回查；Table II 不可指、785 未核实、分片名不一致、50-d 枚举不闭合 4 处待补。

**【组 3 · 单位】**

| # | 左：RESULTS.md 写法 | 右：应核对来源 / 字段 | 判定 |
|---|---|---|---|
| 1 | :6「cost c_FP = 5, c_FN = 20」；:8 表头「cost @0.5」「cost @rule」（无单位）；:14「per 1,000」；:21「~2,000 per 1,000 calls」 | `run_real_check.py:5`「cost per 1,000 calls with c_FP=5, c_FN=20」；`:12-13`；`:63-66` cost_per_1000=(fp*C_FP+fn*C_FN)/len(y)*1000；`:69-75` 亦 *1000 | **待改** — 单位写法三处不齐（表头缺、:14 省「calls」、:21 全）；数值—量纲本身配套，判通过 |
| 2 | :6「decision p ≥ 0.2」与 c_FP=5 / c_FN=20 | `run_real_check.py:13` THR_RULE=C_FP/(C_FP+C_FN)=5/25=0.2；`:218` predr=(p>=THR_RULE) | **通过** — 自洽（阈值与权重同量纲、无量纲错配）；**待补**：稿内未给推导式、未声明阈值随 cost 权重设定而变的适用条件 |
| 3 | :20「cuts cost by 29.8%」「while F1 falls slightly」 | json:33-47 mlp.cost05.mean=2860.34、cost_rule.mean=2007.60、delta.mean=852.74 → 29.8%；lr 对应 1489.55/3885.58=**38.3%**；:10–11 F1：MLP 0.770→0.759（降）、lr 0.676→0.686（**升**） | **待改** — 29.8% 与「F1 falls slightly」仅对 MLP 成立，句内未按 detector 限定且与 :11 表不符；29.8% 的分母口径（汇总均值比 vs 逐 run 比率均值）稿内未写，后者未核实 |
| 4 | :14「60% attack prior … 2,337 → 1,583 per 1,000」 | `run_real_check.py:69-75,230-231`；json:53-61 mlp.exp60_05=2337.02、exp60_rule=1582.52；lr:125-133 为 3109.14 / 1976.85 | **待改** — 数值对得上且为 MLP，但 detector 归属未标、箭头语义（@0.5→@rule 还是重加权前后）未说明、「per 1,000」单位不齐；「the paper's 60%」为外部设定，未核实 |
| 5 | :21「absolute level of cost (~2,000 per 1,000 calls)」 | json:38-42 mlp.cost_rule.mean=2007.60 | **通过** — 量级、单位、量纲一致 |

组 3 结论：cost/权重/阈值/重加权数值与量纲配套；单位标注不齐、29.8% 与 F1 表述未按 detector 限定、60% 重加权口径 3 处待改；p 推导与阈值适用条件待补。

**【组 4 · 图表】**

| # | 左：RESULTS.md 写法 | 右：应核对来源 / 字段 | 判定 |
|---|---|---|---|
| 1 | :8 表头 9 列 | csv:1 列；json 键；`summarise.py:5-6` | **通过** — AUPRC↔auprc、AUROC↔auroc、ECE↔ece、cost @0.5↔cost05、cost @rule↔cost_rule、Δ↔delta、F1 @0.5↔f1_05、F1 @rule↔f1_rule；千分位写法（2,860 / 3,886 / 2,008 / 1,036 / 2,337 / 1,583）全表一致 |
| 2 | :10 MLP 整行（含 853 [665, 1,036]） | json mlp.*；delta_ci95 [665.3,1036.1] | **通过** — 逐格复核：0.867/0.027、0.860/0.015、0.075/0.019、2,860/355、2,008/126、853、[665,1,036]、0.770、0.759 全部与源一致 |
| 3 | :11 logistic 整行 | json lr.*；csv ece 列 10 行 | **待改** — 仅 ECE 单元格「0.087 (0.019)」与 `lr.ece.mean=0.0772401`（csv 十行 ece 均值同值）不符；同格 SD 0.019 与 `lr.ece.sd=0.018685` 相符；其余 8 格一致。**本席只报差异，不改动、不代填** |
| 4 | :13「Means over 10 runs, standard deviation in parentheses」 | :10–11 表；json 各键均含 sd | **待改** — F1 @0.5 / F1 @rule 两列无括号 SD（源有 sd=0.0227/0.0284/0.0290/0.0333），Δ 列两行亦无 SD；表注覆盖不全 |
| 5 | :10「853 [665, 1,036]」；:11「1,490」；:13「Δ is a paired bootstrap 95% interval over the 10 MLP runs」 | json:146-149 仅一个 delta_ci95；`summarise.py:17-24` 仅 mlp 的 10 个 delta；`run_real_check.py:227` delta=cost05−cost_rule | **待改** — Δ 的 CI 写法前后不一致（MLP 有点估计+方括号 CI，lr 仅点估计）；:13 未给出 Δ 定义、未说明 CI 仅覆盖 MLP、未披露 4000 次重采样 / seed 11 / pstdev（`summarise.py:11,16,20`） |
| 6 | 表内未出现的源字段 | json ece_iso、cost_iso、exp22_05、exp22_rule 及 lr.exp60_*；csv ece_iso、cost_iso、exp22_*、thr_block、pos_te | **待补** — 列名可对应源字段的「子集」；上述字段未进表，是否报告属原席取舍，本席不判，仅提示需一句口径声明 |
| 7 | :14「2,337 → 1,583」与表 :8–11 并列 | 表 cost @0.5 / cost @rule 列；json exp60_05 / exp60_rule | **待补** — :14 与表使用同一箭头但轴不同（60% prior 重加权 vs @0.5→@rule），未加区分说明 |

组 4 结论：列名—字段映射、MLP 行数值、千分位体例判通过；logistic ECE 数值、SD 括号覆盖、Δ 的 CI 写法 3 处待改；未进表字段与箭头语义待补。

### 二、边界诚实段清单

**【已具备】**

| 编号 | 位置 | 内容 |
|---|---|---|
| E1 | :5 | 明确 50-d 特征仅来自解码波形、「NOT the paper's four-channel 50-dim space」、语音语料无 signalling/semantic channel；与 `featlib.py:11-13` 同口径 |
| E2 | :20–22 | 明确 corpus 与 feature channel 不同、绝对 cost 水平不可与 Table II 比较 |
| E3 | :21 | 给出绝对量级「~2,000 per 1,000 calls」而非只报相对改进；与 json mlp.cost_rule.mean=2007.6 一致 |
| E4 | :6 与 :13 | 披露协议关键设置（5×2 folds、15% holdout、temperature+bias、cost 权重、p≥0.2）与统计口径（10 runs 均值 / 括号 SD / bootstrap 95% 区间） |
| E5 | :18 | 如实记录 codec_stress.py 未跑完及原因（host page-file 耗尽于 ffmpeg 并发）；确认工作区无 codec_stress.csv |
| E6 | :3–4 | 明确是 ASVspoof5 dev 子集（2,000 条、125/族、speaker IDs from protocol），非全量语料 |

**【需补】**

| 编号 | 位置 | 需补内容 |
|---|---|---|
| B1 | :18 | 未写明「该实验无可用结果 / 本稿不含 waveform-codec 结论」；:16–18 文件清单列出 codec_stress.py，易被误读为有配套结果。codec_stress.py 列了 4 个条件（clean / g711_8k / opus_12k / opus_24k），稿内未标注条件与结果均缺。措辞由原席写 |
| B2 | :22 | 「Table II」不可指；同 :5/:14/:20 的「the paper」「the simulation」「the paper's 60% attack prior」亦无本轮可核来源 → 未核实，需补可指来源或改稿内编号 |
| B3 | :14 | 60% prior 为重加权目标（外部设定），未说明本语料实测 pos_te 约 0.448–0.565；json 另有 exp22_*（按 yte.mean() 重加权）未报 → 需写明重加权结果非本语料实测 cost |
| B4 | :20 | 定性结论（29.8% /「F1 falls slightly」）未按 detector 限定；:11 表显示 lr 为 38.3% 且 F1 上升 → 需分述或限定 MLP |
| B5 | :13 | bootstrap 口径披露不全：seed 11 / 4000 次 / 仅 MLP 10 个 delta / pstdev / delta_ci95 仅一个（MLP） |
| B6 | :6 | 未给出 p=c_FP/(c_FP+c_FN) 的推导（`run_real_check.py:13` 有），未声明「阈值随 cost 权重设定而变」这一适用条件 |
| B7 | :3 | 「785 speakers」与「`flac_D_aa`」无本轮可回查来源（785 未核实；本地目录为 audio/flac_D）→ 需补出处或对应关系。**〔G04 仲裁见第九节〕** |
| B8 | :5 / :8–11 | 「calibration」仅指 temperature+bias，但 ece_iso / cost_iso 字段存在且未进表；未声明 ECE 列对应哪种校准 |
| B9 | :5 | 50-d 括号枚举按字面加总 46，与 `featlib.py:3-9` 的 10+25+15=50 不闭合 → 需对齐枚举口径（非改数据） |
| B10 | :4 | 「2,000 utterances」为选中数量；`extract_feats.py:43` 用 rng(2026) 抽样、`:69-72` 解码失败跳过，稿内未披露抽样种子与失败跳过规则（本轮由 csv 各折 n_te 合计确认有效 2,000 条；feats.npz 内部未读、未跑脚本 → 未核实） |

### 三、待改条目清单（逐条：该改什么 / 依据哪一组；只描述，不改写正文、不代写补充实验段）

| 编号 | 依据 | 该改什么 |
|---|---|---|
| R1 | 组 4 图表；兼组 3 单位 | :11 logistic 行 ECE 单元格「0.087」与 `real_summary.json` lr.ece.mean=0.0772 及 csv ece 列十行均值不符（同格 SD 0.019 与 lr.ece.sd 相符）→ 回源核对并统一该格数值；本席不改动数值、不代填 |
| R2 | 组 3 单位 | 表头 cost 两列未标单位、:14 作「per 1,000」、:21 作「per 1,000 calls」、:6 未出现单位 → 以 :21 已有写法为基准统一，并在表头或表注标明；仅体例，不涉数值 |
| R3 | 组 4 图表 | F1 @0.5 / F1 @rule 两列未带括号 SD（源 json 有 sd），与 :13 表注不符 → 补齐或修正表注覆盖范围说明 |
| R4 | 组 4 图表 | Δ 列前后写法不一（MLP 含 CI，lr 无 CI 无 SD），且 :13 未定义 Δ、未说明 CI 仅覆盖 MLP → 补 Δ 定义（`run_real_check.py:227`）与两行写法说明、方括号/圆括号体例区分 |
| R5 | 组 1 术语 | decision layer(:1,:20) / @rule(表头) / p≥0.2(:6) / cost rule(`run_real_check.py:4-5`) 四种写法指同一解码器，稿内无等价声明 → 在 Protocol 行或表注一次性写明等价关系；「0.5 threshold」与「@0.5」亦一并挂钩 |
| R6 | 组 1 术语；兼组 4 | 稿内「calibration」仅指 temperature+bias，而 json/csv 有 ece_iso / cost_iso 未进表 → 需声明 ECE 列对应哪种校准、isotonic 对照是否在报告范围（是否纳入属原席取舍，本席不判） |
| R7 | 组 1 术语 | :5 同一行「50-d」与「50-dim」两种缩写 → 统一；另「four-channel」(稿) 与「4-channel」(featlib.py:11) 数字体例可一并统一 |
| R8 | 组 2 编号 | :22「Table II」及 :5/:14/:20 的「the paper」「the simulation」「the paper's 60% attack prior」引用对象不可指 → 补可指来源或改稿内编号；当前判未核实 |
| R9 | 组 2 编号 | :3「shard `flac_D_aa`」与本地 AUDIO 目录「audio/flac_D」不一致 → 注明二者对应关系（原始分片名 vs 解压目录）或统一名称 |
| R10 | 组 2 编号 | :3「785 speakers」无本轮可回查来源 → 补出处或明确标注未核实。**〔G04 仲裁见第九节〕** |
| R11 | 组 2 编号 | :5 的 50-d 括号枚举按字面加总 46 ≠ 50 → 按 `featlib.py:3-9` 的「10 个标量统计量 + 25 log-mel + 15 MFCC」口径对齐枚举；不改动任何数值 |
| R12 | 组 3 单位；兼 B4 | :20「29.8%」「F1 falls slightly」未按 detector 限定（lr 为 38.3%、F1 0.676→0.686 上升），且 29.8% 分母口径未写 → 限定 detector 并写明分母口径；逐 run 比率均值口径未核实 |
| R13 | 组 3 单位；兼组 4 | :14「2,337 → 1,583」实为 MLP 的 exp60_05 / exp60_rule（lr 的 3,109 → 1,977 未出现），箭头语义未说明 → 标注 detector 归属、说明箭头是 @0.5→@rule 还是「重加权前后」，并统一单位 |
| R14 | 边界诚实 B1 | :18 需补一句「本稿不含 codec stress 结果、该条件不作结论」的说明，避免文件清单被误读为有配套结果；具体措辞由原席写 |
| R15 | 边界诚实 B3/B5/B6 | 补三项适用条件/口径披露：①60% prior 为外部重加权设定、本语料实测 pos_te 约 0.448–0.565 与之不同（且 exp22_* 未报）；②bootstrap 的 4000 次 / seed 11 / pstdev / CI 仅 MLP；③p=c_FP/(c_FP+c_FN) 推导与「阈值随 cost 权重而变」 |
| R16 | 组 1 术语，提示项 | :4「bona fide」与 protocol 标签「bonafide」跨源写法差异 → 若全稿其他处用连写需统一；RESULTS.md 稿内本身无混用，不作硬性待改 |

**【回件边界 · X-09 原述】** 本席只交付核查报告与落点清单：未改写 RESULTS.md 任何正文、未代写论文或补充实验段、未代跑/重算实验、未编造数据；logistic ECE 一格仅报差异不代填；涉及内容取舍、论证改写、数据口径实质的判定（isotonic 对照是否上报、exp22_* 是否补、29.8% 采用何种分母口径、外部引用出处）均交回原席/总编排，本席不越界。图像/图表合规、对外一致性四项（稿件—系统—声明—CV）不在本轮派单范围，未展开；换模板需另走一遍完整 C 组。

**自检：6/6**（字段齐 ✓ 格式对 ✓ 无占位未清 ✓ 无承诺用语 ✓ 无编造 ✓ 无越界 ✓）

**【补充段】X-09 对总编排转呈证据的重走判定**（附于原回件末尾，不覆盖原文；触发：总编排转呈 3 条只读事实 + X-05 两批交叉参考，按本席「换证据必重走一遍 C 组」契约重判）

**【重走声明】**（X-09 原述）本席未写盘、未运行实验脚本、未改 RESULTS.md、未代写正文；新证据中的全量计数（785 / 140,950 / 47,400 / 628 / 93,550 / X(2000,50)）均据总编排转呈与 X-05 只读复核，本席据以做口径比对，未自行重算（`feats.npz` 二进制未读、未跑脚本 → 全量统计本身标「据转呈」）。C 组细则文件 `references/07_一致性_格式与规范核查细则.md` 不在本轮工作区（已检索 `D:/ace/语义攻击` 及本轮目录，无此文件）→ 具体条目编号「未核实」；本补充段按派单指定标号挂靠：C-100＝编号/命名、C-300＝单位/量纲、C-400＝字段/母体口径，不臆造条目号。点 3 按派单作「通过」项。

**【受影响的原判定 · 更新清单】**

| 原条目 | 原判 | 更新 |
|---|---|---|
| 组 2 第 6 行 / R10 / B7 中「785 speakers」 | 待补（未核实） | **撤销「未核实」** → 数字本身已证实为 protocol 全量 unique speaker，改判「**口径待改**」（同物异指：785 语料 / 628 实验） |
| 组 2 第 6 行 / R9 / B7 中「flac_D_aa」 | 待补 | 补入 47,400 / 140,950 事实，**升级为「待改」**（名称不一致 + 语料范围未限定） |
| B10 抽样口径 | 待补 | 扩展（新增非分层、派生量、RNG 顺序三条），仍判「待补」 |
| 组 2 第 3 行、组 4 第 1/2 行、R1 | — | 与原判一致，维持；R1 新增佐证（见 X1） |

**补充表 A · C-100 / C-400「编号与语料口径」**

| # | 左：RESULTS.md 写法（定位） | 右：应核对来源 / 字段 | 判定 |
|---|---|---|---|
| A1 [C-100] | :3「Corpus: ASVspoof5 dev (shard `flac_D_aa`), 785 speakers」 | dev.track_1.tsv 全量 140,950 行、unique speaker 785（据转呈 / X-05）；`feats.npz` spk unique 628（2,000 子集覆盖）；`run_real_check.py:185-189` 按 spk 分组实为这 628 | **待改** — 785 核实无误，但「speakers」在稿内仅此一次且紧邻 :6「5 speaker-grouped folds」，实际分组母体是 628；两个所指未区分，属同物异指 |
| A2 [C-100/C-400] | :3「785 speakers」未标注是语料全量还是实验子集；:6「5 speaker-grouped folds」未给分组说话人数 | X-05：628 是抽样结果派生量、非设计参数；抽样不按 speaker 分层（`extract_feats.py:43-59`）；X(2000,50) | **待补** — 需声明 folds 的说话人数为 628、且 628 为派生值（非分层抽样设计），否则「speaker-grouped」易被读成基于 785 |
| A3 [C-100] | :3「shard `flac_D_aa`」 | 实际目录 `audio/flac_D`，47,400 条 flac；该 47,400 全部命中协议 fid，协议另有 93,550 条 fid 本地无 flac（47,400+93,550=140,950） | **待改** — 分片名与本地目录名不一致（原 R9 维持并升级）；且稿内未说明该 shard 只是 dev 全集的本地子集 |
| A4 [C-100/C-400] | :3「ASVspoof5 dev」（未限定范围）＋ :4「2,000 utterances」 | dev 全集 140,950 行 → 本地池 47,400 flac → 抽样子集 2,000；X(2000,50) | **待补** — 三级规模在稿内只出现末级 2,000；需标注抽样池为本地分片而非 dev 全量 |
| A5 [C-400]（派单点 3，通过项） | :4「2,000 utterances, 1,000 bona fide + 1,000 spoof (125 per family)」；:3「8 attack families A09–A16」 | X-05：attack = A09–A16 各 125 ＋ bonafide 1000（9 标签），y=1000+1000，X 形状 (2000,50)；原组 2 第 3 行 8×125=1000、+1000=2000 | **通过** — 全量分布与 :4 及原判一致；X 的 50 列亦支持「50-d」维度数（不改变组 2 第 7 行「括号枚举加总 46」的表述口径待补） |

表 A 结论：点 1、点 2 的编号面判「待改」（785/628 同物异指、`flac_D_aa` 名实不符）＋「待补」（母体限定语缺失）；点 3 判「通过」。

**补充表 B · C-300「单位 / 量纲 / 计数母体口径」**

| # | 左：RESULTS.md 写法 | 右：应核对来源 / 字段 | 判定 |
|---|---|---|---|
| B1 [C-300] | :3「785 speakers」——计数，未标母体 | 785 ＝ protocol 全量 unique speaker；628 ＝ `feats.npz` spk unique（2,000 子集）；47,400 ＝ 本地 flac 数；140,950 ＝ dev 协议行数 | **待改** — 同为计数、无量纲错配，但同一单位词「speakers」承载两个不同母体（全量 / 子集），口径错配；需分别命名限定，不改动任何数值 |
| B2 [C-300/C-400] | :3 全行未给语料规模数值；:4 仅给 2,000 | 三级计数 140,950 / 47,400 / 2,000 母体不同；与原组 3 的 cost「per 1,000 calls」为不同量纲，互不冲突 | **待补** — 计数层级未标母体；与 cost 量纲交叉核对「通过」（无错配、无单位串用） |
| B3 [C-300/C-400] | :6「cost c_FP=5, c_FN=20」；:14「60% attack prior」；:8–11 cost 列 | X-05 复核：csv 20 行（10 mlp+10 lr）→ json 14 键×2 模型 mean/sd 全一致、n=10/10、delta_ci95=[665.3,1036.1] | **通过** — 聚合链与原组 3 / 组 4 判定一致，无新增量纲问题；原 R2（单位标注不齐）、R13（箭头语义）不受影响 |

表 B 结论：数值本身量纲配套、无错配（通过）；计数母体未区分与层级未标注判「待改 / 待补」。

**交叉参考 · X-05 两批只读事实对 X-09 旧判定的影响**

| 编号 | 内容 |
|---|---|
| X1 | :11 ECE「0.087 (0.019)」：X-05 复核 `lr.ece.mean=0.077240`、`lr.ece_iso.mean=0.082315`、`mlp.ece_iso.mean=0.086127`，无一为 0.087；sd 0.018685→0.019 对得上。→ 原 R1「待改（回源核对、不代填）」维持并加强：**可排除「误填 isotonic 列」这一解释**，但本席仍不臆断正确值、不代填；是否重算/统计口径归统计席 |
| X2 | csv→json 聚合链（20 行 → 14 键×2、n=10、delta_ci95）→ 原组 4 第 1/2 行「通过」维持；原 R4（Δ 定义与 CI 覆盖）、R3（F1 缺 SD）是稿面写法问题，不受数据链复核结论影响，维持「待改」 |
| X3 | 抽样池 47,400 全命中协议、93,550 条本地无 flac；抽样非按 speaker 分层、628 为派生量；RNG 顺序（`:54 shuffle(bona)` 后按 `sorted(by_attack.items())` 连续 shuffle 8 次、共用 `default_rng(2026)`）依赖顺序与 numpy 版本 → 并入原 B10「需补」，扩展为可复现披露条目（见 R21），仍判「待补」 |

说明（X-09 原述）：以上 X-05 事实本席仅作交叉参考，未替其下数据结论，也未把 628/785 之类转成统计席结论。

**补充段待改落点（编号续原回件 R，只描述，不改写正文、不代写实验段）**

| 编号 | 依据 | 该改什么 |
|---|---|---|
| R17 [C-100/C-400；更新 R10] | 编号口径 | :3「785 speakers」数字已核实无误，**撤销原「未核实」**；需与实验实际分组对象 628（`feats.npz` spk、`run_real_check.py:185-189`）区分标注，改判「口径待改」 |
| R18 [C-100/C-400] | 编号/母体 | :3 补限定语，说明 speaker-grouped folds 的说话人数为 628、且为抽样派生量（非按 speaker 分层设计）；措辞由原席写 |
| R19 [C-100/C-400；更新 R9] | 编号 | :3「flac_D_aa」升级为「待改」：与本地 `audio/flac_D` 名实不符，且需标注该分片为 dev 全集的本地子集（47,400 / 140,950） |
| R20 [C-300/C-400] | 单位口径 | 三级计数母体（140,950 协议行 / 47,400 本地 flac / 2,000 子集）稿内只出现末级，需在 Corpus 行标明抽样池范围；与 cost「per 1,000 calls」量纲无冲突，仅母体口径 |
| R21 [边界诚实 B10 扩展，仍待补] | 可复现披露 | 补三项：抽样非按 speaker 分层、628 为派生量、RNG 状态顺序依赖 `sorted(by_attack)` 顺序与 numpy 版本（`extract_feats.py:43-59`） |
| R22 [C-400；R1 佐证加强] | 数据回查 | :11 ECE 0.087 维持「待改（回源核对、不代填）」；X-05 已排除三个 ece 系列字段，本席不臆断正确值、不代填 |

**【补充段结论 · X-09 原述】** 转呈点 1（785/628）与点 2（`flac_D_aa` / 47,400）在编号组判「待改」、在单位/口径组判「待改＋待补」；点 3（attack 分布与 X 形状）判「通过」。原回件其余 4 组判定、边界诚实 E/B 清单、R1–R16 除上述 R9/R10/B10 更新外均不变。本席仍只交付核查报告与落点，不产「最终可提交版」承诺，不改他人正文，提交决定在作者。

**自检：6/6**（字段齐 ✓ 格式对 ✓ 无占位未清 ✓ 无承诺用语 ✓ 无编造 ✓ 无越界 ✓；新增计数均标注「据转呈」、C 组细则文件缺席已标「未核实」）

## 六、补充实验段〔示意〕骨架

由 X-05 回件【3】原样转呈（见第四节），主持人只拼装、不代写正文；每段按 X-09 待改条目挂接落点，便于作者按号取用。

| 段 | 功能句（X-05 原文） | 需先清掉的落点 |
|---|---|---|
| S1 动机 | 承担「在真实语音锚点上复核 decision layer 相对 0.5 阈值」的问题设定与对照对象登记，不承载数值与机制判断 | B2 / R5 / R8（等价声明与可指来源） |
| S2 数据协议 | 承担语料、子集、特征、切分、校准、代价与阈值全部可复跑参数及其落盘位置的逐行登记 | B7 / B9 / B10 / D3′ / D4′ / D11 / D12 / R9 / R11 / R15 |
| S3 结果 | 承担按检测器与指标陈列落盘数值、离散度与区间的表格，只报数值与区间、不含解读句 | R1 / R2 / R3 / R4 / R13 / D2 / D6 |
| S4 边界 | 承担语料与特征通道差异、未跑完分支、不等价评分链等适用范围限定项的列示 | B1 / B3 / B4 / B6 / B8 / R12 / R14 / D7 |
| S5 待补 | 承担缺项、补录件与所解锁段落的逐条编号登记，与流水行号一一对应 | 第七节全表 |

**已具备、不建议动的边界段**（X-09 判 E1–E6）：特征通道非论文四通道（:5）、绝对 cost 与 Table II 不可比（:20–22）、给出绝对量级而非只报相对改进（:21）、未跑完分支如实记录（:18）、明确是 dev 子集非全量（:3–4）。这五处是当前稿件的边界诚实资产，返修时勿删。

## 七、待补清单（汇编）

只做编号归并，不新增专业判断；每条括号为来源席条目号。P0/P1 为总编排的**派单优先级**，不是对稿件严重度的专业判定。

**P0 · 阻断可信度，需作者先确认或补料**

| 编号 | 待补项 | 来源 |
|---|---|---|
| P0-1 | `RESULTS.md:11` logistic ECE「0.087」在 `real_summary.json` / `real_runs.csv` 中无一致字段（`lr.ece.mean=0.077240`、sd=0.018685 相符）。按 G06 涉数据改动须作者确认，须先定以哪个落盘字段为准，再统一该格；本团不代填 | X-09 组4-3 / R1；X-05【1】⑥ / D2 / 附注 |
| P0-2 | :20「cuts cost by 29.8%」「F1 falls slightly」未按 detector 限定——lr 为 38.3% 且 F1 0.676→0.686 上升；29.8% 分母口径（汇总均值比 vs 逐 run 比率均值）未写 | X-09 组3-3 / B4 / R12；X-05 回查 C3 |
| P0-3 | 「Table II」「the paper」「the simulation」「the paper's 60% attack prior」引用对象不可指；工作区无稿件／仿真结果／Table II 数值 | X-09 组1-6 / 组2-1 / B2 / R8；X-05 C4 / C5 / D1 |
| P0-4 | codec stress 未跑完需明示「本稿不含 waveform-codec 结论」；且 `codec_stress.py:86-94` 缺 T+b 校准、与主协议不同源，即使补跑也不能与 Table II／主结果并列 | X-09 B1 / R14 / E5；X-05【1】④ / D7；总编排 R1 / C-6 |

**P1 · 可追溯与体例**

| 编号 | 待补项 | 来源 |
|---|---|---|
| P1-1 | 785（协议全量）与 628（子集、fold 分组母集）成对登记层级定义；补「flac_D_aa ↔ audio/flac_D」对应关系 | C-7 / C-8；X-05 D3′ / D4′ / Q1；X-09 组2-6 / B7 / R9 / R10（G04 见第九节） |
| P1-2 | 端到端复跑不成立：fid 选样清单未落盘、非 speaker 分层使 628 为派生量、rng(2026) 消耗顺序与 numpy 版本未登记；每折 speaker 数 / 样本数未落表 | X-05 Q2(b)(c) / D3′ / D11 / D12；X-09 B10 |
| P1-3 | 50-d 括号枚举字面加总 46 ≠ 50；`featlib.py:3-9` 声明 flux std、`:96/:102` 实现为 flux mean 重复，有效维数需复核 | X-09 组2-7 / B9 / R11；X-05【1】② / D5 |
| P1-4 | 聚合与校准口径披露：pstdev(ddof=0)、bootstrap seed 11 / 4000 次 / CI 仅 MLP、ncal 下限 64、p=c_FP/(c_FP+c_FN) 推导与阈值随权重而变 | X-09 B5 / B6 / 组4-5 / R4 / R15；X-05【1】④⑤ / D6 / D9 |
| P1-5 | 单位体例（cost 表头 / :14 / :21）、F1 与 Δ 列缺 SD、Δ 的 CI 前后写法、:14 箭头语义与 detector 归属 | X-09 R2 / R3 / R4 / R13 / 组3-1 / 组4-7 |
| P1-6 | 术语等价声明（decision layer = @rule = p≥0.2 = cost rule = 0.5 threshold 对照）、50-d/50-dim、four-/4-channel、ECE 对应哪种校准、isotonic 对照是否入表 | X-09 R5 / R6 / R7 / B8 / 组1-1 / 组1-4 / 组4-6 |
| P1-7 | 派生字段命名 `exp22_*` 实际先验为 `yte.mean()` 非 0.22；60% 重加权非本语料实测 cost（pos_te 0.448–0.565） | X-05【1】⑤ / D8；X-09 B3 / 组3-4 |
| P1-8 | 占位死代码 `fold_split():162-170` 处置；复跑指向 `main():185-192` | 总编排 R2；X-05【1】③ / D7 |
| P1-9 | 过程流水与许可登记缺表（F-120 六列流水、W-07 登记在先入库在后）；返修时新旧设定对照行成对出现 | X-05 D10 / 补充段 V1–V3 |

**X-09 补充段归并（并列登记，不覆盖上表原行；符合 V3 新旧设定成对出现）**

| 新增条目 | 归入 | 处置 |
|---|---|---|
| R17 / R18 / R19 / R20 | P1-1（785/628 层级与分片名） | 与 C-7、C-8、D3′、D4′ 并列；R17 撤销「785 未核实」、R19 把 `flac_D_aa` 由「待补」升级为「待改」，不改数值 |
| R21 | P1-2（端到端复跑） | 与 D3′/D11/D12/Q2(b)(c) 并列，补三项可复现披露 |
| R22 / X1 | **P0-1** | 新增佐证：X-05 已排除 `lr.ece`、`lr.ece_iso`、`mlp.ece_iso` 三个字段，可**排除「误填 isotonic 列」这一解释**；R1 仍维持「回源核对、不代填」 |
| X2 | 已核对项 | csv→json 聚合链复核通过，R3/R4 属稿面写法问题、不受影响 |
| A5 / B3 | 已核对项 | attack 分布、X(2000,50)、量纲配套判「通过」 |

补充段**不新增第 14 项待补**：R17–R22 全部并入既有 P0/P1 编号，故收口仍为 13 项。另登记一条席位合规标注：X-09 声明 C 组细则文件 `references/07_一致性_格式与规范核查细则.md` 不在本工作区，故 C-100/C-300/C-400 的具体条目号标「未核实」，本团按派单挂靠、不臆造条目编号（RD2/RD4）。

**G01 三问仍缺的料**（不属两席结论，由作者补）：① 交给谁看（期刊／学位／基金／会议）；② 处在哪环（只有想法／有数据未成文／已成文未核对／已投出等回件）；③ 稿件全文、审稿意见原文、目标期刊体例。三问未答清，本团不派下一轮的席位单。

## 八、收口三行

**已核对 3 层、共 4 批回件**：总编排 C-1～C-10（10 项）；X-05 四块＋补充段（过程记录表、结论句 5 句回查、〔示意〕骨架、D1–D12 待补、Q1/Q2 两个判断）；X-09 四组一致性比对＋E1–E6 已具备＋B1–B10 需补＋R1–R16 待改；X-09 补充段（补充表 A/B、交叉参考 X1–X3、R17–R22，含对 R9/R10/B10 的判定更新）。
**还缺 13 项待补（逐条报名号）**：P0-1、P0-2、P0-3、P0-4、P1-1、P1-2、P1-3、P1-4、P1-5、P1-6、P1-7、P1-8、P1-9；另 `codec_stress.csv` 无产物、G01 三问未答。
**下一步只做**：请作者确认 P0-1 的 `RESULTS.md:11` ECE「0.087」应以哪个落盘字段为准（G06 作者确认制），确认后由对应席出统一口径；其余 12 项排队，本轮不扩面（G02）。

自检：6/6（字段齐／格式对／无占位未清／无承诺用语／无编造／无越界）

## 九、G04 冲突仲裁与变更记录

**争点 1（需仲裁）｜「785 speakers」是否可回查**
- X-09（组2-6、B7、R10）判「未核实」，理由：该席只读文本材料、`feats.npz` 为二进制未读、未跑脚本。
- 总编排 C-7 与 X-05 补充段 0) 已独立只读核对：`protocols/ASVspoof5.dev.track_1.tsv` 全量 140,950 行、unique speaker = **785**（与 `RESULTS.md:3` 一致）；`feats.npz` 的 `spk` unique = **628**（子集覆盖、fold 分组母集）；抽样池 47,400 条 flac 全部落在协议内，协议另有 93,550 条 fid 本地无音频。
- **裁决：采总编排 C-7 与 X-05 的事实认定（785 为协议全量 corpus-level，可回查）**；X-09 的「未核实」标注**保留不删**——在其材料范围内成立，且 R10「补出处」的诉求依然有效，因为报告未区分 785 与 628 两个层级。依据：G04 主理人仲裁、三·1「可追溯：每条主张有数据位置」、RD2「事实与来源只取本轮材料」。
- 变更登记：B7／R10 的结论细化为「785 = 协议全量已核实；报告需补 corpus-level 785 与 subset-level 628 的层级定义」；X-09 回件原文不改，只在此留痕。

**后续变更（X-09 补充段，收口前到达）｜争点 1 已自行消解**
- X-09 按本席「换证据必重走一遍 C 组」契约，在补充段的【受影响的原判定 · 更新清单】中**主动撤销**组 2 第 6 行 / R10 / B7 的「785 未核实」，改判「口径待改」（785 语料 / 628 实验同物异指）；R9 由「待补」升级为「待改」；B10 扩展为可复现披露；新增 R17–R22。
- **对裁决的影响**：事实结论不变（785 = 协议全量已核实、628 = 子集／fold 分组母集），但性质由「主理人裁决两席分歧」变为「两席与总编排一致收敛」。按 G04 与 G08 每轮留痕，此处登记变更：上述裁决文字**保留不删**（作为当时状态），补充段判定**并列登记**，X-09 原回件不覆盖。
- 追加变更：R17 撤销 R10 的「未核实」；R19 升级 R9；R21 扩展 B10；R22 / X1 加强 R1 并排除「误填 isotonic 列」这一解释；A5 / B3 / X2 复核通过。
- **仲裁结论更新：本轮无未决分歧**。采谁／舍谁已无必要，本条改为记录收敛路径。

**争点 2（非冲突，属两席独立收敛，合并登记）**：`logistic ECE 0.087` — X-05 标「待补证据」（D2），X-09 标「待改」（组4-3 / R1），指向同一缺口 → 合并为 P0-1。

**争点 3（非冲突，属两席独立收敛，合并登记）**：`29.8% / F1 falls slightly` — X-05 回查 C3「部分可回查、lr 方向相反」，X-09 组3-3 / B4 / R12「待改」→ 合并为 P0-2。

**本轮变更记录**（G08 / 四·2）：
- 新增 `RESULTS.check.md`（本文件）：派单行 2 条、总编排已核 10 项、R1–R3 风险登记、两席回件原样转呈、〔示意〕骨架、待补清单 13 条、收口三行、本节仲裁留痕。
- 新增 `.workbuddy/memory/2026-11-13.md`：断点盘点与本轮派单留痕。
- **未改动**：`RESULTS.md`、`real_runs.csv`、`real_summary.json`、`feats.npz` 及全部 `.py` 脚本；未生成 `codec_stress.csv`；未运行任何实验脚本。
- 收口前并入 X-09 补充段（表 A/B、X1–X3、R17–R22），第五节追加原样转呈、第七节追加并列归并表、第八节更新为「3 层 4 批回件」、第九节追加「争点 1 已自行消解」留痕；待补项仍为 13 项，未新增第 14 项。
- 未解决项：P0-1～P0-4、P1-1～P1-9、G01 三问、`codec_stress.csv` 无产物。
- 依据条号：G01／G02／G04／G06／G07／G08、B01／B02、三·1／三·2、四·1／四·2、RD2／RD3／RD5／RD6、F-118／F-120／K-303、C-100／C-300／C-400、X-05、X-09。

## 十、后续事实更正（Agent mode 复核，2026-11-13 20:36）｜P1-2 严重度下调

- 只读复核：`feats.npz` 的 keys 为 `X, y, spk, attack, fid`，其中 `fid` 形状 (2000,)、**2000 个唯一值、全部命中 `audio/flac_D` 下的 flac（missing = 0）**；`spk` unique = 628。
- 因此 X-05 补充段 D3′ / Q2(b) 与 X-09 B10 / R21 中「2,000 条 fid 选样清单未落盘 / 未单独落盘」的事实前提**不成立**：选样清单已随 `feats.npz["fid"]` 落盘。
- 影响：**从 `fid` 出发重建 2,000 条子集并向下游复跑是成立的**；仍不成立的只有「从协议+flac 从零重放抽样」这一步（依赖 `default_rng(2026)` 的连续消耗顺序、`sorted(files)` 顺序、47,400 条目录内容与 numpy 版本）。P1-2 保留但收窄，不再表述为「端到端复跑整体不成立」。
- 处置建议（不改数据）：报告中把 `feats.npz["fid"]` 明确登记为选样清单与复跑入口；D3′ 的「补 fid 选样清单落盘」改为「补复跑入口声明」；D11 保留（rng 顺序与环境版本仍需登记）。
- 依据：RD2 事实与来源、G08 每轮留痕、三·1 可追溯。X-05／X-09 原回件文字不覆盖，本段并列登记。

## 十一、修订落地记录（2026-11-13 20:39，Agent mode）

用户授权「按建议进行修改」，按四层建议执行：
- **已改**：`RESULTS.md`（A+B 类），原件备份为 `RESULTS.md.bak`。改动限于措辞、单位、口径声明、边界句与来源说明。
- **数值零改动**（自动核对）：原文件 50 个数值 token 全部保留（`MISSING from new: []`）；MLP / logistic 两行表格逐格一致；`0.087` 仅加 † 脚注标记；备份与原件字节一致；无 `<<` / 待确认 / TODO 占位。
- **C 类处置（不代填）**：① `0.087` 保留原值并加 † 脚注，写明无法回查、列出 `lr.ece`/`lr.ece_iso`/`mlp.ece_iso` 三个候选、待作者确认；② 29.8% 披露为 852.7/2,860.3 的 10-run means 比值（事实披露，未采用未算过的「逐 run 比率均值」口径）；③ Table II / the paper / the simulation 用 Provenance note 标注源不在工作区，simulation 对照句改为「未在此核实」而非删除。
- **D 类（代码层）按建议未在本轮改动**：`codec_stress.py` 的 T+b 校准与 ffmpeg 并发、`featlib.py` 字典、`run_real_check.py` 的 `fold_split()` 死代码留下一轮；本轮只在 `RESULTS.md` 里注明 flux std 重复与 codec stress 无结论。
- 新增可回查数字均来自 `real_summary.json` / `summarise.py` / 协议与目录计数：140,950、47,400、628、64、4,000 / seed 11、ddof=0、0.448–0.565、3,109→1,977、38.3%、0.077/0.082/0.086、852.7/2,860.3、2026。
- 自检：数值零改动 ✓ 无占位 ✓ 备份完整 ✓ 不代填 ✓ 边界诚实资产保留 ✓ 未越界改代码 ✓ = 6/6。

## 十二、P0/P1 整改落地与 G04 仲裁（2026-11-14，Agent mode）

用户提交一份外部整改方案（P0-1～P0-4 / P1-1～P1-9，附「修改后的 Python 代码片段」与「完整更新后 RESULTS.md」）。本轮为**整改落地轮**，唯一交付物 = 全套 P0/P1 改动的落盘实现。组名沿用「语义攻击·论文作战组」；本轮不新开席位，由总编排执行，两席已于 2026-11-13 收工。

### 12.1 外部方案六处代码块冲突（G04：**舍外部代码块，采真实文件最小补丁**）

| 号 | 外部方案写法 | 真实代码 | 采信与依据 |
|---|---|---|---|
| K-1 | `extract_feats.py` 用 `split("\t")`，取 `fields[0]=fid, [1]=spk, [2]=attack, [3]=label` | 协议是空白分隔 10 列：`spk, fid, gender, codec, q, ttsvc, src, attack, label`；fid 在 **[1]**、attack 在 **[7]**、label 在 **[8]** | **舍**。照抄会让 `fid` 拿到 speaker ID（`D_0062` 型），与 47,400 个 FLAC 文件名（`D_0000000001` 型）零交集 → 抽样池为空。依据 RD2、G07、方案自身「不改变抽样逻辑」目标 |
| K-2 | 按协议 140,950 行顺序构造 bona/attack 列表 | `for fid in sorted(files)`（47,400 文件名排序）后分组，同一个 `default_rng(2026)` 连续 shuffle 9 次 | **舍**。输入顺序不同 → 选中的 fid 全变，与方案「零数值改动」冲突 |
| K-3 | `featlib.py` 10 标量写成 6 个真值 + `0.,0.,0.,0.`；`compute_stft(): pass` | 真实 10 标量：logdur / e.mean / e.std / cent.mean / cent.std / **flux** / **flux 重复** / roll / zcr / zcr_std | **舍**。会直接改特征数值且不可运行。方案 A 的**意图**（只改注释）采信 |
| K-4 | `decode_audio` 改回 `stdout=PIPE` | `featlib.decode` 特意用临时 wav，注释写明「pipe 在 10 并发下耗尽内存」 | **舍**。会把已修的内存保护改回去，正好踩 P0-4 |
| K-5 | `run_real_check.py` 用 scipy `minimize` 重写 `fit_temperature`，main 循环写 `pass` | 真实是 **torch LBFGS**（`a=logT, b`），训练/校准/评估循环完整 | **舍**。校准数值会全变，`real_runs.csv` 全表失效 |
| K-6 | 「在 `real_summary.json` 顶层加 `stat_metadata`」并放到 `run_real_check.py` | 该 json 由 `summarise.py` 写；`run_real_check.py` 只写 `real_runs.csv`。方案 P0-1 又要求「仿真输出 csv/json 维持原样」 | **舍**（方案内部自相矛盾）。G04 裁决见 12.2 |

### 12.2 G04 冲突仲裁留痕

- **争点**：P1-4 要「在 `real_summary.json` 顶层新增 metadata 块」；P0-1、第三节改动清单总览、风险控制第 1 条均要求「不改动任何仿真输出 csv/json」「现有 `real_summary.json` 保持不变」。
- **采 P0-1，舍 P1-4 的落点**：判定 P0-1 为硬约束（用户反复强调零数值改动、产物全部保留）。统计口径改为**独立 sidecar** `stat_metadata.json`，`real_summary.json` 字节不变；`delta_ci95` 仍在其顶层。
- **依据**：G04 冲突仲裁写明采谁舍谁、RD2 事实与来源、G08 每轮留痕、W-07-14 与 F-120 登记行。方案样稿中「All bootstrap CI results are stored in `real_summary.json → stat_metadata`」一句为事实错误，已在 `RESULTS.md` S2/S3 与 `REVISION_NOTE.md` 更正为 `delta_ci95` 顶层键 + 独立 sidecar。
- **另两处措辞更正**（非冲突，属方案样稿自相矛盾）：① P1-6 要求「全篇统一 50-dim / 4-channel」，样稿正文却写 `50-d` / `four-channel` → 已真正统一；② 样稿写「codec stress script logic has been repaired」且未说明未跑数 → 已改为「已修复、**本轮未执行**、无 `codec_stress.csv`、不作 waveform-codec 结论」。

### 12.3 实际落地清单（对照方案九条）

| 条 | 落地 | 数值影响 |
|---|---|---|
| P0-1 | `0.087` 保留 + † 脚注；F-120 登记「文稿录入异常／仿真输出未改动／不需重跑」 | 无 |
| P0-2 | S3 Reading 按 MLP / logistic 分述，写明 29.8% = 852.7/2,860.3 且为 10-run 均值之比 | 无 |
| P0-3 | S1 Provenance 块；三个 `.py` docstring 去外部表号硬引用、写明 50-dim vs 4-channel | 无 |
| P0-4 | `codec_stress.py`：复用 `fit_temperature` 的 T+b 链（15% clean holdout、floor 64、一组参数套全部条件）；`MAX_WORKERS=4`／默认 2 workers；每条件独立有界进程池 + `.npz` 断点 + `--conds` 分批；头部 WARNING 明示不可比 | **未执行**，无产物 |
| P1-1 | `extract_feats.py` 常量与注释区分 785/628、`flac_D_aa`↔`audio/flac_D`；S2 三级规模 | 无 |
| P1-2 | `write_sampling_metadata()` + `--metadata-only`；生成 `sampling_metadata.json`（值全部从已有 npz/协议/目录离线读回） | 无，未重抽样 |
| P1-3 | 方案 A：`featlib.py` 仅改 docstring 与 `features()` 注释，登记 flux mean 重复维 | 无，`feats.npz` 字节不变 |
| P1-4 | `summarise.py` 的 `STAT_METADATA` + 独立 `stat_metadata.json`；S2 全口径披露 | 无 |
| P1-5 | 单位统一 `per 1,000 calls`、F1 补 SD（4 个值均回查 `real_summary.json`）、Δ 定义、CI 仅 MLP、箭头语义 | 无（新增披露值可回查） |
| P1-6 | 术语等价声明、缩写统一 50-dim / 4-channel | 无 |
| P1-7 | `exp22_*` 命名历史注释 + S3 说明 + `stat_metadata.json` | 无 |
| P1-8 | 删 `fold_split()` 占位死代码，封装 `speaker_grouped_fold_split()` 并由 main 调用 | 无（等价性已验证） |
| P1-9 | 新建 `data/数据分析过程记录表.csv`（F-120 六列，17 行）与 `data/官方口径登记表.csv`（W-07，17 项，新旧成对） | 无 |

### 12.4 验证结果

- `python -m py_compile` 对 5 个 `.py` **全通过**。
- **切分等价性**：新旧逻辑在 2 seeds × 5 folds 上逐元素比对 `FOLD_SPLIT_EQUIVALENT = True`；各折 `n_te` = `[406,406,378,380,430]` / `[379,467,406,396,352]`，与 `real_runs.csv` 完全一致。
- **产物字节不变**：`feats.npz` / `real_runs.csv` / `real_summary.json` 的 sha256 与 `backups/2026-11-14/` 一致（`sha256sum -c` 三项 OK）。
- **报告数值保全**：新版 `RESULTS.md` 相对上一版的 70 个数值 token，`MISSING` 5 项均为 token 化差异（`0.448→0.4485` 更精确；`20,`／`5,` 为 `c_FN = 20`／`c_FP = 5` 的逗号；`64` 在 `max(64, …)` 内），**无数值丢失**；`0.087†` 保留；新增 4 个 F1 SD 与 `93,550 = 140,950 − 47,400` 均可回查。
- **无残留占位**：`RESULTS.md` 全篇无未填占位标记、无未完成标记、无待回填标记（自动检索为空）。
- **两张登记表列数**：F-120 六列 18 行（含表头）、W-07 七列 18 行，逐行一致。
- **未生成** `codec_stress.csv`；未重跑主实验；未改 `feats.npz` / csv / json。

### 12.5 边界与未决

- P0-1 的 `0.087` 仍**待作者确认**（G06 不代填），本轮只登记异常、不改数、不重跑。
- codec stress **代码已修但未执行**，本稿仍不含 waveform-codec 结论；补跑需在用户本机进行（红线 B01 不代跑实验）。
- G01 三问（交给谁看／处在哪环／有什么料）仍未答清；稿件全文、Table II 数值、仿真结果、审稿意见原文仍缺。
- P1-3 方案 B（补真实 flux-std）会改 `feats.npz` 并需整套重跑，本轮**未采用**，已列入 S5 待办。

**自检：6/6**（字段齐 ✓ 格式对 ✓ 无占位未清 ✓ 无承诺用语 ✓ 无编造（六处冲突均据实登记）✓ 无越界（未代跑实验、未代填 ECE）✓）。

## 十三、P0-1 结清：G06 作者真值裁决（2026-11-14 10:31，Agent mode）

**性质**：作者拍板后的执行落地（G06 作者确认制已满足）。本轮**不新派单、不出新专业结论**；前十二节两席回件与此前所有「待确认」表述按 G08 **保留不删**，作为 V3 新旧成对证据；`backups/2026-11-14/`（整改前）与 `backups/2026-11-14-g06/`（定稿前）两份快照均不覆盖。

### 13.1 作者裁决与三问核验（原文要点逐条入账）

| 项 | 作者结论 |
|---|---|
| Q1 | 稿件正文无其他冲突 ECE 描述；主 Table II 为合成仿真，与本 ASVspoof5 锚点实验是两套特征，互不冲突 |
| Q2 | 完全匹配 G06 真值 `lr.ece.mean = 0.0772`（temperature+bias 校准 ECE），与表格列定义一致 |
| Q3 | 审稿人问的是 temperature+bias 校准 ECE，不是 isotonic 校准 |

**编排层判定**：Q1/Q2/Q3 构成 G01 三问的**部分补齐**——①读者＝审稿人、②环节＝返修、③材料＝仿真输出 json 已明确；但稿件全文、Table II 数值、仿真结果与审稿意见原文**仍未进入工作区**，G01-③ 未完全答清。按 G02 本轮不扩面、不派新单。

### 13.2 落地动作（`RESULTS.md` 唯一一次文稿侧数值修正）

| # | 位置 | 旧 | 新 |
|---|---|---|---|
| A1 | S3 表格 logistic / ECE 单元格 | `0.087† (0.019)` | `0.0772 (0.019)` — **只替换该单元格**，整行其余 8 格、`3,886` 千分位体例与列分隔均未动（作者给出的整行里 `3 886` 为窄空格千分位，整行替换会引入字符漂移） |
| A2 | S3 表格下 † 脚注（6 行） | 保留并声明待确认 | 整段删除 |
| A3 | S4(6) `**Open cell.** … pending author confirmation` | 存在 | 删除；S4 余 5 条，编号不需重排 |
| A4 | S5 第 1 条 ECE 待确认项 | 存在 | 删除；原 2–6 条重编号为 1–5 |
| A5 | 顶部 Revision note | 「no reported value was changed … cell flagged for author confirmation」 | 改为准确表述：**仿真输出零改写**，唯一文稿侧修正为 `0.087 → 0.0772`（对齐 `lr.ece.mean = 0.0772400649`），属录入订正、不需重跑 |
| A6 | 文件清单 `codec_stress.py (repaired, not executed)` | 上一轮补跑后的遗留错误 | 改为 `repaired and executed separately on 2026-11-14`（事实一致性，非本轮新增结论） |

**真值回查（本轮实测）**：`real_summary.json` `lr.ece.mean = 0.07724006491927238` → 0.0772；`lr.ece.sd = 0.01868545306800695` → 0.019。`lr.ece_iso.mean = 0.0823`、`mlp.ece_iso.mean = 0.0861` 均非采用值，isotonic 对照仍未进表，与作者 Q3 一致。

### 13.3 同步回写

`REVISION_NOTE.md` §1（限定为 released outputs 不变 + 登记唯一文稿侧例外）、§3 两条 bullet、§4 产物表与行数、§5 重构为「已结清／仍未决」并保留 V3 成对记录；F-120 追加 1 行（22 行含表头）、W-07 追加 `W-07-19`（21 行含表头，结清 P0-1，历史行不删）；`.workbuddy/memory/2026-11-14.md` 追加本轮。`CODEC_STRESS_RUNBOOK.md` / `CODEC_STRESS_RESULTS.md` / `verify_codec_stress.py` 无 `0.087`／†／待确认 字样，未改动。

### 13.4 边界与验收

- `feats.npz` / `real_runs.csv` / `real_summary.json` 的 sha256 仍与 `backups/2026-11-14/` 一致，**仿真输出一个字节都没改**；主实验未重跑；codec stress 结果隔离不变，`verify_codec_stress.py` 仍 9/9 PASS（该校验器无依赖 `0.087†` 的断言）。
- `RESULTS.md` 全文无 `0.087` / `†` / 待确认 / `pending` / `confirmation` 残留（自动检索为空）。`REVISION_NOTE.md` 的 7 行命中（L21/26/27/84/114/115/117）**全部是 V3 成对历史记录**——描述「由旧值改为新值」「旧 † 脚注已删除」「当时状态为待确认」，不是仍在生效的脚注或待确认标记；该文件无生效中的 pending 项（§5 已重构为「已结清／仍未决」）。`RESULTS.check.md` 前十二节与两份备份中的历史表述按 G08 保留不删。
- 数值 token 审计（相对定稿前快照）：`removed = [0.077, 0.082, 0.086, 0.087]`、`added = [0.0772, 0.0772400649]`；移除的四项**全部来自被整段删除的 † 脚注**（脚注内列的三个候选值与旧单元格值），非结果数值丢失；S3 表格 logistic 行其余 8 格逐格未动，MLP 行完全未动。精确复核：logistic 行第 4 个单元格（表头 ECE 列，索引 3）= `0.0772 (0.019)`。
- `RESULTS.check.md` 中唯一命中 `TODO` 的是 §11 L408 的历史验收句「无 `<<` / 待确认 / TODO 占位」，属**描述性文字而非未清占位**，按 G08 保留；避免后续轮次自动检索误报。
- **登记一条格式体例待判项（不代改、不扩面）**：ECE 列 MLP 为三位小数 `0.075`，本次按作者指定写四位 `0.0772`；同列精度不一致属 C-300 体例问题，是否统一（如 `0.077`）交格式席／作者判定，本轮遵从作者给定值。
- **仍未决**：G01-③ 稿件全文、Table II 数值、仿真结果、审稿意见原文；P1-3 方案 B（未采用）。

**自检：6/6**（字段齐 ✓ 格式对 ✓ 无占位未清 ✓ 无承诺用语 ✓ 无编造 ✓ 无越界（作者已裁决，本轮只执行落地与留痕）✓）。

## 十四、v1.1 可读性与一致性轮（2026-11-14 晚，作者审阅清单）

**本轮唯一交付物**：`RESULTS.md` v1.1 文稿层修订 + `RESULTS.pdf` v1.1 重出 + 可复现构建脚本 `build_results_pdf.py`。判据全部由作者逐条给出，本轮为执行落地与取证，不新拉席位、不代席产出专业结论。改动前快照：`backups/2026-11-14-v11/`（6 份）。

### 14.1 G04 前置取证：所谓「句子截断」不成立

作者对 PDF 提出多处「句子 abruptly 结束」「数字与单位粘连」「`@0.5` 变成 `0.0.0.5`」。逐行核对 `RESULTS.md` 源文件与 `RESULTS.pdf` 文本层（`pdftotext -layout`）后判定：**均为阅读／复制侧按行宽截断并吞掉空格的假象，文件本身没有缺字**。

| 作者举的断句 | PDF 文本层实际内容 | 判定 |
|---|---|---|
| §3 末尾「…are not in this」 | L87 `…the simulation results are not in this workspace.` | 完整 |
| §4(3)「computed but not」 | L105 `…and the isotonic control are computed but not tabulated.` | 完整 |
| §4(4)「the MLP Δ」 | L106 `The 95% CI is computed for the MLP Δ only.` | 完整 |
| §4(5)「628 is derived from non-stratified」 | L107–108 `…628 is derived from non-stratified sampling.` | 完整 |
| §4(2)「9/9checks」 | L103 `…enforces these guardrails (9/9 checks PASS).` | 完整 |
| `2,000utterances` / `47,400FLAC` / `0.5threshold` / `S1Motivation` | 源文件与 PDF 分别为 `2,000 utterances` / `47,400 FLAC` / `0.5 threshold` / `S1 Motivation` | 空格本就存在 |
| 表头「△」vs 正文「Δ」 | 源文件 `△` 出现 0 次、`Δ` 5 次，为同一符号 | 字体渲染差异 |
| `@//0.0.0.5/`、`@//rule/` 附件引用 | PDF L48 为 `@0.5` / `@rule` | 阅读侧转义假象 |

**按 G06 不代填、不「补全」**：若照作者字面去补句，会重复文字并制造真错误，故该类 6 处**不改**。但取证发现一个**真实排版缺陷**，构成上述观感的根源：v1.0 表格为 `table-layout: fixed` + 固定列宽，Δ 单元格被折成 `853 [665,` / `1,036]`，表头折成 `cost @0.5 [per` / `1,000 calls]`，数值单元格的 SD 也另起一行。**本轮已从生成链路修掉**（见 14.4）。

### 14.2 作者清单逐条处置

| # | 作者意见 | 处置 | 依据／落点 |
|---|---|---|---|
| 1 | 补全多处残句 | **不改**（不成立，14.1 取证）；改从生成链路消除折行观感 | G06 不代填；14.1 |
| 2a | Δ 写法 `853 [665, 1036]` | **已改**：`853 [665, 1,036]` → `853 [665, 1036]`，区间内不用千分位 | S3 表；CI 源 `[665.3, 1036.1]` |
| 2b | `3,886 (782)` 缺空格 | **无需改**：源文件与 PDF 本就有空格，属阅读侧丢失 | 14.1 |
| 2c | ECE 同列精度 | **G04 仲裁**：保留 G06 真值 `0.0772`，采作者给的第二个选项「表注说明」 | 表注 (3)；见 14.3 |
| 2d | 表头 △ / 正文 Δ | **无需改**：源文件统一 `Δ`，`△` 计数 0 | 14.1 |
| 3a | 正文 852.7/2,860.3 与表 853/2,860 | **已补**：「computed from **unrounded** values; the table shows the rounded `853 / 2,860`」 | Reading 段 |
| 3b | logistic 38.3% 未给 | **已补**到表注 (2)，并给 `1,490 / 3,886` | 表注 (2) |
| 4 | 表注重复 Δ 定义 + 正值方向 | **已补**：表注 (1) 与 §S2 Statistics 各一次，`a positive Δ means the cost rule is cheaper` | 表注 (1) |
| 5 | logistic 无 CI 的原因 | **已补代码事实**：`summarise.py` 的 paired bootstrap 只对 MLP Δ 实现，属实现范围而非统计判断；§S5(5) 登记只读复算值并标待拍板 | §S2 Statistics、§S5(5)；见 14.4 |
| 6 | SD 用代码级描述 | **已改**：正文改为 `population SD over the 10 runs`，`statistics.pstdev, ddof = 0` 移入括号并指向 `stat_metadata.json` | §S2 Statistics |
| 7 | AUPRC > AUROC 反常 | **已补** sanity check：1:1 子集下 AUPRC 基线是正例率 ≈ 0.5，非低先验 | 表注 (4) |
| 8 | F1 取舍讨论偏弱 | **已补**量化权衡：MLP 每千次呼叫省 ≈852 成本、F1 降 0.011；logistic 两者同改善 | Reading 第二段 |
| 9 | Revision note 喧宾夺主 | **已改**：整块移到 `Appendix A. Revision history`，正文开头只留 `Version v1.1 — revised 2026-11-14` | 标题下／附录 |
| 10 | 章节编号／交叉引用不统一 | **已统一**为 `§S<n>`：`§S2 Statistics`、`§S4(2)`、`§S5`；标题 `S1 Motivation` 本就有空格 | 全文 |
| 11 | 60% 重加权打断阅读流 | **已改**为 S3 末尾明确标注 `post-hoc re-weighting (not a measured cost)` 的引用块，数字全保留 | S3 末 |
| 12 | option B 影响评估 | **已补但只作诚实声明**：§S5(6) 写明「影响**尚未评估**、不作稳健性结论」，预测性判断不代写 | §S5(6)；B01 |
| 13 | 与主稿件接口可操作句 | **已补**：§S4(1) `Operational reading` 一句，限定为只支持方向性结论、不支持绝对成本量级迁移 | §S4(1) |
| 14a | 数字与单位空格 | **已核实**源文件齐全，阅读侧丢失，未改 | 14.1 |
| 14b | `@0.5` / `@rule` 全称 | S2 Decoders 已给定义，全文固定一种写法，未改 | §S2 Decoders |
| 14c | `c_FP=5, c_FN=20` 公式化 | **已补** §S2 Cost：`E[cost] = c_FP · P(false alarm) + c_FN · P(miss)`，并说明表中值 ×1,000 | §S2 Cost |
| 14d | 页脚加版本号 | **已补** `RESULTS.md v1.1` 到页脚、PDF 元数据、版本行与附录 | PDF／md |

### 14.3 G04 仲裁：ECE 精度的新旧指令冲突

- **旧指令（同日 10:31，G06 作者裁决）**：明确指定单元格为 `0.0772 (0.019)`，四位小数，对齐 `lr.ece.mean = 0.0772400649`。
- **新指令（本轮 §一·2）**：「即使 0.0772 是修订更正值，也应统一为 3 位小数 (`0.077`)，**或在表注中说明**」——作者给了两个互斥选项。
- **裁决**：采「表注说明」，**保留 `0.0772`**。依据 G04（冲突留痕）+ G06（真值不擅自推翻）+ 最小改动。表注 (3) 写明 MLP 三位为原报告精度、logistic 四位为保留 G06 订正值，`the mixed precision is intentional, not a typo`。§13 登记的 C-300 体例待判项由此结清一半：是否改为 `0.077` 仍留作者一句话翻转。
- 本轮**未改任何落盘数值**。

### 14.4 logistic Δ 区间：只读复算，未上表

作者问「补一个 logistic 的 CI 成本不高」。按同法（seed 11 / 4,000 次 paired bootstrap / 10 个 Δ）离线复算，**只读 `real_runs.csv`、不写盘、不改 `real_summary.json`**：

| detector | mean Δ | cost @0.5 | 相对降幅 | 95% CI |
|---|---|---|---|---|
| MLP | 852.7 | 2,860.3 | 29.8% | **[665.3, 1036.1]** ← 与落盘 `delta_ci95` 完全一致，证明方法等价 |
| logistic | 1,489.5 | 3,885.6 | 38.3% | **[987.8, 2066.6]** ← 同法复算 |

**处置**：数值写入 §S5(5) 作为 open item，**没有进 S3 表、没有改 `stat_metadata.json`、没有改统计口径**。理由：是否报告属统计席／作者的方法判断（B01 不代判、不越席），且 `stat_metadata.json` 现登记 `bootstrap only applied to mlp delta`，若采纳须成对更新。§S2 同时把「只对 MLP 实现」写成**实现范围事实**，正面回应「选择性报告」的可能质疑，而不替统计席解释理由。

### 14.5 PDF 生成链路修复（本轮技术债）

`build_results_pdf.py` 由临时脚本正式落到工作区，改动：
- 表格改 `table-layout: auto` + 全单元格 `white-space: nowrap`、去掉 `<colgroup>` 固定列宽、字号 8pt → **所有数值单元格与 Δ 区间单行显示**；`pdftotext -layout` 逐项验证 `0.867 (0.027)` / `0.0772 (0.019)` / `2,860 (355)` / `853 [665, 1036]` / `3,886 (782)` 均在同一行；`xMax = 549.9pt`，未溢出 16mm 页边距。
- 校验段去掉在本机 DLL 不兼容的 `import fitz`，改用 `pypdf`；新增机器判据 `delta interval unwrapped`（区间须为连续字符串）与禁用词检查。
- 页脚／元数据／版本行加 `v1.1`。

**验收**：4 页 A4（595 × 842 pt）；`missing key strings: []`、`forbidden strings found: []`、`cjk path extracted: True`、`delta interval unwrapped: True`；逐页渲染视觉检查无重叠、无裁切、无缺字，中文路径与 § / Δ / ≈ 正常，四页页脚均带 v1.1。

### 14.6 同步回写与边界

`REVISION_NOTE.md`（§4 产物表、§5 第 3 条体例待判项、新增 §6）、F-120 +1 行（23 行含表头）、W-07 +1 行（22 行含表头）、`.workbuddy/memory/2026-11-14.md` 追加本轮。`RESULTS.pdf` 由修订后的 `RESULTS.md` 重新生成，二者同源。

- 三份主产物 `feats.npz` / `real_runs.csv` / `real_summary.json` 的 sha256 仍与 `backups/2026-11-14/` 一致；主实验未重跑。
- `verify_codec_stress.py` **9/9 PASS**：N1 要求 S3 只有 2 行 detector、无 `codec`/`opus`/`g711`/`Table II`；N2 要求 S4 保留 `must not be merged into the main result tables` 与 `not quantitatively comparable`。本轮移动内容、新增表注、新增附录后两条断言仍成立，codec stress 结果隔离未动。
- **未代写**：logistic CI 是否上报、option B 对结论的预期影响、统计量口径变更 —— 三项均只给数据事实／诚实声明／open item，按 B01 留作者与统计席。
- **仍未决**：G01-③ 稿件全文、Table II 数值、仿真结果、审稿意见原文；ECE 是否统一为 `0.077`；logistic CI 是否采纳；P1-3 方案 B。

**自检：6/6**（字段齐 ✓ 格式对 ✓ 无占位未清 ✓ 无承诺用语 ✓ 无编造（14.1 逐行取证、14.4 复算可复现）✓ 无越界（不补不存在的断句、不代填统计结论、不改已发布数值）✓）。
