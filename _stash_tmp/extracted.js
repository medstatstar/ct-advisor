
/* ===================== i18n ===================== */
const I18N = {
  zh:{
    appTitle:"ct-advisor 工作台", appSub:"临床试验总顾问 · Coze 云端计算",
    liteNotice:"本页面是「ct-advisor」技能的简化版，仅实现基础功能；如需使用完整功能，请安装相应的技能。",
    navConsole:"顾问对话", navSkills:"技能控制台", navHistory:"历史记录",
    mConsole:"对话", mSkills:"技能", mHistory:"历史",
    pendingTitle:"需本地技能跟进（Coze 返回 need_tool）", pendingEmpty:"暂无待跟进项",
    consoleTitle:"顾问对话台", sendLabel:"发送",
    contLabel:"连续对话（携带前文）",
    vagueTitle:"问题表述可能不明确（疑似 vague）",
    vagueDesc:"这句话缺少明确对象（过短 / 指代不明 / 依赖前文），而网页版工作台不带澄清追问，直接发送可能答非所问。建议补充具体对象与背景后再发；如需引导式澄清，请在 WorkBuddy 中使用 ct-advisor 技能（本地 route.py 会先澄清 vague 再转发）。",
    vagueProceed:"仍要发送", vagueRefine:"先补充细节",
    qPlaceholder:"描述你的临床试验问题，例如：PD-1 单抗三线 NSCLC 的 ORR 如何估算样本量？",
    attachChipLabel:"上传文件",
    attachPlaceholder:"可选：粘贴背景资料 / 方案片段 / 数据摘要，将随问题一并发送给 Coze（对应原技能的附件追加）",
    attachFileHint:"或上传文件（txt/md/csv/docx/pdf/pptx，随问题发送云端解析；单文件上限 50 MB，超 5 MB 自动转 Markdown 再传）",
    extracting:"正在抽取文件文本…", extractOk:"已抽取并填入附件：", extractFail:"文件抽取失败：",
    attachUploading:"正在上传文件到云端…", attachUploaded:"已上传，将随问题发送：", attachUploadFail:"文件上传失败：",
    docTag:"引用文档", cancelRunLabel:"停止", cancelSent:"已发送取消请求", cancelOk:"本次回答已取消",
    bugBtn:"反馈", bugTitle:"报告问题 / Bug 反馈", bugTip:"请描述遇到的问题（含复现步骤更佳）。报告经脱敏：仅含页面/技能元数据与你确认的描述，不含任何检测数据。",
    bugCtxLabel:"【发送上下文（元数据，只读）】", bugDescLabel:"问题描述", bugDescPh:"例如：单击主按钮后页面无任何反应…",
    bugFill:"请先填写问题描述。", bugConfirmTip:"请在下方预览中确认脱敏报告无误后，点击「确认发送」；需要改动点「返回修改」。",
    bugPreviewTitle:"将发送的脱敏报告（仅元数据 + 你确认的描述）：",
    bugLocal:"已记录本地反馈（{id}）。感谢提交！", bugFail:"提交失败：",
    bugSubmit:"提交反馈", bugSubmitConfirm:"确认发送", bugSubmitting:"提交中…", bugBack:"返回修改", bugCancel:"取消",
    runLocal:"在本机运行（本地技能）", runLocalResult:"本地执行结果", running:"正在本机运行…",
    skillsTitle:"技能控制台", skillsIntro:"点击下方能力卡片，填写结构化参数后直接调用 ct-advisor 云端精校。各入口字段对齐本地技能 CLI，Coze 判定 need_tool 后由本地技能执行并缝合。",
    histTitle:"历史记录",
    exportBtn:"导出 JSON 备份", importBtn:"导入恢复", clearBtn:"清空历史",
    connOk:"后端就绪", connOff:"未配置", connErr:"Coze 错误", connProxy:"本地服务未启动（双击 run_app.bat）",
    bannerOk:"连接正常：本地服务已就绪，可直接发送问题。",
    bannerWarn:"本地服务未启动，发送将无法到达云端。请双击：",
    bannerChecking:"正在连接本地服务…",
    bannerExternal:"请用系统浏览器（Edge / Chrome）打开本页；若直接双击 html 文件或用预览面板打开，会因无法访问同源服务而失败——本地请运行 run_app.bat，已发布到云端则直接由同源 /run 提供服务。",
    bannerTimeout:"连接检查超时。若你在 WorkBuddy 预览面板内查看，它会拦截本页对同源服务的请求——请改用系统浏览器（Edge / Chrome）打开本页地址。",
    sending:"正在发送问题到 Coze 云端分析…", sent:"已发送", langLabel:"EN",
    cozeRoute:"您的问题将发送至 Coze 云端（ct-advisor.coze.site）进行分析，不会上传个人 / 受试者 / 未公开项目数据。",
    setEndpointL:"Coze 端点 URL", setEndpointH:"Default calls same-origin /run (run run_app.bat locally; if published to cloud it uses same-origin automatically, no local proxy needed)",
    setTokenL:"Bearer Token（公开凭据）", setTokenH:"默认已内嵌技能公开凭据，无需填写；如需自定义可在此覆盖",
    setContL:"连续对话默认开启", setContOn:"开启", setContOff:"关闭",
    setTitle:"连接设置", saveBtn:"保存", resetBtn:"恢复默认",
    setNote:"设置保存在本机浏览器（localStorage），不上云。",
    charHint:"字符", sendHint:"· Enter 发送 / Shift+Enter 换行", sideFoldTip:"单击导航栏空白处折叠 / 展开", you:"你", bot:"ct-advisor", needTool:"需本地技能", reask:"重问", copyCard:"复制卡片",
    pendingSkill:"技能", runId:"运行ID", cached:"缓存命中",
    histQ:"问题", histEmpty:"暂无历史，先去对话台提问吧。",
    histReask:"重问", histMore:"点击查看全文", histFold:"收起",
    clearConfirm:"确定清空全部历史记录？此操作不可撤销。",
    copied:"已复制", saved:"已保存",
    errNet:"发送失败：请确认本页由同源服务托管。本地使用请双击 run_app.bat 启动服务；已发布到云端则直接走同源 /run，无需本机代理。",
    errHttp:"Coze 返回错误：",
    errEmpty:"已收到响应，但未包含答案字段（final_answer/content/answer 均缺失）。若响应含 msg 将一并显示。",
    formSend:"发送分析", formCancel:"取消",
    reqField:"必填项未填写：",
    ntTitle:"need_tool 跟进详情", ntRunLocal:"在本机运行（WorkBuddy CLI）", ntCopy:"复制命令",
    ntPrepHint:"准备提示：", ntEngineLocal:"本地引擎（本机执行技能）", ntEngineCoze:"云端引擎（Coze 远程 R 服务）",
    ntReferral:"转诊（referral-only，不经 need_tool 自动调用）",
    ntReferralNote:"该能力需数据抽取 + 重型 R 管线，请显式调用对应技能并附数据集 / 效应量矩阵。",
    ntSampleNote:"样本量计算实际由云端 R 服务完成；以下命令用于在本机 WorkBuddy 中复现，或访问 ct-samplesize.coze.site/run。",
    clarifyAsk:"在回答之前，请帮我确认以下几点：", clarifyHint:"回复你的答案，我会继续追问（最多 3 轮）或开始分析。",
    tasks:[
      {ti:"方案 / 方法学 / 合规审查", de:"设计、合规、审查类问题（方法学 A–J 工作流）", route:"→ ct-advisor 内部工作流", ic:"doc"},
      {ti:"样本量 / 效能", de:"样本量与统计效能计算（转 ct-samplesize）", route:"→ ct-samplesize（coze 引擎）", ic:"calc"},
      {ti:"注册试验检索", de:"ClinicalTrials.gov / CDE 检索（转 ct-registry）", route:"→ ct-registry", ic:"search"},
      {ti:"安全性信号检测", de:"FAERS 不相称性信号（转 ct-safety）", route:"→ ct-safety", ic:"signal"},
      {ti:"文献检索与综述", de:"已发表文献检索（转 ct-literature）", route:"→ ct-literature", ic:"book"},
      {ti:"Meta 分析", de:"Meta 分析与森林图（referral-only）", route:"→ @skill:meta-analysis", ic:"meta"},
      {ti:"法规 / 监管要求", de:"FDA / CDE / NMPA 监管差异", route:"→ ct-advisor 内部知识", ic:"law"}
    ]
  },
  en:{
    appTitle:"ct-advisor Workspace", appSub:"Clinical-Trial Advisor · Cloud Coze Computing",
    liteNotice:"This page is a simplified version of the \"ct-advisor\" skill covering only the basics; for the complete feature set, please install the corresponding skill.",
    navConsole:"Consult", navSkills:"Skill Console", navHistory:"History",
    mConsole:"Chat", mSkills:"Skills", mHistory:"History",
    pendingTitle:"Local-skill follow-ups (Coze need_tool)", pendingEmpty:"No follow-ups",
    consoleTitle:"Consultation Console", sendLabel:"Send",
    contLabel:"Continuous (carry context)",
    vagueTitle:"Question may be vague",
    vagueDesc:"This question lacks a clear subject (too short / unclear reference / relies on prior context), and the web workbench has no clarification loop — sending as-is may miss the point. Add concrete detail first; for guided clarification, use the ct-advisor skill in WorkBuddy (local route.py clarifies vague questions before forwarding).",
    vagueProceed:"Send anyway", vagueRefine:"Refine first",
    qPlaceholder:"Describe your clinical-trial question, e.g. How to size a sample for PD-1 3L NSCLC ORR?",
    attachChipLabel:"Upload file",
    attachPlaceholder:"Optional: paste background / protocol snippet / data summary — sent with the question (maps to attachment append).",
    attachFileHint:"Or upload a file (txt/md/csv/docx/pdf/pptx) — uploaded to the cloud and sent with your question (large docs are chunk-retrieved).",
    extracting:"Extracting file text…", extractOk:"Extracted & appended: ", extractFail:"File extraction failed: ",
    attachUploading:"Uploading file to cloud…", attachUploaded:"Uploaded, will be sent with the question: ", attachUploadFail:"File upload failed: ",
    docTag:"Doc cited", cancelRunLabel:"Stop", cancelSent:"Cancel requested", cancelOk:"This answer was cancelled",
    bugBtn:"Feedback", bugTitle:"Report an issue / Bug feedback", bugTip:"Describe the issue (reproduction steps help). The report is sanitized: metadata + the description you confirm — no consultation content or attachment data.",
    bugCtxLabel:"[Context to send (metadata, read-only)]", bugDescLabel:"Description", bugDescPh:"e.g. clicking the main button did nothing…",
    bugFill:"Please describe the issue first.", bugConfirmTip:"Review the sanitized report below, then Confirm & send; use Back to edit if needed.",
    bugPreviewTitle:"Sanitized report to send (metadata + your confirmed description):",
    bugLocal:"Local feedback recorded ({id}). Thank you!", bugFail:"Submit failed: ",
    bugSubmit:"Submit", bugSubmitConfirm:"Confirm & send", bugSubmitting:"Submitting…", bugBack:"Back to edit", bugCancel:"Cancel",
    runLocal:"Run locally (local skill)", runLocalResult:"Local execution result", running:"Running on this machine…",
    skillsTitle:"Skill Console", skillsIntro:"Pick a capability card, fill the structured form, and call ct-advisor cloud refinement directly. Fields align with the local skill CLIs; Coze judges need_tool, then the local skill executes and stitches.",
    histTitle:"History",
    exportBtn:"Export JSON", importBtn:"Import", clearBtn:"Clear",
    connOk:"Backend ready", connOff:"Not set", connErr:"Coze error", connProxy:"Local server not started (run run_app.bat)",
    bannerOk:"Connection OK: local server ready — send your question.",
    bannerWarn:"Local server not started — sends won't reach the cloud. Run:",
    bannerChecking:"Connecting to local server…",
    bannerExternal:"Open this page in your system browser (Edge / Chrome). Opening the .html file directly or via the preview panel fails because it cannot reach the same-origin server — run run_app.bat locally, or use the cloud-published URL which serves same-origin /run.",
    bannerTimeout:"Connection check timed out. If you are viewing this inside the WorkBuddy preview panel, it blocks page requests to the same-origin server — open the page URL in your system browser (Edge / Chrome) instead.",
    sending:"Sending to Coze cloud for analysis…", sent:"Sent", langLabel:"中",
    cozeRoute:"Your question is sent to the Coze cloud (ct-advisor.coze.site) for analysis. No personal, subject, or unpublished project data is uploaded.",
    setEndpointL:"Coze Endpoint URL", setEndpointH:"Same-origin /run is used by default (run run_app.bat locally; if published to cloud it uses same-origin automatically, no local proxy needed)",
    setTokenL:"Bearer Token (public)", setTokenH:"The embedded shared token is used by default; no need to fill. Override here if needed.",
    setContL:"Continuous by default",
    setContOn:"On", setContOff:"Off",
    setTitle:"Connection Settings", saveBtn:"Save", resetBtn:"Reset",
    setNote:"Settings stored in this browser (localStorage), not in the cloud.",
    charHint:"chars", sendHint:"· Enter to send / Shift+Enter newline", sideFoldTip:"Click blank area of the nav to collapse / expand", you:"You", bot:"ct-advisor", needTool:"Needs local skill", reask:"Re-ask", copyCard:"Copy card",
    pendingSkill:"Skill", runId:"Run ID", cached:"Cached",
    histQ:"Q", histEmpty:"No history yet — ask something in the console.",
    histReask:"Re-ask", histMore:"Click to view full answer", histFold:"Collapse",
    clearConfirm:"Clear all history? This cannot be undone.",
    copied:"Copied", saved:"Saved",
    errNet:"Send failed: make sure this page is served by its host. Locally, run run_app.bat first; if published to cloud it calls same-origin /run directly — no local proxy needed.",
    errHttp:"Coze error: ",
    errEmpty:"Response received but no answer field (final_answer/content/answer missing). Any msg in the response is shown above.",
    formSend:"Run analysis", formCancel:"Cancel",
    reqField:"Required field missing: ",
    ntTitle:"need_tool follow-up detail", ntRunLocal:"Run locally (WorkBuddy CLI)", ntCopy:"Copy command",
    ntPrepHint:"Prep hint: ", ntEngineLocal:"Local engine (skill runs on this machine)", ntEngineCoze:"Cloud engine (Coze remote R service)",
    ntReferral:"Referral (referral-only, not auto-invoked via need_tool)",
    ntReferralNote:"This capability needs data extraction + heavy R pipeline — explicitly call the skill and attach the dataset / effect-size matrix.",
    ntSampleNote:"Sample-size is actually computed by the cloud R service; the command below reproduces it in local WorkBuddy, or visit ct-samplesize.coze.site/run.",
    clarifyAsk:"Before answering, could you help confirm a few things?", clarifyHint:"Reply with your answer — I'll ask up to 3 more rounds, or start the analysis.",
    tasks:[
      {ti:"Protocol / Methodology / Compliance", de:"Design, compliance, review questions (workflows A–J)", route:"→ ct-advisor internal workflows", ic:"doc"},
      {ti:"Sample Size / Power", de:"n / power (→ ct-samplesize)", route:"→ ct-samplesize (coze engine)", ic:"calc"},
      {ti:"Registry Search", de:"ClinicalTrials.gov / CDE (→ ct-registry)", route:"→ ct-registry", ic:"search"},
      {ti:"Safety Signal", de:"FAERS disproportionality (→ ct-safety)", route:"→ ct-safety", ic:"signal"},
      {ti:"Literature", de:"Published literature (→ ct-literature)", route:"→ ct-literature", ic:"book"},
      {ti:"Meta Analysis", de:"Meta-analysis & forest plots (referral-only)", route:"→ @skill:meta-analysis", ic:"meta"},
      {ti:"Regulatory", de:"FDA / CDE / NMPA differences", route:"→ ct-advisor internal knowledge", ic:"law"}
    ]
  }
};
const ICONS = {
  close:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 6l12 12M18 6 6 18"/></svg>',
  reask:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 12a9 9 0 1 0 3-6.7L3 8"/><path d="M3 4v4h4"/><path d="M12 8v4l3 2"/></svg>',
  doc:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8Z"/><path d="M14 3v5h5M9 13h6M9 17h6"/></svg>',
  calc:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="5" y="3" width="14" height="18" rx="2"/><path d="M8 7h8M8 11h2M12 11h2M16 11h0M8 15h2M12 15h2M16 15v4M8 19h4"/></svg>',
  search:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4-4"/></svg>',
  signal:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 12h4l3-8 4 16 3-8h4"/></svg>',
  book:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 5a2 2 0 0 1 2-2h13v16H6a2 2 0 0 0-2 2Z"/><path d="M19 19H6a2 2 0 0 0-2 2"/></svg>',
  meta:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 18 9 6l3 6 3-9 6 15"/><path d="M3 21h18"/></svg>',
  law:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 3v18M5 7l7-3 7 3M5 7l-2 7h4zM19 7l-2 7h4zM8 21h8"/></svg>'
};

/* ===================== skill form definitions (fields align to tool_mapping.json) ===================== */
const SKILLS = {
  design:{ category:"design", accuracy:"good",
    fields:[
      {key:"q", type:"textarea", required:true, rows:4, label:{zh:"问题或方案片段", en:"Question / protocol snippet"}, ph:{zh:"例如：请审查以下 III 期随机对照试验的盲法设计与统计边界…", en:"e.g. review the blinding design and statistical boundary of this phase III RCT…"}},
      {key:"attach", type:"textarea", rows:3, label:{zh:"附件（可选）", en:"Attachment (optional)"}, ph:{zh:"粘贴方案 / SAP 片段，将随问题一并发给 Coze", en:"paste protocol/SAP snippet, sent with the question"}}
    ],
    build:(v,T)=> (v.q||"") + (v.attach? ("\n\n[附件]\n"+v.attach):"")
  },
  samplesize:{ category:"statistics", accuracy:"good",
    fields:[
      {key:"test", type:"select", label:{zh:"检验类型", en:"Test type"}, options:[{v:"",t:{zh:"自动判断",en:"Auto"}},{v:"proportion_two",t:{zh:"两比例（率/ORR）",en:"Two proportions"}},{v:"proportion_one",t:{zh:"单组率",en:"One proportion"}},{v:"ttest_ind",t:{zh:"两样本均值 t 检验",en:"Two-sample t-test"}},{v:"ttest_paired",t:{zh:"配对 t 检验",en:"Paired t-test"}},{v:"survival",t:{zh:"生存分析（HR）",en:"Survival (HR)"}},{v:"non_inferiority",t:{zh:"非劣效",en:"Non-inferiority"}},{v:"equivalence",t:{zh:"等效",en:"Equivalence"}}]},
      {key:"p1", type:"num", label:{zh:"p1（对照组率）", en:"p1 (control rate)"}},
      {key:"p2", type:"num", label:{zh:"p2（试验组率）", en:"p2 (treat rate)"}},
      {key:"effect", type:"num", label:{zh:"效应量（均值差）", en:"Effect (mean diff)"}},
      {key:"sd", type:"num", label:{zh:"标准差 SD", en:"SD"}},
      {key:"margin", type:"num", label:{zh:"非劣/等效界值", en:"Margin (NI/Equiv)"}},
      {key:"alpha", type:"num", label:{zh:"α（默认 0.05）", en:"α (default .05)"}, def:0.05},
      {key:"power", type:"num", label:{zh:"效能 power（默认 0.8）", en:"power (default .8)"}, def:0.8},
      {key:"side", type:"select", label:{zh:"单/双侧", en:"One/Two-sided"}, options:[{v:"two",t:{zh:"双侧",en:"Two-sided"}},{v:"one",t:{zh:"单侧",en:"One-sided"}}]},
      {key:"k_groups", type:"num", label:{zh:"组数 k", en:"# groups k"}, def:2}
    ],
    build:(v,T)=>{ const parts=[T.zh?"请估算样本量 / 效能：":""];
      if(v.test) parts.push("检验="+v.test);
      if(v.p1!=="") parts.push("p1="+v.p1); if(v.p2!=="") parts.push("p2="+v.p2);
      if(v.effect!=="") parts.push("effect="+v.effect); if(v.sd!=="") parts.push("sd="+v.sd);
      if(v.margin!=="") parts.push("margin="+v.margin);
      if(v.alpha!==""&&v.alpha!==null) parts.push("alpha="+v.alpha);
      if(v.power!==""&&v.power!==null) parts.push("power="+v.power);
      if(v.side) parts.push("side="+v.side);
      if(v.k_groups&&v.k_groups!=2) parts.push("k="+v.k_groups);
      return parts.join("，")+"。";
    }
  },
  registry:{ category:"data-intel", accuracy:"",
    fields:[
      {key:"cond", type:"text", required:true, label:{zh:"适应症 / 疾病", en:"Condition / disease"}, ph:{zh:"如 NSCLC、2 型糖尿病", en:"e.g. NSCLC, type 2 diabetes"}},
      {key:"intr", type:"text", label:{zh:"干预 / 药物", en:"Intervention / drug"}, ph:{zh:"如 Pembrolizumab", en:"e.g. Pembrolizumab"}},
      {key:"sponsor", type:"text", label:{zh:"申办方", en:"Sponsor"}, ph:{zh:"可选", en:"optional"}},
      {key:"status", type:"text", label:{zh:"状态", en:"Status"}, ph:{zh:"如 recruiting / completed", en:"e.g. recruiting / completed"}},
      {key:"max", type:"num", label:{zh:"最多条数（默认 20）", en:"Max (default 20)"}, def:20},
      {key:"with_cde", type:"bool", label:{zh:"含 CDE（中国）", en:"Include CDE (China)"}},
      {key:"cde_keyword", type:"text", label:{zh:"CDE 关键词", en:"CDE keyword"}, ph:{zh:"可选，配合 CDE", en:"optional, with CDE"}}
    ],
    build:(v,T)=>{ const p=[T.zh?"检索临床试验：":""];
      if(v.cond) p.push("适应症="+v.cond); if(v.intr) p.push("干预="+v.intr);
      if(v.sponsor) p.push("申办方="+v.sponsor); if(v.status) p.push("状态="+v.status);
      if(v.max) p.push("最多"+v.max+"条"); if(v.with_cde) p.push("含CDE");
      if(v.cde_keyword) p.push("CDE关键词="+v.cde_keyword);
      return p.join("，")+"。";
    }
  },
  safety:{ category:"data-intel", accuracy:"",
    fields:[
      {key:"drug", type:"text", required:true, label:{zh:"药物（通用名，英文）", en:"Drug (generic, EN)"}, ph:{zh:"如 semaglutide", en:"e.g. semaglutide"}},
      {key:"event", type:"text", label:{zh:"不良事件（MedDRA PT，可选）", en:"Event (MedDRA PT, opt)"}, ph:{zh:"留空则列 top 信号事件", en:"blank = top signal events"}},
      {key:"top", type:"num", label:{zh:"Top N（默认 10）", en:"Top N (default 10)"}, def:10},
      {key:"date_from", type:"text", label:{zh:"起始日期", en:"Date from"}, ph:{zh:"YYYY-MM-DD", en:"YYYY-MM-DD"}},
      {key:"date_to", type:"text", label:{zh:"截止日期", en:"Date to"}, ph:{zh:"YYYY-MM-DD", en:"YYYY-MM-DD"}}
    ],
    build:(v,T)=>{ const p=[T.zh?"FAERS 安全性信号检测：":""];
      if(v.drug) p.push("药物="+v.drug); if(v.event) p.push("事件="+v.event);
      if(v.top) p.push("top="+v.top); if(v.date_from) p.push("起="+v.date_from); if(v.date_to) p.push("止="+v.date_to);
      return p.join("，")+"。";
    }
  },
  literature:{ category:"data-intel", accuracy:"",
    fields:[
      {key:"topic", type:"text", required:true, label:{zh:"主题", en:"Topic"}, ph:{zh:"如 PD-1 晚期 NSCLC 疗效", en:"e.g. PD-1 advanced NSCLC efficacy"}},
      {key:"year_from", type:"num", label:{zh:"起始年份", en:"Year from"}},
      {key:"year_to", type:"num", label:{zh:"截止年份", en:"Year to"}},
      {key:"safety", type:"bool", label:{zh:"限定安全性文献", en:"Safety-only literature"}},
      {key:"max", type:"num", label:{zh:"最多条数（默认 20）", en:"Max (default 20)"}, def:20},
      {key:"with_europepmc", type:"bool", label:{zh:"含 Europe PMC", en:"Include Europe PMC"}, def:true}
    ],
    build:(v,T)=>{ const p=[T.zh?"检索已发表文献：":""];
      if(v.topic) p.push("主题="+v.topic); if(v.year_from) p.push("年≥"+v.year_from);
      if(v.year_to) p.push("年≤"+v.year_to); if(v.safety) p.push("安全性文献");
      if(v.max) p.push("最多"+v.max+"篇"); if(v.with_europepmc) p.push("含Europe PMC");
      return p.join("，")+"。";
    }
  },
  meta:{ referral:true, fields:[], build:()=>"" },
  regulatory:{ category:"regulatory", accuracy:"",
    fields:[
      {key:"q", type:"textarea", required:true, rows:4, label:{zh:"监管 / 法规问题", en:"Regulatory question"}, ph:{zh:"例如：FDA 与 CDE 在 MRCT 主方案上的监管要求差异？", en:"e.g. FDA vs CDE differences on MRCT master protocols?"}},
      {key:"attach", type:"textarea", rows:3, label:{zh:"附件（可选）", en:"Attachment (optional)"}, ph:{zh:"粘贴法规文本 / 沟通纪要", en:"paste regulatory text / meeting notes"}}
    ],
    build:(v,T)=> (v.q||"") + (v.attach? ("\n\n[附件]\n"+v.attach):"")
  }
};

/* ===================== engine + CLI mapping ===================== */
const SKILL_META = {
  "ct-registry":{engine:"local", script:"ct-registry/scripts/ct_registry.py", extra:["--auto-confirm","--run","--print-summary","--kw-adopt"], prep:{zh:"需确认检索主词（适应症 / 靶点 / 药物名，中英文均可）、可选期别与申办方范围", en:"Confirm search terms (condition/target/drug, EN+ZH), optional phase & sponsor"}},
  "ct-safety":{engine:"local", script:"ct-safety/scripts/ct_safety.py", extra:["--run"], prep:{zh:"需确认药物通用名（openFDA 用英文通用名，如 semaglutide）、目标 AE 术语（MedDRA PT，可选）、起止时间（可选）", en:"Confirm generic drug name (openFDA EN, e.g. semaglutide), target AE (MedDRA PT, opt), date range (opt)"}},
  "ct-literature":{engine:"local", script:"ct-literature/scripts/ct_literature.py", extra:["--run"], prep:{zh:"需确认检索主题（药物 / 靶点 + 适应症）、年份范围、是否限定安全性文献", en:"Confirm topic (drug/target + indication), year range, safety-only?"}},
  "ct-samplesize":{engine:"coze", script:"ct-samplesize/scripts/samplesize_power.py", extra:[], prep:{zh:"需确认检验类型与效应量假设（p1+p2 / effect+sd / HR）、α、power、单双侧", en:"Confirm test type & effect assumption (p1+p2 / effect+sd / HR), α, power, side"}},
  "meta-analysis":{referral:true, prep:{zh:"需数据抽取 + 重型 R 管线；请显式调用并附数据集 / 效应量矩阵", en:"Needs data extraction + heavy R pipeline; call explicitly with dataset / effect-size matrix"}}
};
function cliCmd(tool, params){
  const m = SKILL_META[tool]; if(!m || m.engine!=="local") return "";
  const map = {
    "ct-registry":{cond:"--cond",intr:"--intr",sponsor:"--sponsor",status:"--status",max:"--max",drug:"--drug",with_cde:"--with-cde",cde_keyword:"--cde-keyword"},
    "ct-safety":{drug:"--drug",event:"--event",top:"--top",date_from:"--date-from",date_to:"--date-to"},
    "ct-literature":{topic:"--topic",year_from:"--year-from",year_to:"--year-to",safety:"--safety",max:"--max",with_europepmc:"--with-europepmc"}
  }[tool] || {};
  const parts=["python","~/.workbuddy/skills/"+m.script];
  Object.keys(map).forEach(k=>{ let val=(params||{})[k];
    if(val===undefined||val===null||val==="") return;
    if(typeof val==="boolean"){ if(val) parts.push(map[k]); return; }
    parts.push(map[k]+' "'+String(val).replace(/"/g,'\\"')+'"');
  });
  (m.extra||[]).forEach(e=>parts.push(e));
  return parts.join(" ");
}

/* ===================== state & storage ===================== */
const LS = { hist:"wb_ctadvisor_hist_", cfg:"wb_ctadvisor_cfg_", lang:"wb_ctadvisor_lang_", qid:"wb_ctadvisor_qid_", seen:"wb_ctadvisor_seen_", side:"wb_ctadvisor_side_" };
let state = { lang:"zh", hist:[], cfg:null };
let lastConnOk = false;
let REMOTE_DEFAULT = { endpoint:"", token:"" }; // 默认相对端点：托管页（本地或云端）自动用同源 /run
// 前端 Bearer Token = 用户私有 LLM key（前端直连大模型时使用），不随技能发布，由设置框手动填入（存于浏览器 localStorage）。
// 项目 Coze 连接凭据（ct_advisor_coze / ct_bugreport_coze）统一内嵌 adapters/coze_token_embedded.py，不经此通道下发到前端。

function loadCfg(){
  try{ state.cfg = JSON.parse(localStorage.getItem(LS.cfg)) || null; }catch(e){ state.cfg=null; }
  if(!state.cfg) state.cfg = { endpoint:REMOTE_DEFAULT.endpoint, token:REMOTE_DEFAULT.token, locale:"zh", continuous:"on" };
  if(!state.cfg.endpoint || state.cfg.endpoint.indexOf("ct-advisor.coze.site")>=0 || state.cfg.endpoint.indexOf("8787")>=0 || state.cfg.endpoint.indexOf("127.0.0.1")>=0 || state.cfg.endpoint.indexOf("localhost")>=0) state.cfg.endpoint=REMOTE_DEFAULT.endpoint;
  if(!state.cfg.token) state.cfg.token = REMOTE_DEFAULT.token;
  return state.cfg;
}
function saveCfg(){ localStorage.setItem(LS.cfg, JSON.stringify(state.cfg)); }
function _deviceSig(){
  return [ navigator.userAgent||"", screen.width+"x"+screen.height, navigator.hardwareConcurrency||"", Intl.DateTimeFormat().resolvedOptions().timeZone||"", (navigator.language||"") ].join("|");
}
function getQid(){
  // ct-base §8.6 调用来源标识：sha256:<64hex>（71 字符），同机（同浏览器）恒定，不可逆无 PII。
  // 旧版存的 env:<16hex> 指纹 / env:...:nonce 不合规 → 检测到非 sha256: 前缀即重算覆盖。
  const existing = localStorage.getItem(LS.qid);
  if(existing && existing.indexOf("sha256:")===0 && existing.length===71) return existing;
  const sig=_deviceSig();
  let h1=0x811c9dc5, h2=0x1000193;
  for(let i=0;i<sig.length;i++){ const c=sig.charCodeAt(i); h1=((h1^c)*0x01000193)>>>0; h2=((h2^(c+1))*0x85ebca6b)>>>0; }
  // FNV 种子确定性扩展 64hex（同步兜底）：格式合规、同机稳定；真 SHA-256 由 computeQid 异步覆盖
  let out="", x=((h1^h2)>>>0);
  while(out.length<64){ x=(((Math.imul(x,0x01000193))>>>0)+0x9e3779b9)>>>0; out+=x.toString(16).padStart(8,"0"); }
  const id="sha256:"+out.slice(0,64);
  localStorage.setItem(LS.qid, id); return id;
}
async function computeQid(){
  // 页面加载期异步计算真 SHA-256 设备签名（优先于 getQid 的 FNV 扩展兜底值）
  try{
    if(!(window.crypto&&crypto.subtle&&window.isSecureContext)) return;
    const buf=await crypto.subtle.digest("SHA-256", new TextEncoder().encode(_deviceSig()));
    const id="sha256:"+Array.from(new Uint8Array(buf)).map(function(b){return b.toString(16).padStart(2,"0");}).join("");
    localStorage.setItem(LS.qid, id);
  }catch(e){ /* 兜底值已合规，保持不变 */ }
}
function getQueryOrigin(){
  // ct-base coze_io_contract §1.3 / §8.6：query_origin = 设备标识（sha256:<64hex>，同机恒定）。
  // 2026-10-13 撤销方案 A 的 per-request nonce：经 Coze 端代码核实缓存键 = 归一化问题文本
  // md5 + 历史指纹、不含 query_origin（nonce 零缓存收益）；且 nonce 违反 §8.6「同机稳定」、
  // 污染飞书 query_origin 审计列（每行哈希漂移、无法归因）。入口区分由 entry_point 承载。
  return getQid();
}

// ── 2026-10-22 会话标识与上报（服务端 session_store 持久化上下文/缓存/去重）──
function getSessionId(){
  // 会话标识：localStorage 持久化（同机恒定），用于服务端跨轮/跨刷新上下文延续。
  try{
    let s = localStorage.getItem("ct_advisor_session");
    if(!s){ s = (window.crypto && crypto.randomUUID) ? crypto.randomUUID() : ("sess-"+Date.now()+"-"+Math.random().toString(36).slice(2,12)); localStorage.setItem("ct_advisor_session", s); }
    return s;
  }catch(e){ return "anon"; }
}
function _reportTurn(sid, q, answer, runId, difficulty){
  // 收到答案后上报服务端（fire-and-forget，不阻塞渲染），持久化到 session_store
  try{
    fetch("/api/turn", {method:"POST", headers:{"Content-Type":"application/json"},
      body: JSON.stringify({session_id:sid, question:q, answer:answer, run_id:runId||"", query_meta:{difficulty:difficulty||""}})}).catch(()=>{});
  }catch(e){}
}
function _reportFeedback(runId, rating, note){
  try{
    fetch("/api/feedback", {method:"POST", headers:{"Content-Type":"application/json"},
      body: JSON.stringify({session_id:getSessionId(), run_id:runId||"", rating:rating, note:note||""})}).catch(()=>{});
  }catch(e){}
}
function loadHist(){
  try{ state.hist = JSON.parse(localStorage.getItem(LS.hist))||[]; }catch(e){ state.hist=[]; }
  // 🔴 _chatSeq 重播种（2026-10-13）：_chatSeq 每次页面加载从 0 开始，而 localStorage 历史
  // 条目携带持久化 _id（1..N）。不重播种 → 新问题 _id=1 与历史 _id=1 冲突 → _chatNodes Map
  // 把新条目当已渲染旧条目跳过 → 新问题气泡不显示、typing 锚到旧问题下方、答案返回后界面
  // 仍显示旧回答（历史视图直接遍历数组所以正常——本次线上事故现象）。
  // 两遍法：先追平历史最大数字 _id，再给无 _id 老条目补号——避免混存时补号撞已有 _id。
  for(const h of state.hist){ if(h && h._id!=null && h._id>_chatSeq) _chatSeq=h._id; }
  for(const h of state.hist){ if(h && h._id==null) h._id=++_chatSeq; }
}
function saveHist(){ if(!_histDirty) return; localStorage.setItem(LS.hist, JSON.stringify(state.hist)); _histDirty=false; }
function loadLang(){ state.lang = localStorage.getItem(LS.lang) || (navigator.language||"zh").startsWith("zh")?"zh":"en"; window.WB_LANG = state.lang; }
function saveLang(){ localStorage.setItem(LS.lang, state.lang); }

/* ===================== i18n apply ===================== */
function t(){ return I18N[state.lang]; }
function applyLang(){
  const T = t(); window.WB_LANG = state.lang;
  document.documentElement.lang = state.lang==="zh"?"zh-CN":"en";
  const set=(id,v)=>{const e=document.getElementById(id); if(e) e.textContent=v;};
  set("appTitle",T.appTitle); set("appSub",T.appSub);
  set("liteNotice",T.liteNotice); set("cozeRoute",T.cozeRoute);
  set("navConsole",T.navConsole); set("navSkills",T.navSkills); set("navHistory",T.navHistory);
  set("mConsole",T.mConsole); set("mSkills",T.mSkills); set("mHistory",T.mHistory);
  set("pendingTitle",T.pendingTitle);
  set("consoleTitle",T.consoleTitle); set("sendLabel",T.sendLabel);
  set("bugBtnLabel",T.bugBtn);
  set("contLabel",T.contLabel);
  const _cbtn=document.getElementById("cancelBtn"); if(_cbtn) _cbtn.textContent=T.cancelRunLabel;
  set("sendHint",T.sendHint);
  const snav=document.getElementById("wb-side"); if(snav) snav.title=T.sideFoldTip;
  set("skillsTitle",T.skillsTitle); set("skillsIntro",T.skillsIntro);
  set("histTitle",T.histTitle);
  set("exportBtn",T.exportBtn); set("importBtn",T.importBtn); set("clearBtn",T.clearBtn);
  set("langLabel",T.langLabel);
  set("setEndpointL",T.setEndpointL); set("setEndpointH",T.setEndpointH);
  set("setTokenL",T.setTokenL); set("setTokenH",T.setTokenH);
  set("setContL",T.setContL); set("setContOn",T.setContOn); set("setContOff",T.setContOff);
  set("setTitle",T.setTitle); set("saveBtn",T.saveBtn); set("resetBtn",T.resetBtn); set("setNote",T.setNote);
  document.getElementById("qinput").placeholder = T.qPlaceholder;
  const chip=document.getElementById("attachChipLabel"); if(chip) chip.textContent=T.attachChipLabel;
  document.getElementById("attachInput").placeholder = T.attachPlaceholder;
  const afh=document.getElementById("attachFileHint"); if(afh) afh.textContent=T.attachFileHint;
  document.getElementById("contChk").checked = state.cfg.continuous!=="off";
  setConnState(lastConnOk, T);
  renderSkills(); renderHistory(); renderPending(); renderChat();
}
// 语言单入口（顶栏单按钮；设置抽屉已无 locale 下拉）
function wbToggleLang(){
  state.lang = state.lang==="zh"?"en":"zh"; saveLang();
  state.cfg.locale = state.lang; saveCfg();
  applyLang();
  if(window.wbHistory) window.wbHistory.rerender();   // WBList 重建文案（不重拉数据）
}

/* ===================== views ===================== */
const SKILLS_LOCKED = true;
function toggleSide(){
  const a=document.querySelector(".app"); if(!a) return;
  a.classList.toggle("side-collapsed");
  try{ localStorage.setItem(LS.side, a.classList.contains("side-collapsed")?"1":"0"); }catch(e){}
}
function switchView(v){
  if(v==="skills" && SKILLS_LOCKED) v="console";
  document.querySelectorAll(".view").forEach(s=>s.classList.remove("active"));
  document.getElementById("view-"+v).classList.add("active");
  document.querySelectorAll("nav.side .navitem, .bottomtab .navitem").forEach(n=>{ n.classList.toggle("active", n.dataset.view===v); });
  if(v==="history") renderHistory();
  if(v==="skills") renderSkills();
}

/* ===================== skills console ===================== */
function renderSkills(){
  const T=t(); const grid=document.getElementById("skillGrid"); grid.innerHTML="";
  T.tasks.forEach((tk,i)=>{
    const key = ["design","samplesize","registry","safety","literature","meta","regulatory"][i];
    const d=document.createElement("div"); d.className="qcard";
    d.innerHTML=`<div class="ic">${ICONS[tk.ic]||""}</div><div class="ti">${esc(tk.ti)}</div><div class="de">${esc(tk.de)}</div><div class="route">${esc(tk.route)}</div>`;
    d.onclick=()=>openSkillForm(key);
    grid.appendChild(d);
  });
}
function openSkillForm(key){
  const T=t(); const sk=SKILLS[key]; if(!sk) return;
  if(sk.referral){ openReferralDetail("meta-analysis"); return; }
  document.getElementById("modalTitle").textContent = T.tasks[Object.keys(SKILLS).indexOf(key)].ti;
  document.getElementById("modalDesc").textContent = T.tasks[Object.keys(SKILLS).indexOf(key)].de;
  const body=document.getElementById("modalBody"); body.innerHTML="";
  const form=document.createElement("form");
  sk.fields.forEach(f=>{
    const wrap=document.createElement("div"); wrap.className="field";
    const lab=document.createElement("label");
    lab.innerHTML = esc(typeof f.label==="string"? f.label : f.label[state.lang]) + (f.required?'<span class="req">*</span>':"");
    wrap.appendChild(lab);
    let inp;
    if(f.type==="textarea"){ inp=document.createElement("textarea"); if(f.rows) inp.rows=f.rows; if(f.ph) inp.placeholder=f.ph[state.lang]; }
    else if(f.type==="select"){ inp=document.createElement("select"); (f.options||[]).forEach(o=>{ const op=document.createElement("option"); op.value=o.v; op.textContent=(typeof o.t==="string"?o.t:o.t[state.lang]); inp.appendChild(op); }); }
    else if(f.type==="bool"){ inp=document.createElement("input"); inp.type="checkbox"; inp.style.width="auto"; }
    else { inp=document.createElement("input"); inp.type=(f.type==="num"?"number":"text"); if(f.ph) inp.placeholder=f.ph[state.lang]; }
    inp.id="f_"+key+"_"+f.key;
    if(f.def!==undefined && (f.type==="num"||f.type==="select")) inp.value=f.def;
    if(f.type==="bool" && f.def===true) inp.checked=true;
    wrap.appendChild(inp); form.appendChild(wrap);
  });
  const btns=document.createElement("div"); btns.className="row-btns";
  const send=document.createElement("button"); send.className="primarybtn"; send.type="button"; send.textContent=T.formSend;
  send.onclick=()=>{
    const vals={}; let missing=[];
    sk.fields.forEach(f=>{ const el=document.getElementById("f_"+key+"_"+f.key);
      let v=(f.type==="bool")? el.checked : el.value;
      if(f.type==="num"){ v=el.value===""? "":el.value; }
      vals[f.key]=v;
      if(f.required && (v===""||v===null||v===undefined)) missing.push(typeof f.label==="string"?f.label:f.label[state.lang]);
    });
    if(missing.length){ toast(T.reqField+missing.join("、")); return; }
    const q=sk.build(vals,T); closeModal();
    sendToCoze(q, "", {category:sk.category, accuracy:sk.accuracy||"", difficulty:"", continuous:state.cfg.continuous!=="off", meta:{skill:key}});
  };
  const cancel=document.createElement("button"); cancel.className="ghostbtn"; cancel.type="button"; cancel.textContent=T.formCancel; cancel.onclick=closeModal;
  btns.appendChild(send); btns.appendChild(cancel); form.appendChild(btns); body.appendChild(form); openModal();
}

/* ===================== console / chat ===================== */
// §性能（ct-base workbench_perf.md ④）：增量渲染——仅新增条目 append，不整表重建；
// 仅 init/导入/删除/清空/切语言 走 full 全量。配合下方 _mdCache 缓存 md2html，历史重渲染近乎零成本。
let _chatSeq = 0;
let _histDirty = false;
const _chatNodes = new Map(); // _id -> {user:Node, bot:Node|null}
function _bubbleBot(h){ return bubble("bot", h.answer, h.meta, h.need_tool? h:{need_tool:null}, h.error, h.ts, h); }
function _syncChatEntry(h){
  const log = document.getElementById("chatlog");
  if(!log) return;
  let rec = _chatNodes.get(h._id);
  if(!rec){
    const user = bubble("user", h.q, h.meta, null, false, h.ts);
    const bot = (h.answer!=null && h.answer!==undefined) ? _bubbleBot(h) : null;
    rec = {user, bot}; _chatNodes.set(h._id, rec);
    log.insertBefore(rec.user, log.firstChild);
    if(rec.bot) log.insertBefore(rec.bot, rec.user.nextSibling);
  } else if(!rec.bot && h.answer!=null && h.answer!==undefined){
    rec.bot = _bubbleBot(h);
    log.insertBefore(rec.bot, rec.user.nextSibling);
  }
}
function renderChat(opts){
  const log = document.getElementById("chatlog");
  if(!log) return;
  const full = !opts || opts.full;
  if(state.hist.length===0){ log.innerHTML=`<div class="empty">${esc(t().histEmpty)}</div>`; _chatNodes.clear(); return; }
  if(full){ log.innerHTML=""; _chatNodes.clear(); }
  const entries = state.hist; // 正序遍历（旧→新）；_syncChatEntry 逐条插到最前 → 最新记录显示在最上面
  for(const h of entries){
    if(!full && _chatNodes.has(h._id)) continue;
    _syncChatEntry(h);
  }
}
function fmtTime(ts){ try{ return new Date(ts||Date.now()).toLocaleTimeString([], {hour:"2-digit", minute:"2-digit"}); }catch(e){ return ""; } }
function bubble(role, text, meta, extra, isErr, ts, msgObj){
  const T=t(); const d=document.createElement("div"); d.className="msg "+role+(isErr? " err":"");
  const who = role==="user"? T.you : T.bot;
  const ava = role==="user" ? "#14509B" : "#1C6DD0";
  let metaHtml="";
  if(meta){ const tags=[];
    if(extra && extra.need_tool) tags.push(`<span class="tag" style="color:var(--wb-err);border-color:var(--wb-err)">${esc(T.needTool)}: ${esc(extra.need_tool)}</span>`);
    if(meta.cached) tags.push(`<span class="tag">${esc(T.cached)}</span>`);
    if(meta.docId) tags.push(`<span class="tag" title="${esc(String(meta.docId))}">📎 ${esc(T.docTag)}</span>`);
    if(meta.runId) tags.push(`<span class="tag">${esc(T.runId)}: ${esc(String(meta.runId).slice(0,8))}</span>`);
    metaHtml = tags.join(" ");
  }
  const tm = fmtTime(ts);
  // §20.15：Coze 顶层 message 字段 → 置顶可关闭 banner（仅承载表面提示）
  let bannerHtml="";
  if(role==="bot" && msgObj && msgObj.message){
    const m=msgObj.message; const lvl=m.level||"notice";
    const icon={tip:"💡",info:"ℹ️",notice:"📌",warning:"⚠️"}[lvl]||"📌";
    const label={tip:"提示",info:"说明",notice:"提示",warning:"提醒"}[lvl]||"提示";
    const dis=(m.dismissible!==false);
    bannerHtml=`<div class="coze-msg" style="display:flex;align-items:center;gap:6px;margin-bottom:8px;padding:6px 10px;border-radius:8px;background:rgba(28,109,208,.10);border:1px solid rgba(28,109,208,.25);font-size:13px;color:var(--wb-tx,#222)"><span style="font-size:14px">${icon}</span><b style="font-weight:600">${esc(label)}</b><span style="flex:1">${esc(m.text)}</span>${dis? '<button class="coze-msg-dismiss" style="margin-left:6px;border:none;background:transparent;cursor:pointer;font-size:15px;color:#888" title="隐藏提示">×</button>':''}</div>`;
  }
  // 缓存来源声明（2026-09-09，彤 规范）：命中云计算缓存 → 答案上方明示，非本次实时计算
  let cacheDeclHtml="";
  if(role==="bot" && meta && meta.cached){
    const zh=(document.documentElement.lang||"").indexOf("zh")===0;
    const txt=zh? "本答案来自云计算缓存（历史运行结果，非本次实时计算）。如需最新结果，请追问要求重新生成。" : "This answer is from the cloud cache (a previous run, not freshly computed for this request). Ask again for a fresh generation if needed.";
    cacheDeclHtml=`<div style="margin-bottom:6px;font-size:12px;color:#a16207;background:rgba(250,204,21,.12);border:1px solid rgba(250,204,21,.35);border-radius:6px;padding:4px 8px">📦 ${esc(txt)}</div>`;
  }
  d.innerHTML=`<div class="who"><span class="ava" style="background:${ava}"></span><span class="nm">${esc(who)}</span>${metaHtml}<span class="tm">${esc(tm)}</span></div><div class="body">${cacheDeclHtml}${bannerHtml}${role==="bot"? md2html(text||"") : esc(text)}</div>`;
  if(role==="bot" && msgObj && msgObj.message){
    const bd=d.querySelector(".coze-msg-dismiss");
    if(bd) bd.onclick=()=>{ const el=d.querySelector(".coze-msg"); if(el) el.style.display="none"; };
  }
  // 2026-10-22：满意度反馈（👍/👎 → /api/feedback），fire-and-forget
  if(role==="bot"){
    const fb=document.createElement("div"); fb.className="feedback";
    fb.style.cssText="margin-top:8px;display:flex;gap:8px;align-items:center;font-size:12px;color:var(--wb-sub)";
    const _rid=(meta&&meta.runId)||"";
    fb.innerHTML=`<span>${(t().helpful||"这篇回答有帮助吗？")}</span><button type="button" class="fb-btn" data-r="up" style="border:1px solid var(--wb-bd,#ddd);background:var(--wb-bg,#fff);border-radius:6px;cursor:pointer;padding:2px 8px">👍</button><button type="button" class="fb-btn" data-r="down" style="border:1px solid var(--wb-bd,#ddd);background:var(--wb-bg,#fff);border-radius:6px;cursor:pointer;padding:2px 8px">👎</button>`;
    fb.querySelectorAll(".fb-btn").forEach(b=>{ b.onclick=()=>{ _reportFeedback(_rid, b.dataset.r==="up"?1:-1); fb.querySelectorAll(".fb-btn").forEach(x=>x.disabled=true); b.textContent=b.dataset.r==="up"?"👍 已反馈":"👎 已反馈"; }; });
    d.appendChild(fb);
  }
  return d;
}
function lastTurns(n){
  const out=[]; const arr=state.hist.slice().reverse();
  for(const h of arr){ if(h.answer){ out.push({role:"user",content:h.q}); out.push({role:"assistant",content:h.answer}); } if(out.length>=n*2) break; }
  return out.slice(0,n*2);
}
function extractAnswer(data){
  if(typeof data==="string") return data.trim();
  if(!data || typeof data!=="object") return "";
  // _raw_b64_result：pollTask 适配 /task 返回 base64 字符串时转 UTF-8
  if(data._raw_b64_result && typeof data._raw_b64_result==="string"){
    const decoded = decodeB64Utf8(data._raw_b64_result);
    if(decoded) return decoded.trim();
    return data._raw_b64_result.trim();
  }
  const cand=[ data.final_answer, data.result, data.answer, data.content, data.output, data.text, data.reply, data.response,
    data.data && (data.data.final_answer ?? data.data.answer ?? data.data.content ?? data.data.text ?? data.data.output) ];
  for(const c of cand){ if(c===undefined||c===null||c==="") continue; if(typeof c==="string") return c.trim(); if(typeof c==="object"){ const s=extractAnswer(c); if(s) return s; } }
  return "";
}
function decodeB64Utf8(b64){
  // v1.3.9：base64 → UTF-8 文本（经典 binary-string 中转写法，兼容老 webview）
  try { return decodeURIComponent(escape(atob(b64))); } catch(e){ return null; }
}
function stripDelimiters(s){
  if(typeof s!=="string"||!s) return s;
  // v1.3.9：base64 ASCII-safe 载荷优先解码（ct-advisor 输出契约升级）；
  // 旧 <<<CT_ANSWER_START>>> 纯文本块保持兼容（legacy/debug 输出）。
  var m = s.match(/<<<CT_ANSWER_B64_START>>>\s*\r?\n([\s\S]*?)\r?\n\s*<<<CT_ANSWER_B64_END>>>/);
  if(m){
    var dec = decodeB64Utf8(m[1].replace(/\s+/g,""));
    if(dec!=null) return dec;
  }
  return s.replace(/<<<CT_ANSWER_START>>>/g, "").replace(/<<<CT_ANSWER_END>>>/g, "").replace(/^\s*[\r\n]+|[\r\n]+\s*$/g, "");
}
function detectVague(q){
  const s=(q||"").trim(); if(!s) return false;
  if(/(这个|那个|它|它们|这|那|这种|那些|该药|该方案)/.test(s) && s.length<=24) return true;
  if(/(前面|上面|刚才|上一条|上一个|上轮|上次|之前提到|前述|上述)/.test(s) && s.length<=30) return true;
  if(s.length<=8 && !/(SDTM|ADaM|AE|SAE|CSR|TLF|CRF|EDC|GCP|CDISC|ADSL|BDS|OCCDS|ADTTE|PK|PD|MedDRA|WHO|ICF|SUSAR|DSUR|RBM|QbD|ALCOA|IB|SAP|什么是|的定义|含义|如何|步骤|流程|时限|保存|填写|提交|上报|复核|正确|规范|要求|记录|报告|破盲|回收|发放)/i.test(s)) return true;
  const uncertain=/(不确定|不清楚|不知道|没想好|拿不准|没有头绪|not sure|unsure|don'?t know|no idea|not clear)/i.test(s);
  const hasObject=/(是否|能不能|可不可以|对不对|合理|合规|正确|appropriate|valid|acceptable|\bif\b)/i.test(s);
  if(uncertain && !hasObject) return true;
  return false;
}
function doSend(q, att){
  const qEl=document.getElementById("qinput"); const aEl=document.getElementById("attachInput");
  qEl.value=""; aEl.value="";
  const doc=_pendingDoc; _pendingDoc=null; renderAttachState();   // file_id 附件随本次发送消耗
  const ofmt=document.getElementById("outFmt"); const outputFormat=ofmt? ofmt.value : "auto";
  sendToCoze(q, att, { category:"", accuracy:"", difficulty:"", continuous:document.getElementById("contChk").checked, meta:{}, doc, output_format:outputFormat });
}
/* ===================== P0-B：本地引擎技能自动执行 ===================== */
function _isLocalSkill(tool){ const m=SKILL_META[tool]; return !!(m && m.engine==="local"); }
async function _autoRunLocalSkill(cur){
  const T=t(); const tool=cur.need_tool; const params=cur.params||{};
  // 在 bot 气泡下方插入「正在运行…」提示
  const log=document.getElementById("chatlog");
  const running=document.createElement("div"); running.className="msg bot"; running.style.opacity=".8";
  running.innerHTML=`<div class="who"><span class="ava" style="background:#1C6DD0"></span><span class="nm">${esc(T.bot)}</span></div><div class="body"><span class="typing"><i></i><i></i><i></i></span> ${esc(T.running||"正在本机运行…")}</div>`;
  log.appendChild(running); scrollChat();
  let ok=true, out="", note="";
  try{
    const r=await fetch("/api/run-skill", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({tool, params})});
    const data=await r.json(); ok=!!data.ok; out=data.stdout||""; note=data.note||"";
  }catch(e){ ok=false; note=e.message; }
  running.remove();
  // 缝合：草稿 + 技能执行结果
  const draft=cur.answer||"";
  const stitch = ok
    ? (draft + "\n\n---\n\n**本地技能执行结果（" + tool + "）：**\n\n" + out).trim()
    : (draft + "\n\n---\n\n**本地技能执行失败（" + tool + "）：** " + (note||"未知错误")).trim();
  cur.answer = stitch; cur.need_tool=null; cur.params={};
  saveHist(); renderChat(); renderPending(); updateBadge();
}

/* ===================== P0-A：Vague 澄清循环 UI ===================== */
// 澄清态：null 不在澄清中；{ original, previous_answers, round, question_profile, confirmation, att }
let _clarifyCtx = null;
async function _callClarify(q, previous_answers, question_profile, confirmation, round){
  const payload={ original_question:q, previous_answers, question_profile, confirmation, round, max_rounds:3 };
  try{
    const r=await fetch("/api/clarify", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(payload)});
    return await r.json();
  }catch(e){ return {status:"decidable", ambiguous:false, round, max_rounds:3, questions:[], question_profile:{}, confirmation:{}, error:String(e)}; }
}
function _renderClarifyBubble(q, questions){
  const T=t(); const log=document.getElementById("chatlog");
  const d=document.createElement("div"); d.className="msg bot clarify-bubble";
  d.innerHTML=`<div class="who"><span class="ava" style="background:#1C6DD0"></span><span class="nm">${esc(T.bot)}</span></div>
    <div class="body">${esc(q)}${questions.length? "<p style='margin:8px 0 4px;font-weight:600;color:var(--wb-brand)'>"+(T.clarifyAsk||"在回答之前，请帮我确认以下几点：")+"</p><ol style='margin:4px 0 4px 20px'>"+questions.map(s=>"<li style='margin:3px 0'>"+esc(s)+"</li>").join("")+"</ol><p style='font-size:12px;color:var(--wb-sub);margin-top:6px'>"+(T.clarifyHint||"回复你的答案，我会继续追问（最多 3 轮）或开始分析。")+"</p>":""}</div>`;
  log.appendChild(d); scrollChat();
}
function _removeClarifyBubbles(){ document.querySelectorAll(".clarify-bubble").forEach(n=>n.remove()); }
// 已保留 showVagueConfirm 但不再由 sendConsole 调用（替换为澄清循环）；保留以备 fallback
function showVagueConfirm(q, att){
  const T=t();
  document.getElementById("modalTitle").textContent=T.vagueTitle;
  document.getElementById("modalDesc").textContent=T.vagueDesc;
  const body=document.getElementById("modalBody"); body.innerHTML="";
  const bar=document.createElement("div"); bar.className="row-btns";
  const bRefine=document.createElement("button"); bRefine.type="button"; bRefine.className="ghostbtn"; bRefine.textContent=T.vagueRefine;
  bRefine.onclick=()=>{ closeModal(); document.getElementById("qinput").focus(); };
  const bSend=document.createElement("button"); bSend.type="button"; bSend.className="primarybtn"; bSend.textContent=T.vagueProceed;
  bSend.onclick=()=>{ closeModal(); doSend(q, att); };
  bar.appendChild(bRefine); bar.appendChild(bSend); body.appendChild(bar); openModal();
}
async function sendConsole(){
  const qEl=document.getElementById("qinput"); const aEl=document.getElementById("attachInput");
  const q=qEl.value.trim(); const att=aEl.value.trim();
  if(!q) return;
  // P2：长输入引导（数据：8 条 >10000 字，长输入比短问慢 36%）——提示上传附件，不阻断发送
  if(q.length>2000){ try{ toast("内容较长（"+q.length+" 字），建议作为文件附件上传以获得更稳定的解析；也可直接发送。"); }catch(e){} }
  if(_clarifyCtx){
    // 澄清态：本轮答案追加 → 再调一次 clarify
    _clarifyCtx.previous_answers.push(q);
    _removeClarifyBubbles();
    const r=await _callClarify(_clarifyCtx.original, _clarifyCtx.previous_answers, _clarifyCtx.question_profile, _clarifyCtx.confirmation, _clarifyCtx.round+1);
    if(r.status==="need_clarify" && r.questions && r.questions.length){
      _clarifyCtx.round=r.round; _clarifyCtx.question_profile=r.question_profile||{}; _clarifyCtx.confirmation=r.confirmation||{};
      _renderClarifyBubble(_clarifyCtx.original, r.questions);
    } else {
      // decidable / forced_decide → 清空态，发 Coze
      const ctx=_clarifyCtx; _clarifyCtx=null; _removeClarifyBubbles();
      // 将 confirmation 摘要拼到问题前作为上下文（前端轻缝合）
      const summary=ctx.confirmation && ctx.confirmation.summary;
      const enriched = summary? (ctx.original + "\n\n[已确认信息]\n" + summary) : ctx.original;
      doSend(enriched, att);
    }
    return;
  }
  if(detectVague(q)){
    // P0-A：启动澄清循环
    _clarifyCtx={ original:q, previous_answers:[], round:0, question_profile:{}, confirmation:{}, att };
    const r=await _callClarify(q, [], {}, {}, 0);
    if(r.status==="need_clarify" && r.questions && r.questions.length){
      _clarifyCtx.question_profile=r.question_profile||{}; _clarifyCtx.confirmation=r.confirmation||{};
      _renderClarifyBubble(q, r.questions);
    } else {
      // 无歧义 → 直接发 Coze（极少路径）
      _clarifyCtx=null; doSend(q, att);
    }
    return;
  }
  doSend(q, att);
}
function setBtnLoading(T){ const b=document.getElementById("sendBtn"); b.classList.add("loading"); b.disabled=true; document.getElementById("sendLabel").textContent=T.sending; const _cb=document.getElementById("cancelBtn"); if(_cb) _cb.style.display=""; }
function setBtnSent(T){ const b=document.getElementById("sendBtn"); b.classList.remove("loading"); b.classList.add("sent"); b.disabled=false; document.getElementById("sendLabel").textContent=T.sent; }
function resetBtn(T){ const b=document.getElementById("sendBtn"); b.classList.remove("loading","sent"); b.disabled=false; document.getElementById("sendLabel").textContent=T.sendLabel; const _cb=document.getElementById("cancelBtn"); if(_cb) _cb.style.display="none"; }
// §20.15：归一化 Coze 响应信封顶层可选 message 字段（与 ct-base coze_io_contract §5 一致）
function normalizeCozeMessage(raw){
  if(!raw) return null;
  if(typeof raw==="string"){ raw=raw.trim(); return raw? {level:"notice", text:raw, dismissible:true}:null; }
  if(Array.isArray(raw)){ const parts=[]; raw.forEach(it=>{ const s=normalizeCozeMessage(it); if(s&&s.text) parts.push(s.text); }); return parts.length? {level:"notice", text:parts.join("\n"), dismissible:true}:null; }
  if(typeof raw==="object"){ const text=(typeof raw.text==="string")? raw.text.trim():""; if(!text) return null; const lv=raw.level; const level=(["tip","info","notice","warning"].indexOf(lv)>=0)? lv:"notice"; const dis=(typeof raw.dismissible==="boolean")? raw.dismissible:true; return {level, text, dismissible:dis}; }
  return null;
}
// 异步任务轮询：GET /task/{task_id} 每 2.5s 一次，上限 20 分钟（服务端 TIMEOUT_SECONDS=900）。
// 2026-10-13 引入：同步 /run 会被 Coze 云端网关 stgw 的 60s 硬超时掐断（重问题必 504），
// 非流式默认路径改走 POST /async_run（秒回 task_id）+ 本轮询。返回 row.result —— 与 /run
// 同构的答案信封（final_answer/cache_hit/doc_id…），走原有 extractAnswer 渲染路径。
async function pollTask(tid, T){
  const base=(state.cfg.endpoint||"/run").replace(/\/run\/?$/, "/");
  const deadline=Date.now()+20*60*1000;
  const ph={"Authorization":"Bearer "+(state.cfg.token||"")};
  while(Date.now()<deadline){
    await new Promise(r=>setTimeout(r,2500));
    let resp;
    try{ resp=await fetch(base+"task/"+encodeURIComponent(tid), {headers:ph}); }
    catch(e){ continue; }
    if(resp.status===404) continue;
    if(!resp.ok) throw new Error(T.errHttp+resp.status);
    const row=await resp.json();
    const st=String(row.status||"").toLowerCase();
    if(st==="completed"){
      // 多位置适配：row.result（对象）/ row.result（base64字符串）/ row.data / row.output / row.final_answer
      const r = row.result;
      if(r && typeof r==="object") return r;
      if(r && typeof r==="string") return { _raw_b64_result: r };
      if(row.data && typeof row.data==="object") return row.data;
      if(row.output && typeof row.output==="string") return { _raw_b64_result: row.output };
      if(row.final_answer) return { final_answer: row.final_answer };
      // result 字段缺失/为空 → 返回完整 row 供 extractAnswer 兜底
      return row;
    }
    if(st==="cancelled") return {status:"cancelled"};
    if(st==="failed" || st==="error" || st==="timeout"){
      const e0=row.error;
      const em=typeof e0==="string"? e0 : (e0 && (e0.message||e0.error_message)) || ("task "+st);
      throw new Error(String(em));
    }
  }
  throw new Error(T.errHttp+"task poll timeout (20min)");
}
async function sendToCoze(q, att, opts){
  const T=t();
  if(!isHttpOrigin()){
    const pill=document.getElementById("connPill"); pill.className="pill warn"; pill.textContent=T.connProxy; pill.title=T.bannerExternal;
    toast(T.connProxy); return;
  }
  const continuous=opts.continuous;
  // P1 取消契约：X-Run-Id 上游指定 run_id，服务端 /cancel/{run_id} 按它精确取消
  const runId=(window.crypto&&crypto.randomUUID)? crypto.randomUUID() : ("wb-"+Date.now()+"-"+Math.random().toString(36).slice(2,10));
  window._curRunId=runId;
  const cur={_id: ++_chatSeq, q, answer:null, meta:{difficulty:opts.difficulty, cached:false, runId:"", docId:"", docCached:false, skill:opts.meta&&opts.meta.skill||null}, need_tool:null, params:{}, ts:Date.now(), sample:false};
  _histDirty = true;
  state.hist.push(cur); renderChat(); scrollChat();
  const log=document.getElementById("chatlog");
  const typing=document.createElement("div"); typing.className="msg bot";
  const _t0=Date.now();
  typing.innerHTML=`<div class="who"><span class="ava" style="background:#1C6DD0"></span><span class="nm">${esc(T.bot)}</span></div><div class="body"><span class="typing"><i></i><i></i><i></i></span> <span class="prog" id="prog_${runId}">已提交，云端分析中…（0s）</span></div>`;
  // P0-1：即时进度 + 计时（p50 68.7s，用户常以为没发出）。提交即显示，每秒刷新已等待秒数。
  const _progTimer=setInterval(()=>{ const el=document.getElementById("prog_"+runId); if(el) el.textContent=`云端分析中…（已 ${Math.round((Date.now()-_t0)/1000)}s）`; }, 1000);
  const firstUser=log.querySelector(".msg.user");
  if(firstUser && firstUser.nextSibling) log.insertBefore(typing, firstUser.nextSibling); else log.appendChild(typing);
  scrollChat(); setBtnLoading(T);
  // ct-base coze_io_contract §1.3：顶层信封直发 entry_point="workbench"（显式值优先，代理
  // _inject_entry_point 仅作缺失兜底；后端 GraphInput.entry_point 声明字段经 state 透传飞书）。
    const payload={ entry_point:"workbench", query_meta:{ difficulty:opts.difficulty, category:opts.category||"", accuracy:opts.accuracy||"", query_origin:getQueryOrigin(), locale: state.cfg.locale || state.lang, output_format: opts.output_format||"auto" },
      original_question: att? (q+"\n\n[附件]\n"+att) : q, draft_answer:"", conversation_history: continuous? lastTurns(10):[] };
  // P0 v1.26 file_id 通道：上传的文件不再内联全文，改以 doc_context 字符串信封随请求发送
  if(opts.doc && opts.doc.file_id){
    payload.doc_context = JSON.stringify({ doc_id:"doc_"+opts.doc.file_id, mode:"file_id", file_id:opts.doc.file_id,
      file_url:"", file_name:opts.doc.file_name, origin_name:opts.doc.origin_name, instruction:"" });
  }
  try{
    const headers={"Content-Type":"application/json", "X-Run-Id":runId, "X-Session-Id":getSessionId()};
    if(state.cfg.token) headers["Authorization"]="Bearer "+state.cfg.token;
    let data;
    // 异步提交 + 轮询（默认路径；原同步 /run 撞 stgw 60s 必 504）。
    const ap = (state.cfg.endpoint || "/run").replace(/\/run\/?$/, "/async_run");
    const resp=await fetch(ap, {method:"POST", headers, body:JSON.stringify(payload)});
    if(!resp.ok){ const _t=await resp.text(); throw new Error(T.errHttp+resp.status+(_t? "："+_t.slice(0,200):"")); }
    const sub=await resp.json();
    const tid=sub && (sub.task_id || sub.run_id);
    if(!tid) throw new Error(T.errHttp+"async_run: no task_id");
    data = await pollTask(tid, T);
    if(data && typeof data==="object" && data.status==="cancelled"){ cur.answer = T.cancelOk; }
    else{
      const bizErr = (data && typeof data==="object")? (data.error||data.message||data.msg||"") : "";
      const answer = extractAnswer(data);
      if(!answer){ cur.answer = bizErr? String(bizErr) : (T.errEmpty + (data && typeof data==="object" ? "\n\n[实际响应]\n" + JSON.stringify(data).slice(0,500) : "")); cur.error = true; }
      else{ cur.answer = stripDelimiters(answer); cur.need_tool = data.need_tool || null; cur.params = data.params || {}; cur.meta.cached = !!data.cache_hit; cur.meta.runId = data.run_id || "";
        cur.meta.docId = data.doc_id || ""; cur.meta.docCached = data.doc_cached===true;
        // P0-B：本地引擎技能 → 自动执行，缝合结果到聊天流
        if(cur.need_tool && _isLocalSkill(cur.need_tool)){ _autoRunLocalSkill(cur); } }
    }
    cur.message = normalizeCozeMessage(data.message);  // §20.15：置顶提示（可关闭）
    if(!cur.error && cur.answer){ _reportTurn(getSessionId(), q, cur.answer, cur.meta.runId, opts.difficulty); }
    saveHist(); clearInterval(_progTimer); typing.remove(); renderChat(); renderPending(); updateBadge();
    if(cur.error){ resetBtn(T); } else { setBtnSent(T); setTimeout(()=>resetBtn(t()), 1300); }
  }catch(e){
    clearInterval(_progTimer); typing.remove(); cur.answer = (e instanceof TypeError)? T.errNet : (T.errHttp + e.message); cur.error=true;
    saveHist(); renderChat();
    const pill=document.getElementById("connPill"); pill.className="pill err"; pill.textContent=T.connErr;
    pill.title = (e instanceof TypeError)? T.bannerExternal : (T.bannerWarn+" run_app.bat");
    resetBtn(T);
  }finally{ window._curRunId=""; scrollChat(); }
}
// P1：取消本次运行（服务端 asyncio task 取消，LangGraph 在节点 await 点优雅退出）
async function cancelRun(){
  const T=t(); const rid=window._curRunId; if(!rid) return;
  try{ await fetch("/cancel/"+encodeURIComponent(rid), {method:"POST"}); toast(T.cancelSent); }
  catch(e){ toast(T.errNet+": "+e.message); }
}
function onKey(e){ if(e.key==="Enter" && !e.shiftKey && !e.isComposing){ e.preventDefault(); sendConsole(); } }
function scrollChat(){ const m=document.querySelector("main"); if(m) m.scrollTo({top:0, behavior:"smooth"}); }

/* ===================== pending / need_tool detail ===================== */
function renderPending(){
  const T=t(); const strip=document.getElementById("pendingStrip");
  const items=state.hist.filter(h=>h.need_tool);
  const card=document.getElementById("pendingCard");
  if(card) card.style.display = items.length? "" : "none";
  document.getElementById("pendingEmpty").textContent = items.length? "" : T.pendingEmpty;
  strip.querySelectorAll(".pending-chip").forEach(n=>n.remove());
  items.slice().reverse().forEach((h)=>{
    const c=document.createElement("div"); c.className="pending-chip";
    c.innerHTML=`<div class="t">${esc(T.needTool)}</div><div class="s">${esc(h.need_tool)}</div>`;
    // 关闭按钮：清除该条目的 need_tool，不点开详情
    const x=document.createElement("button"); x.type="button"; x.textContent="×";
    x.style.cssText="position:absolute;top:4px;right:6px;border:none;background:transparent;cursor:pointer;font-size:15px;color:var(--wb-sub);line-height:1;padding:0 2px";
    x.onclick=(e)=>{ e.stopPropagation(); h.need_tool=null; saveHist(); renderPending(); updateBadge(); };
    c.style.position="relative"; c.appendChild(x);
    c.onclick=()=>openNeedToolDetail(h); strip.appendChild(c);
  });
  updateBadge();
}
function updateBadge(){
  const n=state.hist.filter(h=>h.need_tool).length;
  const b=document.getElementById("pendingBadge");
  if(n>0){ b.style.display="inline-block"; b.textContent=n; } else b.style.display="none";
}
function openNeedToolDetail(h){
  const T=t(); const tool=h.need_tool; const m=SKILL_META[tool];
  document.getElementById("modalTitle").textContent = T.ntTitle;
  document.getElementById("modalDesc").textContent = (tool||"") + " · " + (m? (m.engine==="coze"?T.ntEngineCoze:(m.referral?T.ntReferral:T.ntEngineLocal)) : "");
  const body=document.getElementById("modalBody"); body.innerHTML="";
  if(m && m.referral){ body.appendChild(referralBlock(tool)); }
  else if(m && m.engine==="coze" && tool==="ct-samplesize"){
    const note=document.createElement("div"); note.className="note"; note.textContent=T.ntSampleNote; body.appendChild(note);
    if(m.prep) prepBlock(body, m.prep);
    const cmd=cliCmd(tool, h.params); if(cmd) cmdBlock(body, cmd, T);
    reaskBlock(body, h, T);
  } else if(m && m.engine==="local"){
    if(m.prep) prepBlock(body, m.prep);
    const cmd=cliCmd(tool, h.params); if(cmd) cmdBlock(body, cmd, T);
    const runBtn=document.createElement("button"); runBtn.className="primarybtn"; runBtn.textContent=T.runLocal; runBtn.style.marginTop="10px";
    runBtn.onclick=()=>runLocalSkill(tool, h.params); body.appendChild(runBtn);
    reaskBlock(body, h, T);
  } else { const note=document.createElement("div"); note.className="note"; note.textContent=(T.ntPrepHint)+" "+JSON.stringify(h.params||{}); body.appendChild(note); }
  openModal();
}
function openReferralDetail(tool){
  const T=t(); const m=SKILL_META[tool];
  document.getElementById("modalTitle").textContent = "@skill:"+tool;
  document.getElementById("modalDesc").textContent = T.ntReferral;
  const body=document.getElementById("modalBody"); body.innerHTML=""; body.appendChild(referralBlock(tool)); openModal();
}
function prepBlock(body, prep){ const T=t(); const d=document.createElement("div"); d.className="note"; d.innerHTML="<b>"+esc(T.ntPrepHint)+"</b> "+esc(typeof prep==="string"?prep:prep[state.lang]); body.appendChild(d); }
function cmdBlock(body, cmd, T){ const box=document.createElement("div"); box.className="cmdbox"; box.textContent=cmd; body.appendChild(box);
  const btns=document.createElement("div"); btns.className="row-btns"; const cp=document.createElement("button"); cp.className="ghostbtn"; cp.textContent=T.ntCopy; cp.onclick=()=>copyText(cmd); btns.appendChild(cp); body.appendChild(btns); }
function referralBlock(tool){ const T=t(); const d=document.createElement("div");
  const note=document.createElement("div"); note.className="note"; note.textContent=T.ntReferralNote; d.appendChild(note);
  const box=document.createElement("div"); box.className="refbox";
  box.innerHTML = `在 WorkBuddy 中调用：<b>@skill:${esc(tool)}</b><br>`+`GitHub：<a href="https://github.com/medstatstar/${esc(tool)}" target="_blank" rel="noopener">https://github.com/medstatstar/${esc(tool)}</a>`;
  d.appendChild(box); return d; }
function reaskBlock(body, h, T){ const btns=document.createElement("div"); btns.className="row-btns";
  const ra=document.createElement("button"); ra.className="ghostbtn"; ra.textContent=T.reask;
  ra.onclick=()=>{ closeModal(); document.getElementById("qinput").value=h.q; switchView("console"); document.getElementById("qinput").focus(); };
  btns.appendChild(ra); body.appendChild(btns); }
function copyText(s){ navigator.clipboard.writeText(s).then(()=>toast(t().copied)).catch(()=>toast(s)); }

/* ===================== 附件文件上传（v1.26 file_id 通道） ===================== */
let _pendingDoc=null;   // {file_id, file_name, origin_name, size}：已上传待随问题发送的文档
function renderAttachState(){
  const note=document.getElementById("extractNote"); if(!note) return;
  const T=t();
  if(_pendingDoc){
    const kb=_pendingDoc.size? "（"+Math.max(1,Math.round(_pendingDoc.size/1024))+" KB）":"";
    note.style.display="block"; note.style.borderColor="rgba(5,150,105,.4)"; note.style.color="var(--wb-ok)";
    note.textContent=T.attachUploaded+_pendingDoc.origin_name+kb;
  }else{ note.style.display="none"; }
}
async function handleAttachFile(){
  const T=t(); const inp=document.getElementById("attachFile");
  const f=inp.files&&inp.files[0]; if(!f) return;
  if(!isHttpOrigin()){ toast(T.connProxy); return; }
  const note=document.getElementById("extractNote");
  note.style.display="block"; note.style.borderColor="var(--wb-line)"; note.style.color="var(--wb-sub)"; note.textContent=T.attachUploading;
  try{
    const fd=new FormData(); fd.append("file", f);
    const r=await fetch("/upload_file", {method:"POST", body:fd});
    const data=await r.json();
    if(data && data.file_id){
      _pendingDoc={file_id:data.file_id, file_name:data.file_name||f.name, origin_name:f.name, size:data.size||f.size};
      renderAttachState(); toast(T.attachUploaded+f.name);
    }else{
      const why=(data && (typeof data.detail==="string"? data.detail : (data.note||data.message)))||T.errEmpty;
      note.style.borderColor="rgba(220,38,38,.4)"; note.style.color="var(--wb-err)"; note.textContent=T.attachUploadFail+why;
    }
  }catch(e){ note.style.display="block"; note.style.borderColor="rgba(220,38,38,.4)"; note.style.color="var(--wb-err)"; note.textContent=T.attachUploadFail+e.message; }
  finally{ inp.value=""; }
}

/* ===================== 反馈 / Bug 上报（ct-safety 同款两段式：填描述 → 预览脱敏报告 → 确认发送/返回修改） ===================== */
let bugConfirmed=false;
function openFeedback(){
  const T=t();
  bugConfirmed=false;
  document.getElementById("bugTitleEl").textContent=T.bugTitle;
  document.getElementById("bugTipEl").textContent=T.bugTip;
  document.getElementById("bugDescLabelEl").textContent=T.bugDescLabel;
  const ctx=document.getElementById("bugCtx");
  if(ctx){
    const meta=["skill: ct-advisor","page: "+location.href,"locale: "+state.lang,"ts: "+new Date().toISOString()].join("\n");
    ctx.textContent=T.bugCtxLabel+"\n"+meta;
  }
  const ta=document.getElementById("bugDesc"); ta.value=""; ta.placeholder=T.bugDescPh;
  const pv=document.getElementById("bugPreview"); pv.style.display="none"; pv.textContent="";
  document.getElementById("bugSubmitBtn").textContent=T.bugSubmit;
  const b=document.getElementById("bugBackBtn"); b.style.display="none"; b.textContent=T.bugBack;
  document.getElementById("bugCancelBtn").textContent=T.bugCancel;
  const m=document.getElementById("bugMsg"); m.textContent=""; m.style.color="";
  document.getElementById("bugModal").classList.add("open");
  document.getElementById("modalMask").classList.add("open");
  setTimeout(function(){ ta.focus(); },0);
}
function closeFeedback(){
  const mm=document.getElementById("bugModal"); if(mm) mm.classList.remove("open");
  document.getElementById("modalMask").classList.remove("open");
}
function bugBack(){
  const T=t();
  bugConfirmed=false;
  const pv=document.getElementById("bugPreview"); pv.style.display="none"; pv.textContent="";
  document.getElementById("bugSubmitBtn").textContent=T.bugSubmit;
  document.getElementById("bugBackBtn").style.display="none";
  const m=document.getElementById("bugMsg"); m.textContent=""; m.style.color="";
}
function buildBugPreview(desc){
  const T=t();
  const meta=["  skill: ct-advisor","  page: "+location.href,"  locale: "+state.lang].join("\n");
  return T.bugPreviewTitle+"\n"+meta+"\n\n  description (confirmed by you):\n    "+String(desc).split("\n").join("\n    ");
}
function submitFeedback(){
  const T=t();
  const ta=document.getElementById("bugDesc"); const m=document.getElementById("bugMsg"); const s=document.getElementById("bugSubmitBtn");
  const desc=ta.value.trim();
  if(!desc){ m.textContent=T.bugFill; m.style.color="var(--wb-err)"; return; }
  if(!bugConfirmed){
    const pv=document.getElementById("bugPreview");
    pv.textContent=buildBugPreview(desc); pv.style.display="block";
    s.textContent=T.bugSubmitConfirm;
    document.getElementById("bugBackBtn").style.display="inline-flex";
    m.textContent=T.bugConfirmTip; m.style.color="";
    bugConfirmed=true;
    return;
  }
  s.disabled=true; s.textContent=T.bugSubmitting;
  fetch("/api/bug-report",{method:"POST",headers:{"Content-Type":"application/json"},
    body:JSON.stringify({description:desc, meta:{page:location.href, locale:state.lang}})})
    .then(function(r){ return r.json(); })
    .then(function(j){
      if(!j.ok) throw new Error(j.note||"bad response");
      m.style.color="var(--wb-ok)"; m.textContent=T.bugLocal.replace("{id}", j.id||"");
      setTimeout(closeFeedback, 1700);
    })
    .catch(function(e){
      s.disabled=false; s.textContent=T.bugSubmit;
      m.style.color="var(--wb-err)"; m.textContent=T.bugFail+" "+String(e.message||e);
    });
}

/* ===================== need_tool 本机运行 ===================== */
async function runLocalSkill(tool, params){
  const T=t(); const body=document.getElementById("modalBody");
  const resBox=document.createElement("div"); resBox.className="cmdbox"; resBox.style.whiteSpace="pre-wrap"; resBox.style.marginTop="10px";
  resBox.textContent=T.running; body.appendChild(resBox);
  try{ const r=await fetch("/api/run-skill", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({tool, params})});
    const data=await r.json();
    if(data.ok){ resBox.textContent="["+T.runLocalResult+"]\n"+(data.stdout||""); }
    else{ resBox.style.borderColor="var(--wb-err)"; resBox.textContent="["+T.runLocalResult+" ×]\n"+(data.note||"")+(data.stdout?("\n\n"+data.stdout):""); }
  }catch(e){ resBox.style.borderColor="var(--wb-err)"; resBox.textContent="运行请求失败："+e.message; }
}

/* ===================== 历史列表（WBList · 卡片行模板 · 决策 C） ===================== */
let wbHistory = null;
function histRows(){ return state.hist.slice().reverse().map(h=>{  // 倒序：最新记录排最前
  const id = h.id || (h.id = "h"+h.ts+"_"+Math.random().toString(36).slice(2,7));
  return { id, q:h.q, ts:h.ts, difficulty:(h.meta&&h.meta.difficulty)||"", needTool:h.need_tool||"",
    answer:h.answer||"", summary:(h.answer? (h.answer.length>140? h.answer.slice(0,140)+"…":h.answer):"—") };
}); }
const _histExpanded = new Set(); // 已展开完整回答的历史卡片 row.id（refresh/翻页/搜索后保持状态）
function ctHistToggle(id){
  if(_histExpanded.has(id)) _histExpanded.delete(id); else _histExpanded.add(id);
  if(wbHistory) wbHistory.refresh(); else renderHistory();
}
function histCard(r, lang){
  const T=I18N[lang]; const d=new Date(r.ts); const tstr=isNaN(d)? "":d.toLocaleString();
  const diff = r.difficulty? `<span class="wb-pill">${esc(r.difficulty)}</span>`:"";
  const nt = r.needTool? `<span class="wb-pill" style="background:var(--wb-err-bg);color:var(--wb-err);border-color:var(--wb-err)">${esc(T.needTool)}: ${esc(r.needTool)}</span>`:"";
  // 2026-10-13：单击问题/回答区切换展开——折叠态 140 字摘要 + 提示；展开态 md2html 全文（与对话气泡同渲染）
  const open = _histExpanded.has(r.id);
  const ans = open
    ? `${md2html(r.answer||"")}<div class="hist-fold">▲ ${esc(T.histFold||"收起")}</div>`
    : `${esc(r.summary)}${(r.answer && r.answer.length>140)? `<span class="hist-more"> …${esc(T.histMore||"点击查看全文")}</span>`:""}`;
  return `<div class="hist-q" onclick="ctHistToggle('${esc(r.id)}')" title="${esc(T.histMore||"")}">${esc(r.q)}</div>
    <div class="hist-m">${esc(tstr)} ${diff} ${nt}</div>
    <div class="hist-a${open?" expanded":""}" onclick="ctHistToggle('${esc(r.id)}')">${ans}</div>
    <button type="button" class="wb-list-act" style="position:absolute;bottom:10px;right:54px" onclick="ctReask('${esc(r.id)}', event)" title="${esc(T.histReask)}">${ICONS.reask}</button>`;
}
function ctReask(id, ev){ if(ev&&ev.stopPropagation) ev.stopPropagation(); const h=state.hist.find(x=>(x.id||"")===id); if(h){ document.getElementById("qinput").value=h.q; switchView("console"); document.getElementById("qinput").focus(); } }
function initHistoryList(){
  if(wbHistory){ wbHistory.refresh(); return; }
  wbHistory = WBList.create({
    mount:"wb-hist-list", rowId:"id", pageSize:10, selectable:false,
    columns:[
      {key:"q", label:{zh:"问题",en:"Question"}, searchable:true},
      {key:"answer", label:{zh:"答案",en:"Answer"}, searchable:true},
      {key:"ts", label:{zh:"时间",en:"Time"}, sortable:true, sortValue:(r)=>r.ts},
      {key:"difficulty", label:{zh:"难度",en:"Difficulty"}, sortable:true}
    ],
    fetchData: histRows,   // 数据源接线：histRows() 已倒序（最新在前）；WBList 默认不重排，保持传入顺序
    rowRender: histCard, onDelete: delHistRow,
    i18nExtra: { wblEmpty: t().histEmpty, wblConfirmDel: t().clearConfirm? "确认删除这条记录？" : "确认删除这条记录？" }
  });
}
function renderHistory(){ initHistoryList(); }
function delHistRow(row){
  state.hist = state.hist.filter(h=> (h.id||"")!==row.id);
  saveHist(); if(wbHistory) wbHistory.refresh(); renderChat(); renderPending(); updateBadge();
}
function exportJSON(){
  const blob=new Blob([JSON.stringify(state.hist,null,2)],{type:"application/json"});
  const a=document.createElement("a"); a.href=URL.createObjectURL(blob); a.download="ct-advisor-history.json"; a.click();
  toast(t().saved);
}
function importJSON(e){
  const f=e.target.files[0]; if(!f) return;
  const r=new FileReader();
  r.onload=()=>{ try{ const data=JSON.parse(r.result); if(Array.isArray(data)){ state.hist=data; state.hist.forEach(h=>{ if(h._id==null) h._id=++_chatSeq; else if(h._id>_chatSeq) _chatSeq=h._id; }); _histDirty=true; saveHist(); renderHistory(); renderChat({full:true}); renderPending(); toast(t().saved); } }catch(err){ toast(t().errHttp+"invalid JSON"); } };
  r.readAsText(f); e.target.value="";
}
function clearHistory(){ if(!confirm(t().clearConfirm)) return; state.hist=[]; saveHist(); renderHistory(); renderChat(); renderPending(); updateBadge(); }

/* ===================== settings ===================== */
function openSettings(){
  loadCfg();
  document.getElementById("setEndpoint").value=state.cfg.endpoint;
  document.getElementById("setToken").value=state.cfg.token;
  document.getElementById("setCont").value=state.cfg.continuous||"on";
  document.getElementById("drawer").classList.add("open"); document.getElementById("drawerMask").classList.add("open");
}
function closeSettings(){ document.getElementById("drawer").classList.remove("open"); document.getElementById("drawerMask").classList.remove("open"); }
function saveSettings(){
  state.cfg.endpoint=document.getElementById("setEndpoint").value.trim()||REMOTE_DEFAULT.endpoint;
  state.cfg.token=document.getElementById("setToken").value.trim()||REMOTE_DEFAULT.token;
  state.cfg.locale=state.lang; state.cfg.continuous=document.getElementById("setCont").value;
  saveCfg(); closeSettings(); applyLang(); toast(t().saved); checkProxy();
}
function resetSettings(){
  state.cfg={endpoint:REMOTE_DEFAULT.endpoint, token:REMOTE_DEFAULT.token, locale:state.lang, continuous:"on"};
  saveCfg(); openSettings(); toast(t().saved); checkProxy();
}

/* ===================== modal ===================== */
function openModal(){ document.getElementById("modal").classList.add("open"); document.getElementById("modalMask").classList.add("open"); }
function closeModal(){ document.getElementById("modal").classList.remove("open"); document.getElementById("modalMask").classList.remove("open"); }

/* ===================== utils ===================== */
function esc(s){ return String(s==null?"":s).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",'"':"&quot;","'":"&#39;",">":">"}[c])); }
function toast(msg){ const el=document.getElementById("toast"); el.textContent=msg; el.classList.add("show"); el.classList.remove("err"); setTimeout(()=>el.classList.remove("show"),1800); }

/* markdown -> html (safe) */
const _mdCache = new Map(); // §性能 ④：(text,lang) -> html，避免历史全量重解析
const _MD_CACHE_MAX = 500;
function md2html(src){
  if(src==null) return "";
  const _k = (state.lang||"zh") + " " + src;
  const _hit = _mdCache.get(_k);
  if(_hit!==undefined) return _hit;
  const _html = _md2htmlImpl(src);
  if(_mdCache.size >= _MD_CACHE_MAX) _mdCache.clear();
  _mdCache.set(_k, _html);
  return _html;
}
function _md2htmlImpl(src){
  if(src==null) return "";
  const escSrc=esc(src).replace(/\r/g,"");
  const lines=escSrc.split(/\n/); let html=""; let i=0;
  const closeLists=()=>{ if(_ul){html+="</ul>";_ul=false;} if(_ol){html+="</ol>";_ol=false;} if(_blk){html+="</blockquote>";_blk=false;} };
  let _ul=false,_ol=false,_blk=false,_code=false; let codeBuf=[]; let tableBuf=[];
  const isTableRow=ln=>/^\s*\|.*\|\s*$/.test(ln);
  const isSepRow=ln=>{ const body=ln.replace(/^\s*\|/,"").replace(/\|\s*$/,""); const cells=body.split("|").map(c=>c.trim()); return cells.length>0 && cells.every(c=>/^:?-{2,}:?$/.test(c)); };
  const flushTable=()=>{ if(!tableBuf.length) return; const rows=tableBuf.slice(); tableBuf=[];
    if(rows.length>=2 && isSepRow(rows[1])) rows.splice(1,1);
    const splitRow=ln=>ln.replace(/^\s*\|/,"").replace(/\|\s*$/,"").split("|").map(c=>c.trim());
    if(rows.length){ html+="<table><thead><tr>"+splitRow(rows[0]).map(c=>`<th>${inline(c)}</th>`).join("")+"</tr></thead><tbody>";
      for(let k=1; k<rows.length; k++) html+="<tr>"+splitRow(rows[k]).map(c=>`<td>${inline(c)}</td>`).join("")+"</tr>"; html+="</tbody></table>"; } };
  for(;i<lines.length;i++){ let ln=lines[i];
    if(/^```/.test(ln)){ if(_code){ html+="<pre><code>"+codeBuf.join("\n")+"</code></pre>"; codeBuf=[]; _code=false; } else { closeLists(); flushTable(); _code=true; } continue; }
    if(_code){ codeBuf.push(ln); continue; }
    if(isTableRow(ln)){ closeLists(); tableBuf.push(ln); continue; }
    if(tableBuf.length){ flushTable(); }
    if(/^#{1,3}\s/.test(ln)){ closeLists(); const lv=ln.match(/^#+/)[0].length; html+=`<h${lv}>${inline(ln.replace(/^#+\s/,""))}</h${lv}>`; continue; }
    if(/^>\s?/.test(ln)){ if(!_blk){closeLists();html+="<blockquote>";_blk=true;} html+=`<p>${inline(ln.replace(/^>\s?/,""))}</p>`; continue; }
    if(/^\s*[-*]\s/.test(ln)){ if(!_ul){closeLists();html+="<ul>";_ul=true;} html+=`<li>${inline(ln.replace(/^\s*[-*]\s/,""))}</li>`; continue; }
    if(/^\s*\d+\.\s/.test(ln)){ if(!_ol){closeLists();html+="<ol>";_ol=true;} html+=`<li>${inline(ln.replace(/^\s*\d+\.\s/,""))}</li>`; continue; }
    if(/^\s*(---+|\*\*\*+)\s*$/.test(ln)){ closeLists(); html+="<hr>"; continue; }
    if(ln.trim()===""){ closeLists(); continue; }
    closeLists(); html+=`<p>${inline(ln)}</p>`;
  }
  flushTable(); if(_code) html+="<pre><code>"+codeBuf.join("\n")+"</code></pre>"; closeLists(); return html;
  function inline(s){ let out=s; out=out.replace(/\[([^\]\n]+)\]\((https?:\/\/[^)\s]+)\)/g, (m,tx,url)=>`<a href="${url}" target="_blank" rel="noopener noreferrer">${tx}</a>`);
    return out.replace(/\*\*([^*]+)\*\*/g,"<strong>$1</strong>").replace(/\*([^*]+)\*/g,"<em>$1</em>").replace(/`([^`]+)`/g,"<code>$1</code>"); }
}

/* ===================== init ===================== */
function seedSamples(){
  const T=t(); const now=Date.now();
  if(localStorage.getItem(LS.seen)) return;
  state.hist=[
    {q:"FDA 与 CDE 在 MRCT 主方案上的监管要求有何差异？", answer:"两者均接受 master protocol，但 FDA 强调 ICH E6(R3) 的适应性设计事先定型，CDE 偏好阶段性沟通与 Pre-IND 会议明确统计边界。关键差异在盲态与期中分析委员会的独立性要求。", meta:{cached:false,runId:"sample1",skill:"regulatory"}, need_tool:null, params:{}, ts:now-3600e3, sample:true},
    {q:"两组 ORR 30% vs 45%，power 80%，样本量多少？", answer:"按两比例检验（双侧 α=0.05、power 80%）约需每组 95 例，合计 190 例（含 10% 脱落约 211 例）。", meta:{cached:false,runId:"sample2",skill:"samplesize"}, need_tool:"ct-samplesize", params:{test:"proportion_two",p1:0.3,p2:0.45,power:0.8,alpha:0.05}, ts:now-1800e3, sample:true},
    {q:"检索 PD-1 三线 NSCLC 的注册 III 期试验。", answer:"已在知识库中匹配数项；如需完整检索结果请在 WorkBuddy 中运行 ct-registry。", meta:{cached:false,runId:"sample3",skill:"registry"}, need_tool:"ct-registry", params:{cond:"NSCLC",intr:"PD-1",status:"",max:20}, ts:now-600e3, sample:true}
  ];
  saveHist(); localStorage.setItem(LS.seen,"1");
}
// 异步读取 workbench.config.json（端点）+ /api/config（token：前端私有 LLM key，留空则用户在设置框填写）
async function loadRemoteDefaults(){
  try{
    const r=await fetch("workbench.config.json", {cache:"no-store"});
    if(r.ok){ const j=await r.json(); if(j.backend && j.backend.remoteEndpoint) REMOTE_DEFAULT.endpoint=j.backend.remoteEndpoint; }
  }catch(e){ /* file:// 直开无 server，用硬编码默认 */ }
  try{
    const r2=await fetch("/api/config", {cache:"no-store"});
    if(r2.ok){ const j2=await r2.json(); if(j2.token) REMOTE_DEFAULT.token=j2.token; }
  }catch(e){ /* 离线：无 /api/config 时回退空 token（由设置框手动填入） */ }
}
function refreshAll(){
  loadLang();
  computeQid(); // 异步预计算 sha256 设备标识（§8.6），首次提问前就绪；失败由 getQid 同步兜底
  loadRemoteDefaults().then(()=>{
    loadCfg(); loadHist();
    if(SKILLS_LOCKED) document.querySelectorAll('[data-view="skills"]').forEach(n=>n.classList.add("locked"));
    if(state.hist.length===0) seedSamples();
    applyLang(); renderChat(); renderPending(); updateBadge();
    document.getElementById("qinput").addEventListener("input", ()=>{
      const len=document.getElementById("qinput").value.length;
      const sm=document.querySelector(".sendmeta");
      document.getElementById("charHint").textContent = len + " " + t().charHint;
      sm.classList.toggle("warn", len>=800 && len<1500);
      sm.classList.toggle("danger", len>=1500);
    });
    document.getElementById("charHint").textContent="0 "+t().charHint;
    if(window.wbHistory) window.wbHistory.rerender();
  }).catch(e=>{ console.error("refreshAll:", e); });
}
function setConnState(ok, T, reason){
  lastConnOk = ok;
  const pill=document.getElementById("connPill");
  pill.className = "pill " + (ok? "ok":"warn");
  pill.textContent = ok? T.connOk : T.connProxy;
  // 启动指引并入 pill title（仅异常态）；避免与页内横幅双处提醒
  pill.title = ok? "" : ((reason==="external" || reason==="timeout")? T.bannerExternal : (T.bannerWarn + " run_app.bat"));
}
function isHttpOrigin(){ const p=(location.protocol||"").toLowerCase(); return p==="http:" || p==="https:"; }
async function checkProxy(){
  const T=t();
  if(!isHttpOrigin()){ setConnState(false, T, "external"); return; }
  const ctrl=new AbortController(); const timer=setTimeout(()=>ctrl.abort(), 4000);
  try{
    const url = new URL("/api/health", location.origin).href;
    const r=await fetch(url, {cache:"no-store", signal:ctrl.signal}); clearTimeout(timer);
    if(r.ok) setConnState(true, T, "ok"); else throw new Error("http "+r.status);
  }catch(e){ clearTimeout(timer); const aborted=!!(e && e.name==="AbortError"); setConnState(false, T, aborted? "timeout":"err"); }
}
// 冒烟自检（铁律 10）：挂载点 / 视图 / 组件存在性
function smokeCheck(){
  const issues=[];
  ["wb-hist-list","view-console","view-skills","view-history","qinput","sendBtn","wb-lang"].forEach(id=>{ if(!document.getElementById(id)) issues.push("缺失 #"+id); });
  if(typeof WBList==="undefined") issues.push("WBList 未加载（wb-list.js 缺失？）");
  if(issues.length) console.warn("[ct-advisor smoke] "+issues.join("；"));
  return issues;
}
/* 恢复侧栏折叠状态（本地记忆） */
(function(){ try{ if(localStorage.getItem(LS.side)==="1"){ const a=document.querySelector(".app"); if(a) a.classList.add("side-collapsed"); } }catch(e){} })();
window.addEventListener("DOMContentLoaded", ()=>{
  // #q= 跨工作台转接预填（2026-10-20，C 方案）：ct-samplesize 咨询闸门把样本量/效力相关
  // 的概念型问题转接过来。只预填 #qinput、聚焦，绝不自动发送（保持人工确认 HITL）；
  // 预填后清掉 hash，避免刷新重复回填。用 hash 而非 query：问题文本不入服务器日志。
  try{
    const _m=location.hash.match(/^#q=(.+)$/);
    if(_m){
      const _q=decodeURIComponent(_m[1]);
      const _el=document.getElementById("qinput");
      if(_el && _q && !_el.value){ _el.value=_q; _el.focus(); }
      history.replaceState(null,"",location.pathname+location.search);
    }
  }catch(e){}
  try{ refreshAll(); }catch(e){ console.error("refreshAll:", e); } try{ checkProxy(); }catch(e){ console.error("checkProxy:", e); } try{ smokeCheck(); }catch(e){} });
