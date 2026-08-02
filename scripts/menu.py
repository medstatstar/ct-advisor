#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
menu.py -- builder for the ct-advisor clarification menu (gate 0 → decidable).

Loads the machine-readable tree in `scripts/menu.json` and resolves every
user-facing label through `scripts/i18n.py` (the bilingual single source of
truth). It produces the option structures consumed by:

  - adapters/backend.py (Coze) when rendering clarification cards;
  - a local preview / tests (``python3 scripts/menu.py --all``).

In LOCAL mode the methodology agent reads `scripts/menu.json` +
`knowledge/prompts.md` directly and calls the AskUserQuestion tool; this module
is the programmatic twin so Coze and local stay consistent. The agent does NOT
need to execute this file.

Rendering model (mirrors AskUserQuestion / Coze card constraints):
  - type "multi"   -> up to 4 questions in ONE call (Tier 0)
  - type "single"  -> one question, a flat option list (<=4)
  - type "branch"  -> options depend on the PREVIOUS choice (branches map)

Usage:
  python3 scripts/menu.py --tier ground
  python3 scripts/menu.py --tier intent_workflow --choice design_stats
  python3 scripts/menu.py --tier subintent --choice B
  python3 scripts/menu.py --all            # dump every tier as JSON
  python3 scripts/menu.py --all --lang zh  # force Chinese
"""

import json
import sys
from pathlib import Path

# Make sibling scripts importable (i18n.py lives next to this file).
_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

from i18n import t, set_lang  # noqa: E402

MENU_PATH = _HERE / "menu.json"


def load_menu():
    """Load scripts/menu.json via the stdlib json module (no third-party deps)."""
    return json.load(open(MENU_PATH, encoding="utf-8"))


def _option_obj(opt, choices=None, skill_routes=None):
    """Resolve one option dict into {value, label, description?}."""
    value = opt["id"]
    label_key = opt.get("label_key")
    label = t(label_key) if label_key else value
    obj = {"value": value, "label": label}
    # Surface the workflow route (if any) as a hint in Coze cards.
    if "workflows" in opt:
        obj["workflows"] = opt["workflows"]
    # Surface the sibling data-skill route (capability = data_intel) as a hint.
    trig = opt.get("trigger_skill")
    if trig is None and skill_routes and value in skill_routes:
        trig = skill_routes[value]
    if trig:
        obj["trigger_skill"] = trig
    return obj


def render_tier(tier, choices=None, skill_routes=None):
    """Return a dict describing how to render one tier.

    Args:
        tier: a tier dict from menu.json
        choices: dict {tier_id: selected_option_id} for branch tiers

    Returns:
        For type "multi":  {"type": "multi", "title": ..., "questions": [...]}
        For type "single"/"branch": {"type": ..., "title": ..., "question": ...,
                                      "header": ..., "options": [...]}
    """
    title = t(tier["title_key"]) if tier.get("title_key") else ""
    ttype = tier.get("type", "single")

    if ttype == "multi":
        questions = []
        for q in tier.get("questions", []):
            questions.append({
                "header": q.get("header", ""),
                "question": t(q["q_key"]),
                "options": [_option_obj(o, skill_routes=skill_routes) for o in q["options"]],
            })
        return {"type": "multi", "title": title, "questions": questions}

    # single / branch -> one question
    question = t(tier["q_key"]) if tier.get("q_key") else ""
    header = tier.get("header", "")

    if ttype == "branch":
        branch_key = None
        # find which branch this tier follows from the previous choice
        if choices:
            # a branch tier names its controlling tier-id implicitly via position;
            # we accept an explicit `depends_on` or fall back to last choice value
            depends_on = tier.get("depends_on")
            if depends_on and depends_on in choices:
                branch_key = choices[depends_on]
            elif choices:
                # use the most recent choice as the branch key
                branch_key = list(choices.values())[-1]
        ids = tier.get("branches", {}).get(branch_key, [])
        # resolve labels: intent_workflow -> menu.<W>; subintent -> menu.sub.<W>.<opt>
        options = []
        for wid in ids:
            if tier["id"] == "intent_workflow":
                label = t("menu." + wid)
                options.append({"value": wid, "label": label})
            else:  # subintent
                label = t("menu.sub.{}.{}".format(branch_key, wid))
                options.append({"value": wid, "label": label})
        options.append({"value": "explain_diff", "label": t("menu.explain_diff"),
                         "is_explain_diff": True})
        return {
            "type": "branch", "title": title, "question": question,
            "header": header, "branch_key": branch_key, "options": options,
        }

    # plain single
    options = [_option_obj(o, skill_routes=skill_routes) for o in tier.get("options", [])]
    options.append({"value": "explain_diff", "label": t("menu.explain_diff"),
                    "is_explain_diff": True})
    return {
        "type": "single", "title": title, "question": question,
        "header": header, "options": options,
    }


def render_all():
    """Render every tier grouped by entry flow (methodology / data_intel).

    Each flow lists its tiers in order (see `flows:` in menu.json). Branch tiers
    are expanded across all branches for preview; single/multi tiers render once.
    `skill_routes` is threaded through so data_skill options carry `trigger_skill`.
    """
    menu = load_menu()
    flows = menu.get("flows", {})
    skill_routes = menu.get("skill_routes", {})
    out = {}
    for flow_name, tier_ids in flows.items():
        flow_out = {}
        for tid in tier_ids:
            tier = next((t for t in menu["tiers"] if t["id"] == tid), None)
            if tier is None:
                continue
            ttype = tier.get("type")
            if ttype == "branch":
                branch_map = tier.get("branches", {})
                for bk in branch_map:
                    chain = {tier.get("depends_on", tid): bk}
                    flow_out.setdefault(tid, {})[bk] = render_tier(tier, chain, skill_routes)
            else:
                flow_out[tid] = render_tier(tier, {}, skill_routes)
        out[flow_name] = flow_out
    return out


def _opt_extra(o):
    bits = []
    if o.get("workflows"):
        bits.append("workflows " + str(o["workflows"]))
    if o.get("trigger_skill"):
        bits.append("-> " + o["trigger_skill"])
    return "  " + "  ".join(bits) if bits else ""


def _print_human(d, indent=0):
    pad = "  " * indent
    if "questions" in d:  # multi
        print(pad + "[multi] " + d.get("title", ""))
        for q in d["questions"]:
            print(pad + "  • " + q["question"])
            for o in q["options"]:
                print(pad + "      - " + o["label"] + _opt_extra(o))
    else:
        print(pad + "[%s] %s" % (d.get("type"), d.get("title", "")))
        if d.get("question"):
            print(pad + "  " + d["question"])
        for o in d.get("options", []):
            print(pad + "    - " + o["label"] + _opt_extra(o))


def main(argv=None):
    import argparse
    p = argparse.ArgumentParser(description="ct-advisor clarification menu builder")
    p.add_argument("--tier", help="render one tier id (e.g. ground, intent_workflow, subintent, output)")
    p.add_argument("--choice", help="selected option id for a branch tier (drives branch resolution)")
    p.add_argument("--all", action="store_true", help="dump all tiers as JSON")
    p.add_argument("--lang", choices=["en", "zh"], help="force language (default: auto-detect)")
    p.add_argument("--human", action="store_true", help="human-readable print instead of JSON")
    args = p.parse_args(argv)

    if args.lang:
        set_lang(args.lang)

    menu = load_menu()

    if args.all:
        data = render_all()
        if args.human:
            for flow_name, tiers in data.items():
                print("== flow: {} ==".format(flow_name))
                for tid, d in tiers.items():
                    if isinstance(d, dict) and ("questions" in d or "options" in d):
                        _print_human(d, indent=1)
                    else:  # branch dict keyed by branch_key
                        for bk, bd in d.items():
                            print("  # branch '{}'".format(bk))
                            _print_human(bd, indent=2)
            return
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return

    if args.tier:
        tier = next((t for t in menu["tiers"] if t["id"] == args.tier), None)
        if tier is None:
            raise SystemExit("unknown tier: %s" % args.tier)
        choices = {tier.get("depends_on", args.tier): args.choice} if args.choice else None
        rendered = render_tier(tier, choices)
        if args.human:
            _print_human(rendered)
        else:
            print(json.dumps(rendered, ensure_ascii=False, indent=2))
        return

    # default: list tier ids
    print("Available tiers:")
    for t in menu["tiers"]:
        print("  - %s (%s)" % (t["id"], t.get("type")))


if __name__ == "__main__":
    main()
