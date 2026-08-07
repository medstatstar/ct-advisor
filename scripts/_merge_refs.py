import os, re, shutil, glob

BASE = r"C:/Users/WintoneFileSrv/.workbuddy/skills/ct-advisor"
KNOWLEDGE = os.path.join(BASE, "knowledge")
NEW = os.path.join(BASE, "knowledge_new")
os.makedirs(NEW, exist_ok=True)

# target_file: [ordered source files to merge]
GROUPS = {
    "ref-ops-design.md":      ["ref-ops-design.md", "ref-ops-pharmacology.md", "ref-clinical-operations.md"],
    "ref-ops-gcp-site.md":    ["ref-ops-gcp-roles.md", "ref-ops-site.md"],
    "ref-ops-execution.md":   ["ref-ops-execution.md", "ref-ops-methodology-qc.md"],
    "ref-ops-data.md":        ["ref-ops-data.md", "ref-ops-data-systems.md"],
    "ref-ops-safety.md":      ["ref-ops-safety.md", "ref-ops-qa.md", "ref-ops-governance.md"],
    "ref-reg-stats.md":       ["ref-reg-stats.md", "ref-regulatory-statistical.md"],
    "ref-reg-submission.md":  ["ref-reg-csr.md", "ref-reg-ctd.md", "ref-reg-approval.md",
                               "ref-reg-design-endpoints.md", "ref-reg-methods-products.md"],
    "ref-reg-cn.md":          ["ref-reg-cn-routing.md", "ref-reg-cn-data-ethics.md", "ref-reg-cn-transparency.md"],
}


def parse(text):
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    fm_raw = parts[1] if len(parts) > 1 else ""
    body = parts[2] if len(parts) > 2 else ""
    fm = {}
    for line in fm_raw.splitlines():
        m = re.match(r"\s*([a-zA-Z_]+):\s*(.*)", line)
        if m:
            fm[m.group(1)] = m.group(2).strip()
    return fm, body


# every file that participates in a group (targets + sources) must NOT be copied as-is
all_group = set(GROUPS.keys())
for _srcs in GROUPS.values():
    all_group.update(_srcs)
written = []

for target, sources in GROUPS.items():
    topics_all, wf_all, chunks = [], set(), []
    for s in sources:
        p = os.path.join(KNOWLEDGE, s)
        text = open(p, encoding="utf-8").read()
        fm, body = parse(text)
        if "superseded" in fm.get("status", ""):
            continue  # placeholder, skip body
        lines = body.splitlines()
        lines = [l for l in lines if not l.startswith("> 本文件为")]
        while lines and lines[0].strip() == "":
            lines.pop(0)
        while lines and lines[-1].strip() == "":
            lines.pop()
        chunk = "\n".join(lines).strip()
        if chunk:
            chunks.append("<!-- === merged: %s === -->\n%s" % (s, chunk))
        if fm.get("topics"):
            topics_all.append(fm["topics"])
        if fm.get("serves_workflows"):
            wf_all.update(re.findall(r"[A-Z]", fm["serves_workflows"]))
    topics = "；".join(topics_all)
    wf = "[" + ", ".join(sorted(wf_all)) + "]"
    header = "---\nfile: %s\nversion: 2026-08-05\ntopics: %s\nserves_workflows: %s\n---\n" % (target, topics, wf)
    content = header + "\n" + "\n\n".join(chunks) + "\n"
    out = os.path.join(NEW, target)
    open(out, "w", encoding="utf-8").write(content)
    written.append((target, len(content.encode("utf-8"))))

# copy non-merged ref-*.md (kept as-is)
for p in sorted(glob.glob(os.path.join(KNOWLEDGE, "ref-*.md"))):
    name = os.path.basename(p)
    if name in all_group:
        continue
    shutil.copy2(p, os.path.join(NEW, name))
    written.append((name + " (copied)", os.path.getsize(p)))

# copy misc non-ref files
for name in ["prompts.md", "system_prompt.md", "survey_external_projects.md", "reference-index.md"]:
    src = os.path.join(KNOWLEDGE, name)
    if os.path.exists(src):
        shutil.copy2(src, os.path.join(NEW, name))

print("=== merged/copied into knowledge_new/ ===")
for n, sz in written:
    print("  %-34s %7d bytes" % (n, sz))
print("\nTotal files in knowledge_new/: %d" % len(os.listdir(NEW)))
