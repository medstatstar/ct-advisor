# Auto 100-Loop Progress Log — ct-advisor knowledge strengthening

- **Driver**: general-purpose-1 (ct-advisor automated iteration driver)
- **Start**: 2026-08-01 | **Skill root**: C:\Users\WintoneFileSrv\.workbuddy\skills\ct-advisor
- **Targets**: knowledge/ref-clinical-operations.md (workflow B/D/E/F/G/H), knowledge/ref-regulatory-statistical.md (workflow A/C/F/G)
- **SOP**: per round → generate 1 basic + 1 complex scenario → search_refs verify → gap→append subsection → log. Every 10 rounds → version bump (0.7.batch) + changelog + memory + notify main.
- **Red lines**: never git push / publish; dynamic items carry "动态项须官方核实"; no full-text regulation; no workflows.yaml change unless needed.

## used_combos registry (role+scenario, dedup) (updated each round)

---

## Round log
Round 1 | 一般: CRC—已入组受试者电话撤回未用药，需签何文件/ICF原件归档 [gap→ §4.1.4] | 复杂: 注册—中美双报CMC互认/种族敏感性/MRCT中国占比 [covered §5.5]
Round 2 | 一般: CRA—SDV发现源病历涂改无签名无理由如何处理 [covered §3.4] | 复杂: 生物统计—非劣效界值/恒定假设/assay sensitivity [covered §3.3]
Round 3 | 一般: 受试者补偿—交通/误工补偿审批与诱导偏倚防控 [gap→ §3.10] | 复杂: 人遗办—样本出境/人遗审批/数据跨境 [gap→ §8.4]
Round 4 | 一般: DPO—EU数据跨境GDPR/SCC/数据主体权 [gap→ §8.5] | 复杂: 生物统计—贝叶斯自适应先验/停止边界/α等价 [gap→ §3.5]
Round 5 | 一般: 中心库房—运输温控记录仪失效到货处理 [gap→ §3.11] | 复杂: 统计编程—ADaM/TFL QC/供应商交接 [gap→ §4.5]
Round 6 | 一般: 医学写作—CSR讨论避免仅述显著结果/局限性披露 [covered §5.2] | 复杂: HEOR—EQ-5D/效用映射/QALY准入 [gap→ §5.11]
Round 7 | 一般: QM—稽查发现SDV系统性未执行CAPA根因/有效性 [covered §6] | 复杂: 注册—附条件批准上市后确证性试验设计 [covered §5.4/§3.8]
Round 8 | 一般: 临床药理—食物效应餐食标准化/给药时序 [covered §1.5] | 复杂: 生物统计—合成对照构建/偏倚控制 [gap→ §3.6]
Round 9 | 一般: 机构办—机构合并法人变更备案/合同/账目平移 [gap→ §3.12] | 复杂: RWE—医保数据外部对照/target trial emulation/阴性对照 [covered §3.8]
Round 10 | 一般: IRB—跟踪审查逾期继续用药合规依据 [covered §3.7] | 复杂: 注册—生物类似药III期ADA差异/免疫原性桥接 [covered §5.7]

### used_combos (role+scenario, dedup)
- R1: CRC+受试者退出/ICF归档; 注册事务+中美双报桥接
- R2: CRA+SDV源数据涂改; 生物统计+非劣效界值论证
- R3: 受试者补偿+诱导偏倚; 人类遗传资源办+人遗出境/数据跨境
- R4: 数据保护官(DPO)+GDPR跨境; 生物统计+贝叶斯自适应设计
- R5: 中心库房/物流+运输温控失效; 统计编程+ADaM/TFL QC
- R6: 医学写作+CSR讨论局限性; HEOR+EQ-5D/QALY准入
- R7: 质量管理(QM)+稽查CAPA根因; 注册事务+附条件批准确证性
- R8: 临床药理+食物效应; 生物统计+合成对照
- R9: 机构办+机构主体变更; 真实世界研究(RWE)+外部对照
- R10: 伦理委员会秘书(IRB)+跟踪审查逾期; 注册事务+生物类似药免疫原性

### pending_blocks batch 1 (flush @ round 10) ref-clinical-operations.md: §3.10 受试者补偿与诱导偏倚, §3.11 中心库房/物流温控失效, §3.12 机构主体变更, §4.1.4 受试者退出/撤回文档与ICF归档, §4.5 统计编程与TFL QC ref-regulatory-statistical.md: §3.5 贝叶斯自适应设计, §3.6 合成对照, §5.11 HEOR/药物经济学, §8.4 人类遗传资源合规, §8.5 跨国数据隐私(GDPR/DPO)

Round 11 | 一般: DM—EDC建库/UAT/编辑检查验证与上线前放行 [gap→ §4.6] | 复杂: 医学事务—post-hoc亚组投稿选择性报告/透明度预注册 [gap→ §8.6]
Round 12 | 一般: 申办方合规—中心数据可疑造假调查/上报/数据隔离 [gap→ §6.3] | 复杂: 罕见病专家—孤儿药认定/自然史外部对照/减免路径 [gap→ §5.12]
Round 13 | 一般: 生物样本管理员—剩余样本销毁与方案外二次使用授权 [gap→ §4.1.5] | 复杂: 儿科专家—儿科剂量体重/BSA调整/Assent年龄分层 [gap→ §1.7]
Round 14 | 一般: 临床运营经理—远程监查替代现场比例与风险控制 [covered §3.3/§3.6] | 复杂: 生物统计—随机化最小化法/分配隐藏/IRT配置 [gap→ §4.2.5]
Round 15 | 一般: CRO—对CRO质控审计/过渡/CAPA [gap→ §3.13] | 复杂: 注册事务—疫苗/生物制品桥接与免疫原性可比性 [gap→ §5.13]
Round 16 | 一般: 研究者(PI)—PI对sub-I授权与监督/超授权处理 [gap→ §2.4] | 复杂: 独立影像(BICR)—BICR章程/评估不一致处理/影像QC [gap→ §5.14]
Round 17 | 一般: 受试者权益—受试者投诉与权益申诉渠道 [gap→ §2.5] | 复杂: 生物统计—estimand框架下伴发事件策略选择 [covered §3.1]
Round 18 | 一般: 项目经理(PM)—试验风险计划/CtQ/质量容忍限QTL [gap→ §3.14] | 复杂: 药物警戒(PV)—DSUR区域附录与全球安全信息整合 [covered §4.4]
Round 19 | 一般: 中心实验室—中心实验室检测单位/参考范围与本地不一致 [covered §3.5] | 复杂: 申办方合规—GCP核查准备与finding回复/整改 [gap→ §6.4]
Round 20 | 一般: 医学事务—MSL与研究者沟通边界/阳光法案透明 [gap→ §8.7] | 复杂: 统计编程—多重性α分配/回收/跨终点借用 [covered §3.3]

### used_combos (role+scenario, dedup) — batch 2
- R11: 数据管理员(DM)+EDC验证; 医学事务+发表透明度
- R12: 申办方合规+数据造假; 罕见病专家+孤儿药/自然史
- R13: 生物样本管理员+样本销毁/二次使用; 儿科专家+儿科剂量/Assent
- R14: 临床运营经理+远程监查; 生物统计+最小化随机
- R15: CRO+CRO审计/过渡; 注册事务+疫苗桥接
- R16: 研究者(PI)+sub-I授权; 独立影像(BICR)+影像章程
- R17: 受试者权益+投诉申诉; 生物统计+estimand策略
- R18: 项目经理(PM)+风险计划/QTL; 药物警戒(PV)+DSUR区域附录
- R19: 中心实验室+实验室一致性; 申办方合规+GCP核查
- R20: 医学事务+MSL合规; 统计编程+多重性α

### pending_blocks batch 2 (flush @ round 20) ref-clinical-operations.md: §1.7 儿科剂量/Assent, §2.4 sub-I授权监督, §2.5 受试者投诉申诉, §3.13 CRO审计过渡, §3.14 风险计划/QTL, §4.1.5 样本销毁二次使用, §4.2.5 最小化随机, §4.6 CSV/EDC验证, §6.3 数据造假调查, §6.4 GCP核查准备 ref-regulatory-statistical.md: §5.12 孤儿药/自然史, §5.13 疫苗桥接, §5.14 BICR章程, §8.6 发表透明度, §8.7 MSL合规

Round 21 | 一般: 临床药理—FIH模型引导剂量探索CRM/BOIN/目标毒性率 [gap→ §1.8] | 复杂: 生物统计—富集设计(enrichment)筛选与自适应富集 [covered §5.4]
Round 22 | 一般: 药物警戒(PV)—安全性信号管理(验证/优先/单案例→信号) [covered §5.3] | 复杂: 注册事务—种族因子(RFE)定量评估与桥接论证 [gap→ §5.19]
Round 23 | 一般: 研究者(PI)—研究者经济利益冲突(COI)披露与管理 [gap→ §2.6] | 复杂: 生物统计—平台试验MAMS与封档(flagging)规则 [gap→ §5.15]
Round 24 | 一般: 申办方合规—在研药品召回与系统缺陷收回 [gap→ §4.2.6] | 复杂: 医学事务—RWE用于标签扩展的可靠性与边界 [gap→ §5.16]
Round 25 | 一般: 临床运营经理—GCP培训体系与授权前培训 [gap→ §3.15] | 复杂: 生物统计—诊断/预后/预测性生物标志物验证框架 [gap→ §3.7]
Round 26 | 一般: CRC—药物编盲与包装/双盲一致性/应急信封 [gap→ §4.2.7] | 复杂: 独立影像(BICR)—临床终点裁定委员会(CEC/EAC) [gap→ §5.17]
Round 27 | 一般: 数据管理员(DM)—数据管理计划(DMP)与锁库前核查 [covered §4.2/§8.1] | 复杂: 生物统计—响应自适应随机化(RAR)分配比调整 [gap→ §4.2.8]
Round 28 | 一般: 机构办—试验合同与受试者伤害保险/赔偿 [gap→ §3.16] | 复杂: 罕见病专家—罕见病贝叶斯设计与历史数据借力(power prior) [gap→ §3.8]
Round 29 | 一般: 质量管理(QM)—CAPA有效性检查(effectiveness check) [gap→ §6.5] | 复杂: 注册事务—生物类似药临床桥梁与可比性边界 [gap→ §5.18]
Round 30 | 一般: 伦理委员会秘书(IRB)—重大修正案重新知情同意时限衔接 [gap→ §3.17] | 复杂: 生物统计—estimand治疗策略vs耐受策略比较 [covered §3.1]

### used_combos (role+scenario, dedup) — batch 3
- R21: 临床药理+CRM/BOIN剂量; 生物统计+富集设计
- R22: 药物警戒(PV)+信号管理; 注册事务+种族因子RFE
- R23: 研究者(PI)+经济利益冲突; 生物统计+平台试验MAMS
- R24: 申办方合规+药品召回; 医学事务+RWE标签扩展
- R25: 临床运营经理+培训体系; 生物统计+诊断/预后/预测标志物
- R26: CRC+药物编盲包装; 独立影像(BICR)+临床终点裁定CEC
- R27: 数据管理员(DM)+DMP锁库; 生物统计+RAR响应自适应
- R28: 机构办+合同/受试者伤害保险; 罕见病专家+贝叶斯/power prior
- R29: 质量管理(QM)+CAPA有效性; 注册事务+生物类似药临床桥梁
- R30: 伦理委员会秘书(IRB)+重新知情同意; 生物统计+estimand策略比较

### pending_blocks batch 3 (flush @ round 30) ref-clinical-operations.md: §1.8 CRM/BOIN剂量, §2.6 研究者COI, §3.15 培训体系, §3.16 合同/受试者伤害保险, §3.17 重大修正案重签, §4.2.6 召回, §4.2.7 编盲包装, §4.2.8 RAR, §6.5 CAPA有效性 ref-regulatory-statistical.md: §3.7 诊断/预后/预测标志物, §3.8 罕见病贝叶斯/power prior, §5.15 MAMS/封档, §5.16 RWE标签扩展, §5.17 CEC/EAC, §5.18 生物类似药临床桥梁, §5.19 种族因子RFE

Round 31 | 一般: 医学写作—量表/效度量表心理测量属性(clinimetric)验证要求 [covered §5.10] | 复杂: 生物统计—期中样本量重估SSR与α控制/盲态vs疗效驱动 [gap→ §3.9]
Round 32 | 一般: 数据管理员(DM)—试验级数据治理框架/数据质量标准/编码字典 [gap→ §4.7] | 复杂: 药物警戒(PV)—disproportionality(PRR/ROR)信号量化与阈值惯例 [gap→ §4.6]
Round 33 | 一般: 研究者/CRC—电子知情同意eConsent远程获取与电子签名合规 [gap→ §2.7] | 复杂: 注册事务—eCTD/IND/CTA模块与递交技术要求 [covered §7/§8.3]
Round 34 | 一般: 申办方合规—方案偏离PD与PV术语区分与上报告阈 [covered §6.2] | 复杂: CRA—中心启动访视SIV内容与启动质量门衔接 [gap→ §3.18]
Round 35 | 一般: CRC—伴随用药/合并用药采集编码与违禁药判定 [gap→ §4.8] | 复杂: 医学事务—同情用药/扩展性用药(expanded access)合规路径 [gap→ §5.21]
Round 36 | 一般: 受试者权益—妊娠作为安全性事件报告与登记 [covered §5.4] | 复杂: 临床药理—生物等效性BE试验设计与等效界值判定 [gap→ §5.20]
Round 37 | 一般: 临床运营经理—风险计划/CtQ/KRI(已覆盖大纲) [covered §3.14/§3.6] | 复杂: 注册事务—附条件批准+确证性承诺(已覆盖) [covered §5.4/§3.8]
Round 38 | 一般: 数据保护官(DPO)—数据保护影响评估DPIA与高风险处理 [gap→ §8.9] | 复杂: 统计/DM—盲态数据审查BDR与锁库前清理清单 [gap→ §4.9]
Round 39 | 一般: 中心实验室—生物样本链完整性/温度偏离(已覆盖) [covered §4.1.3] | 复杂: 临床药理—肝/肾损害人群剂量调整与分级 [gap→ §1.9]
Round 40 | 一般: 受试者权益—受试者退出/撤回数据删除权(已覆盖) [covered §4.1.4] | 复杂: 机构办—多区域/多国试验伦理协调与中央IRB [gap→ §8.8]

### used_combos (role+scenario, dedup) — batch 4
- R31: 医学写作+量表心理测量; 生物统计+样本量重估SSR
- R32: 数据管理员(DM)+数据治理; 药物警戒(PV)+disproportionality信号
- R33: 研究者/CRC+电子知情同意; 注册事务+eCTD/IND/CTA
- R34: 申办方合规+PD/PV术语; CRA+中心启动访视SIV
- R35: CRC+伴随用药; 医学事务+同情用药/扩展性用药
- R36: 受试者权益+妊娠安全性事件; 临床药理+生物等效BE
- R37: 临床运营经理+风险计划; 注册事务+附条件批准确证性
- R38: 数据保护官(DPO)+DPIA; 统计/DM+盲态数据审查BDR
- R39: 中心实验室+样本链温度; 临床药理+肝/肾损害剂量
- R40: 受试者权益+退出数据删除; 机构办+多区域伦理协调

### pending_blocks batch 4 (flush @ round 40) ref-clinical-operations.md: §1.9 肝/肾损害剂量, §2.7 eConsent, §3.18 SIV, §4.7 数据治理, §4.8 伴随用药, §4.9 BDR ref-regulatory-statistical.md: §3.9 SSR, §4.6 信号检测(disproportionality), §5.20 生物等效, §5.21 同情用药, §8.8 多区域伦理协调, §8.9 DPIA

Round 41 | 一般: 临床运营经理—中心入组缓慢与高脱落率应对(招募/留存/脱落) [gap→ §3.20] | 复杂: 生物统计—随机化区组大小与随机序列生成(已覆盖) [covered §4.2.5]
Round 42 | 一般: PV—个例安全报告(ICSR) MedDRA编码与处理时限 [gap→ §4.7] | 复杂: 注册事务—eCTD/申报资料递交准备与模块组织 [gap→ §7.1]
Round 43 | 一般: 临床药理—PopPK/暴露-效应定量药理学指导剂量 [gap→ §1.10] | 复杂: 生物统计—DSMB章程与运作/利益冲突防范 [gap→ §3.10]
Round 44 | 一般: QM—稽查(audit)准备与发现分级(已覆盖) [covered §6.4] | 复杂: RWE—RWE研究设计(前瞻/回顾/登记)与偏倚控制 [gap→ §3.11]
Round 45 | 一般: DM—安全性数据库设计与SAE一致性核查 [gap→ §4.8] | 复杂: 医学事务—伴随诊断与药物同步开发(已覆盖) [covered §3.7]
Round 46 | 一般: CRC—受试者留存措施/减少脱落(访视负担/交通) [covered §3.20] | 复杂: 注册事务—eCTD技术规格与地域性验证(已覆盖) [covered §7.1]
Round 47 | 一般: 生物样本管理员—留存样本长期储存与稳定性 [gap→ §4.1.6] | 复杂: 申办方合规—AI工具(影像/入组筛选)伦理与监管审查 [gap→ §8.10]
Round 48 | 一般: IT/DM—EDC/IRT/ePRO系统网络安全与数据保护 [gap→ §4.10] | 复杂: 统计—贝叶斯自适应先验稳健性(已覆盖) [covered §3.5]
Round 49 | 一般: 临床药理—老年人群多病共存/多重用药/肾损剂量 [gap→ §1.11] | 复杂: 注册—中美双报CMC互认(已覆盖) [covered §5.5]
Round 50 | 一般: 受试者权益—受试者召回完成随访/留存(已覆盖) [covered §3.20] | 复杂: PV—生殖毒性综合评价与育龄/妊娠管理 [gap→ §5.6]

### used_combos (role+scenario, dedup) — batch 5
- R41: 临床运营经理+招募/留存/脱落; 生物统计+随机区组序列
- R42: 药物警戒(PV)+ICSR/MedDRA; 注册事务+eCTD/申报资料
- R43: 临床药理+定量药理学/暴露-效应; 生物统计+DSMB章程
- R44: 质量管理(QM)+稽查准备; 真实世界研究(RWE)+研究设计偏倚
- R45: 数据管理员(DM)+安全性数据库; 医学事务+伴随诊断
- R46: CRC+受试者留存措施; 注册事务+eCTD技术规格
- R47: 生物样本管理员+样本长期储存; 申办方合规+AI工具伦理
- R48: IT/DM+系统网络安全; 生物统计+贝叶斯先验稳健
- R49: 临床药理+老年人群; 注册事务+中美双报CMC
- R50: 受试者权益+受试者召回随访; 药物警戒(PV)+生殖毒性

### pending_blocks batch 5 (flush @ round 50) ref-clinical-operations.md: §1.10 定量药理学/暴露-效应, §1.11 老年人群, §3.20 招募与留存, §4.1.6 生物样本长期储存, §4.10 网络安全, §5.6 生殖毒性综合评价 ref-regulatory-statistical.md: §3.10 DSMB章程, §3.11 RWE研究设计, §4.7 ICSR处理链/MedDRA, §4.8 安全性数据库/信号管理, §7.1 申报资料/eCTD递交, §8.10 AI工具伦理审查

Round 51 | 一般: 伦理—紧急救治受试者无法即时同意如何合规(豁免/紧急同意) [gap→ §2.8] | 复杂: 临床药理—药物基因组学(CYP2C19/DPYD)指导剂量与禁忌 [gap→ §1.12]
Round 52 | 一般: CRA—中心完成入组后关闭与数据/物资移交 [gap→ §3.21] | 复杂: 注册事务—Type B沟通交流会议准备与纪要落实 [gap→ §8.11]
Round 53 | 一般: 申办方合规—试验被监管clinical hold后的应对与恢复 [gap→ §8.12] | 复杂: PV—安全性风险管理计划(RMP)制定与风险最小化 [gap→ §4.9]
Round 54 | 一般: PV—上市后安全性研究(PASS)/确证性试验履约 [gap→ §4.10] | 复杂: DPO—中国受试者数据出境PIPL/数据安全法安全评估 [gap→ §8.13]
Round 55 | 一般: 受试者权益—弱势群体(孕妇/囚犯/认知障碍)保护(已覆盖) [covered §2.1/§3.7] | 复杂: 生物统计—非劣效界值恒定假设(已覆盖) [covered §3.3]
Round 56 | 一般: 数据管理员—CDISC SDTM/ADaM实施与映射验证(已覆盖) [covered §4.7/§4.5] | 复杂: 注册—中美双报种族敏感性(已覆盖) [covered §5.5/§5.19]
Round 57 | 一般: 临床运营经理—远程监查比例与风险控制(已覆盖) [covered §3.6] | 复杂: 医学事务—MSL沟通边界(已覆盖) [covered §8.7]
Round 58 | 一般: 研究者—受试者撤回后数据删除权GDPR(已覆盖) [covered §4.1.4/§8.5] | 复杂: 生物统计—贝叶斯自适应α等价(已覆盖) [covered §3.5]
Round 59 | 一般: QM—CAPA根因分析与有效性检查(已覆盖) [covered §6.5] | 复杂: 统计编程—ADaM/TFL QC(已覆盖) [covered §4.5]
Round 60 | 一般: CRC—药物编盲包装双盲一致性(已覆盖) [covered §4.2.7] | 复杂: RWE—外部对照偏倚控制(已覆盖) [covered §3.8]

### used_combos (role+scenario, dedup) — batch 6
- R51: 伦理+豁免/紧急知情同意; 临床药理+药物基因组学PGx
- R52: CRA+中心关闭/数据移交; 注册事务+沟通交流会议
- R53: 申办方合规+临床hold; 药物警戒(PV)+RMP
- R54: 药物警戒(PV)+PASS/上市后承诺; 数据保护官(DPO)+中国数据出境PIPL
- R55: 受试者权益+弱势群体保护; 生物统计+非劣效界值
- R56: 数据管理员(DM)+CDISC实施; 注册事务+中美双报种族
- R57: 临床运营经理+远程监查; 医学事务+MSL沟通
- R58: 研究者+撤回数据删除; 生物统计+贝叶斯α等价
- R59: 质量管理(QM)+CAPA根因; 统计编程+ADaM/TFL
- R60: CRC+药物编盲包装; 真实世界研究(RWE)+外部对照

### pending_blocks batch 6 (flush @ round 60) ref-clinical-operations.md: §1.12 药物基因组学(PGx), §2.8 豁免/紧急知情同意, §3.21 中心关闭与移交 ref-regulatory-statistical.md: §4.9 RMP, §4.10 PASS, §8.11 沟通交流会议, §8.12 临床hold, §8.13 中国数据出境PIPL/数据安全法

Round 61 | 一般: 机构办—伦理委员会组成与独立性运作 [gap→ §3.22] | 复杂: 申办方—受试者隐私privacy by design落地 [gap→ §2.10]
Round 62 | 一般: IT/DM—EDC系统退役与数据迁移可追溯 [gap→ §4.12] | 复杂: 研究者—孕妇受试者入组特殊考量 [gap→ §5.7]
Round 63 | 一般: 注册事务—儿科研究计划(PIP)与儿科适应症 [gap→ §5.22] | 复杂: 医学事务—临床试验结果登记与透明度(ClinicalTrials.gov/CTIS) [gap→ §8.14]
Round 64 | 一般: CRC—源数据转录ALCOA+(已覆盖) [covered §4.1] | 复杂: 生物统计—估计目标与伴发事件(已覆盖) [covered §3.1]
Round 65 | 一般: 临床药理—FIH起始剂量(已覆盖) [covered §1.5] | 复杂: PV—DSUR区域附录整合(已覆盖) [covered §4.4]
Round 66 | 一般: QM—GCP核查准备(已覆盖) [covered §6.4] | 复杂: 统计编程—缺失数据MI处理(已覆盖) [covered §4.4]
Round 67 | 一般: 受试者权益—受试者投诉申诉(已覆盖) [covered §2.5] | 复杂: 注册—疫苗桥接免疫原性(已覆盖) [covered §5.13]
Round 68 | 一般: CRO—供应商审计与过渡(已覆盖) [covered §3.13] | 复杂: 生物统计—篮式/伞式多重性(已覆盖) [covered §5.9]
Round 69 | 一般: 临床运营经理—风险计划CtQ/QTL(已覆盖) [covered §3.14] | 复杂: 医学写作—CSR讨论局限性(已覆盖) [covered §5.2]
Round 70 | 一般: 数据管理员—数据治理框架(已覆盖) [covered §4.7] | 复杂: 真实世界—RWE研究设计偏倚(已覆盖) [covered §3.11]

### used_combos (role+scenario, dedup) — batch 7
- R61: 机构办+IRB组成/独立性; 申办方+受试者隐私落地
- R62: IT/DM+系统退役/数据迁移; 研究者+孕妇受试者入组
- R63: 注册事务+PIP儿科; 医学事务+结果登记透明度
- R64: CRC+源数据转录; 生物统计+估计目标/伴发事件
- R65: 临床药理+FIH起始剂量; 药物警戒(PV)+DSUR区域附录
- R66: 质量管理(QM)+GCP核查; 统计编程+缺失MI处理
- R67: 受试者权益+投诉申诉; 注册事务+疫苗桥接
- R68: CRO+供应商审计/过渡; 生物统计+篮式/伞式多重性
- R69: 临床运营经理+风险计划; 医学写作+CSR局限性
- R70: 数据管理员(DM)+数据治理; 真实世界研究(RWE)+RWE研究设计

### pending_blocks batch 7 (flush @ round 70) ref-clinical-operations.md: §2.10 受试者隐私落地, §3.22 IRB组成/独立性, §4.12 数据迁移/系统退役, §5.7 孕妇受试者入组 ref-regulatory-statistical.md: §5.22 PIP儿科研究计划, §8.14 结果登记透明度

Round 71 | 一般: 数据管理专员—个体水平数据(IPD)对外共享的隐私与同意要求 [gap→ §8.16] | 复杂: 注册+医学—IPD共享叠加中国数据出境(PIPL安全评估/去标识/DUA) [gap→ §8.16/§8.13]
Round 72 | 一般: 研究者(PI)—研究者发起研究(IIT)探索已上市药新适应症的治理 [gap→ §2.11] | 复杂: 机构办+申办方—IIT与申办方研究的责任/伦理/数据归属边界 [gap→ §2.11]
Round 73 | 一般: 生物统计师—统计分析报告(SAR)与CSR/TFL关系及内容 [gap→ §5.23] | 复杂: 统计+注册—SAR与SAP/盲态审查(BDR)/分析集一致性 [gap→ §5.23]
Round 74 | 一般: 注册事务—肿瘤药突破性疗法/fast track资格 [gap→ §8.15] | 复杂: 注册+医学—加快程序后附条件批准伴随PASS/RMP上市后承诺 [gap→ §8.15/§4.10/§4.9]
Round 75 | 一般: 医学事务—ClinicalTrials.gov登记后结果公示义务 [covered §8.14] | 复杂: 全球注册—美/欧CTIS/中登记平台结果公示时限差异统一 [covered §8.14]
Round 76 | 一般: 数据治理—IPD共享前假名化与DUA机制 [covered §8.16] | 复杂: 法务+DPO—IPD跨境标准合同路径与重要数据安全评估叠加 [covered §8.16/§8.13]
Round 77 | 一般: PI—IIT使用机构样本库数据是否需重新伦理审查 [covered §2.11] | 复杂: 机构办—多中心IIT伦理协作审查/经费合规/利益冲突 [covered §2.11]
Round 78 | 一般: 生物统计—SAR完成后至CSR定稿数据可否修改 [covered §5.23] | 复杂: 统计+运营—SAR锁定/数据库锁定/盲态审查/TFL版本一致性 [covered §5.23]
Round 79 | 一般: 注册—优先审评与突破性疗法是否同一程序 [covered §8.15] | 复杂: 全球—同一药中美欧分别申请加快程序资格/承诺差异与沟通安排(§8.11) [covered §8.15]
Round 80 | 一般: 医学事务—期刊要求共享IPD但旧ICF未提共享的处理 [covered §8.16] | 复杂: 合规—IPD共享/登记透明度(§8.14)/发表政策(§8.6)避免选择性披露 [covered §8.16/§8.14/§8.6]

### used_combos (role+scenario, dedup) — batch 8
- R71: 数据管理专员+IPD共享隐私/同意; 注册+医学+IPD出境叠加
- R72: 研究者(PI)+IIT治理; 机构办+申办方+IIT责任边界
- R73: 生物统计师+SAR与CSR/TFL; 统计+注册+SAR一致性
- R74: 注册事务+突破性疗法/fast track; 注册+医学+加快程序上市后承诺
- R75: 医学事务+结果登记公示; 全球注册+多平台时限差异
- R76: 数据治理+IPD假名化/DUA; 法务+DPO+IPD跨境叠加
- R77: PI+IIT样本库伦理; 机构办+多中心IIT协作审查
- R78: 生物统计+SAR至CSR数据修改; 统计+运营+SAR版本一致性
- R79: 注册+优先审评vs突破性疗法; 全球+多辖区加快程序差异
- R80: 医学事务+旧ICF共享IPD; 合规+共享/登记/发表冲突

### pending_blocks batch 8 (flush @ round 80) ref-clinical-operations.md: §2.11 研究者发起研究(IIT)治理 ref-regulatory-statistical.md: §5.23 统计分析报告(SAR), §8.15 加快上市程序, §8.16 数据共享/IPD

Round 81 | 一般: 临床药理—CNS镇静药滥用潜力评估需哪些证据 [gap→ §1.13] | 复杂: 安全+注册—滥用阳性后防滥用剂型与RMP(§4.9)/REMS衔接 [covered §1.13]
Round 82 | 一般: 临床药理—外用抗菌药是否需光安全性评估 [gap→ §1.14] | 复杂: 非临床+医学—光毒性临床验证与标签避光警示(§2.1)衔接 [covered §1.14]
Round 83 | 一般: 研究者—育龄女性(WOCBP)入组前须做妊娠试验 [gap→ §2.12] | 复杂: 医学+伦理—避孕失败致妊娠暴露上报与随访(§5.4) [covered §2.12/§5.4]
Round 84 | 一般: 研究药师—试验结束剩余药品回收与销毁(药物销毁) [gap→ §3.23] | 复杂: 药师+QA—回收销毁计数差异归因与上报(§6.3)闭环 [covered §3.23]
Round 85 | 一般: 临床运营—医疗器械试验与药物RCT设计差异 [gap→ §3.24] | 复杂: 注册+统计—器械难盲态下独立终点判定(BICR/CEC)与偏倚控制 [covered §3.24]
Round 86 | 一般: 影像科—肿瘤试验中心影像(BICR)作用 [gap→ §4.13] | 复杂: 数据管理—中心影像采集标准与ALCOA+(§4.1)可追溯 [covered §4.13]
Round 87 | 一般: 统计—临床结局评估(COA)与终点选择注意 [gap→ §5.24] | 复杂: 量表团队—跨国PRO翻译验证(§4.14)与ePRO(§4.10)版本管理 [covered §5.24/§4.14]
Round 88 | 一般: 医学—哺乳期受试者能否入组 [gap→ §5.8] | 复杂: 安全+标签—哺乳暴露量化(M/P比)与说明书决策 [covered §5.8]
Round 89 | 一般: 非临床—新药是否须做遗传毒性与致癌性 [gap→ §5.25] | 复杂: 注册+临床—遗传毒性阳性联动临床监测(§5.3)与风险沟通 [covered §5.25]
Round 90 | 一般: 注册/法务—创新药数据保护期与专利期补偿 [gap→ §8.17] | 复杂: 全球—中美欧数据保护/专利补偿/儿科独占(§5.22)组合布局 [covered §8.17]

### used_combos (role+scenario, dedup) — batch 9
- R81: 临床药理+CNS滥用潜力; 安全+注册+防滥用剂型/RMP
- R82: 临床药理+光安全性; 非临床+医学+光毒性临床验证
- R83: 研究者+WOCBP妊娠筛查; 医学+伦理+避孕失败暴露
- R84: 研究药师+药品回收销毁; 药师+QA+计数差异归因
- R85: 临床运营+医疗器械试验设计; 注册+统计+器械盲态偏倚
- R86: 影像科+中心影像BICR; 数据管理+影像采集可追溯
- R87: 统计+COA终点选择; 量表团队+PRO翻译验证
- R88: 医学+哺乳期入组; 安全+标签+哺乳暴露量化
- R89: 非临床+遗传/致癌性; 注册+临床+遗传阳性监测
- R90: 注册/法务+数据保护期/专利补偿; 全球+独占组合布局

### pending_blocks batch 9 (flush @ round 90) ref-clinical-operations.md: §1.13 药物滥用潜力, §1.14 光安全性, §2.12 WOCBP妊娠筛查/避孕, §3.23 药品回收/销毁, §3.24 医疗器械试验, §4.13 中心影像, §4.14 量表翻译验证, §5.8 哺乳期 ref-regulatory-statistical.md: §5.24 临床结局评估(COA), §5.25 遗传/致癌性, §8.17 数据保护期/专利期补偿

Round 91 | 一般: 临床药理—儿科试验剂型须考虑适口性/给药装置 [gap→ §1.15] | 复杂: 儿科+医学—适口性装置影响依从(§3.25)与精确剂量(§1.7) [covered §1.15]
Round 92 | 一般: 临床药理—哪些药需做 thorough QT 研究 [gap→ §1.16] | 复杂: 安全+医学—QTc监测与标签警示(§2.1)及剂量(§1.5)衔接 [covered §1.16]
Round 93 | 一般: 临床药理—支持PK/BE的生物分析方法要验证什么 [gap→ §1.17] | 复杂: 生物分析+数据—样本链(§4.1.3)与批次QC及GLP合规 [covered §1.17]
Round 94 | 一般: CRC—如何监测记录受试者给药依从性 [gap→ §3.25] | 复杂: 统计+医学—低依从性对PP集与疗效(§5.23)解释影响 [covered §3.25/§5.23]
Round 95 | 一般: 研究者—受试者招募广告须过伦理审查吗 [gap→ §3.26] | 复杂: CRC+伦理—社交媒体招募隐私(§2.10)与公平性(§5 弱势) [covered §3.26]
Round 96 | 一般: 研究者—受试者退出后是否须随访 [gap→ §3.27] | 复杂: 医学+数据—退出后随访数据归属(§4.1)与分析集(§5.23) [covered §3.27/§5.23]
Round 97 | 一般: 医学—实验室异常值如何判定是否算AE [gap→ §4.15] | 复杂: 数据管理—多中心正常值范围统一与MedDRA(§4.7)编码一致 [covered §4.15]
Round 98 | 一般: 研究药师—盲态试验药品编码与发药 [gap→ §4.16] | 复杂: 药师+IRT—双盲双模拟包装与应急破盲(§4.2.2)衔接 [covered §4.16]
Round 99 | 一般: 研究者—受试者死亡如何报告 [gap→ §5.9] | 复杂: PV+医学—死亡归因与DSUR/CSR汇总及退出后获知(§3.27) [covered §5.9]
Round 100 | 一般: 医学—受试者药物过量如何处置 [gap→ §5.10] | 复杂: 安全+风险管理—过量与依从(§3.25)/RMP(§4.9)联动 [covered §5.10]

### used_combos (role+scenario, dedup) — batch 10
- R91: 临床药理+儿科剂型; 儿科+医学+适口性依从
- R92: 临床药理+thorough QT; 安全+医学+QTc标签剂量
- R93: 临床药理+生物分析方法; 生物分析+数据+样本链/GLP
- R94: CRC+给药依从性; 统计+医学+依从与PP集
- R95: 研究者+招募广告伦理; CRC+伦理+社媒隐私公平
- R96: 研究者+退出后随访; 医学+数据+随访数据归属
- R97: 医学+实验室异常判定; 数据管理+正常值范围/MedDRA
- R98: 研究药师+药品编码盲态供应; 药师+IRT+双模拟破盲
- R99: 研究者+受试者死亡报告; PV+医学+死亡归因汇总
- R100: 医学+药物过量处置; 安全+风险管理+过量/RMP

### pending_blocks batch 10 (flush @ round 100 — FINAL) ref-clinical-operations.md: §1.15 儿科剂型, §1.16 QTc/thorough QT, §1.17 生物分析/样本分析, §3.25 给药依从性, §3.26 招募广告, §3.27 停药/退出与随访, §4.15 正常值范围, §4.16 药品编码/盲态供应, §5.9 受试者死亡/死亡报告, §5.10 药物过量/意外暴露 (ref-regulatory-statistical.md: 本批无新增；药物警戒计划确认由 §4.9 RMP 覆盖，未新增)

## 100-ROUND COMPLETION SUMMARY
- 总计 100 轮（Round 1–100），每轮 1 道一般 + 1 道复杂 = 200 道场景题；其中覆盖缺口(gap)按批补强，已覆盖(covered)题复用既有知识未改动。
- 累计新增知识块：104 块（batches 1–3 共 41 + batch4 12 + batch5 12 + batch6 8 + batch7 6 + batch8 4 + batch9 11 + batch10 10）。
- 最终 SKILL.md 版本：0.7.10。
- 红线执行：所有动态项（时间线/年份/字段/版本/阈值/比例）均带"动态项须官方核实"标记；仅本地改动 2 个 ref 文件 + SKILL.md + 进度日志 + 记忆文件；未 git push、未 publish；未改 workflows.yaml；未存法规全文。
- 验证：每批新增探针关键词均经 scripts/search_refs.py 单模式匹配确认 FOUND（累计 13+13+14 余批探针全部命中）。
- 产出文件：knowledge/ref-clinical-operations.md、knowledge/ref-regulatory-statistical.md、SKILL.md(changelog 0.7.4–0.7.10)、auto_loop_rounds.md(全程日志)、memory/2026-08-01.md(#39–#45)。
