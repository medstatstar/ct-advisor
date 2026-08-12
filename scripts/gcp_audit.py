#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gcp_audit.py — GCP 13 原则合规检查报告生成器

读取 knowledge/ref-gcp-13-principles.md 中的检查点，
根据用户输入的 study_type/scope 生成合规检查报告。

Usage:
  python scripts/gcp_audit.py --study_type oncology --scope phase3 --format json
  python scripts/gcp_audit.py --study_type all --scope full --format ascii
"""

import argparse
import json
import os
import sys
from typing import Dict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KNOWLEDGE_DIR = os.path.join(ROOT, "knowledge")

# GCP 13 原则检查点（内联，避免运行时解析 markdown）
GCP_PRINCIPLES = [
    {
        "id": "P1",
        "name": "伦理原则",
        "checkpoints": [
            "伦理委员会批件是否在有效期内",
            "知情同意书是否经伦理批准",
            "受试者补偿是否合理",
        ],
        "common_violations": ["伦理过期未续", "知情同意未经伦理审批", "补偿过高诱导"],
        "phase": "启动/进行中",
    },
    {
        "id": "P2",
        "name": "风险-受益比",
        "checkpoints": [
            "是否有独立的风险评估报告",
            "风险控制措施是否落实",
            "预期受益是否有依据",
        ],
        "common_violations": ["风险评估流于形式", "风险控制措施未执行", "受益夸大"],
        "phase": "方案设计/进行中",
    },
    {
        "id": "P3",
        "name": "受试者保护",
        "checkpoints": [
            "数据脱敏方案是否到位",
            "生物样本管理是否合规",
            "数据跨境是否合规",
        ],
        "common_violations": ["脱敏不彻底", "样本管理混乱", "数据出境未审批"],
        "phase": "全程",
    },
    {
        "id": "P4",
        "name": "方案科学性",
        "checkpoints": [
            "临床前数据是否充分",
            "剂量选择是否有依据",
            "终点指标是否合理",
        ],
        "common_violations": ["临床前数据不足", "剂量爬坡设计不合理", "终点未经验证"],
        "phase": "方案设计",
    },
    {
        "id": "P5",
        "name": "合规性",
        "checkpoints": [
            "IND/临床试验通知书是否在有效期内",
            "方案变更是否报批",
            "安全性报告是否及时",
        ],
        "common_violations": ["批件过期", "重大变更未报", "SUSAR 报告延迟"],
        "phase": "启动/进行中",
    },
    {
        "id": "P6",
        "name": "研究者资质",
        "checkpoints": [
            "PI 执业范围是否覆盖",
            "GCP 培训是否在有效期内",
            "是否有足够的时间投入",
        ],
        "common_violations": ["执业证过期", "GCP 培训超期", "PI 精力不足"],
        "phase": "启动前",
    },
    {
        "id": "P7",
        "name": "数据完整性",
        "checkpoints": [
            "原始数据与 CRF 是否一致",
            "数据修改是否留痕",
            "电子数据是否有审计追踪",
        ],
        "common_violations": ["数据不一致", "修改无痕迹", "无审计追踪"],
        "phase": "进行中/锁库",
    },
    {
        "id": "P8",
        "name": "知情同意",
        "checkpoints": [
            "知情同意过程是否规范",
            "受试者是否有足够时间考虑",
            "弱势群体是否有额外保护",
        ],
        "common_violations": ["知情同意走过场", "时间不足", "弱势群体保护不足"],
        "phase": "入组前",
    },
    {
        "id": "P9",
        "name": "药品管理",
        "checkpoints": [
            "药品储存条件是否达标",
            "药品发放记录是否完整",
            "药品回收是否合规",
        ],
        "common_violations": ["温湿度超标", "记录缺失", "回收不规范"],
        "phase": "进行中",
    },
    {
        "id": "P10",
        "name": "安全性报告",
        "checkpoints": [
            "SUSAR 是否 7/15 天内报告",
            "DSMB 是否按计划召开",
            "SAE 是否及时记录",
        ],
        "common_violations": ["报告超时", "DSMB 未开", "SAE 漏报"],
        "phase": "进行中",
    },
    {
        "id": "P11",
        "name": "监查",
        "checkpoints": [
            "监查计划是否执行",
            "监查发现是否整改",
            "监查报告是否归档",
        ],
        "common_violations": ["监查频率不足", "问题未整改", "报告缺失"],
        "phase": "进行中",
    },
    {
        "id": "P12",
        "name": "统计分析",
        "checkpoints": [
            "SAP 是否锁库前定稿",
            "是否控制 I 类错误",
            "缺失数据处理是否预先规定",
        ],
        "common_violations": ["SAP 滞后", "多重性未控制", "缺失数据方案缺失"],
        "phase": "分析阶段",
    },
    {
        "id": "P13",
        "name": "数据保留",
        "checkpoints": [
            "保存期限是否符合要求（至少 5 年）",
            "数据是否可检索",
            "销毁是否有记录",
        ],
        "common_violations": ["保存期不足", "数据无法检索", "销毁无记录"],
        "phase": "结束后",
    },
]

# NMPA 特殊要求
NMPA_REQUIREMENTS = [
    {
        "id": "NMPA-1",
        "name": "临床试验登记",
        "check": "是否在 CDE 临床试验登记平台完成登记",
        "reference": "《药物临床试验登记与信息公示管理规范》",
    },
    {
        "id": "NMPA-2",
        "name": "基因资源审批",
        "check": "涉及人类遗传资源的是否获得科技部审批",
        "reference": "《人类遗传资源管理条例》",
    },
    {
        "id": "NMPA-3",
        "name": "数据出境",
        "check": "临床试验数据出境是否通过安全评估",
        "reference": "《数据出境安全评估办法》",
    },
    {
        "id": "NMPA-4",
        "name": "儿童试验",
        "check": "儿童受试者是否有额外保护措施",
        "reference": "NMPA《儿科人群药物临床试验技术指导原则》",
    },
]


def generate_audit_report(study_type: str = "all", scope: str = "full") -> Dict:
    """生成 GCP 合规检查报告。
    
    参数：
        study_type: 试验类型（oncology/cardio/all 等）
        scope: 检查范围（phase1-3/full/startup/ongoing/closure）
    
    返回：
        dict 含检查项列表、汇总统计、建议
    """
    # 根据 scope 筛选适用阶段
    scope_phase_map = {
        "startup": ["启动前", "启动/进行中"],
        "ongoing": ["进行中", "进行中/锁库", "全程"],
        "closure": ["结束后", "分析阶段"],
        "full": [],  # 全部
    }
    
    applicable_phases = scope_phase_map.get(scope, [])
    
    items = []
    for p in GCP_PRINCIPLES:
        if applicable_phases and p["phase"] not in applicable_phases:
            continue
        
        items.append({
            "principle_id": p["id"],
            "principle_name": p["name"],
            "phase": p["phase"],
            "checkpoints": p["checkpoints"],
            "common_violations": p["common_violations"],
            "status": "pending",  # 待用户确认
        })
    
    # NMPA 特殊要求（scope=full 或 startup/ongoing 时包含）
    nmpa_items = []
    if scope in ("full", "startup", "ongoing"):
        for r in NMPA_REQUIREMENTS:
            nmpa_items.append({
                "requirement_id": r["id"],
                "name": r["name"],
                "check": r["check"],
                "reference": r["reference"],
                "status": "pending",
            })
    
    report = {
        "study_type": study_type,
        "scope": scope,
        "total_principles": len(items),
        "total_nmpa": len(nmpa_items),
        "items": items,
        "nmpa_requirements": nmpa_items,
        "summary": {
            "critical": 0,
            "major": 0,
            "minor": 0,
            "compliant": 0,
            "pending": len(items) + len(nmpa_items),
        },
    }
    
    return report


def format_ascii(report: Dict) -> str:
    """格式化为 ASCII 表格。"""
    lines = []
    lines.append("=" * 70)
    lines.append("GCP 13 原则合规检查报告")
    lines.append(f"试验类型: {report['study_type']} | 范围: {report['scope']}")
    lines.append("=" * 70)
    lines.append("")
    
    for item in report["items"]:
        lines.append(f"[{item['principle_id']}] {item['principle_name']} ({item['phase']})")
        for cp in item["checkpoints"]:
            lines.append(f"  □ {cp}")
        lines.append(f"  常见违规: {', '.join(item['common_violations'])}")
        lines.append("")
    
    if report["nmpa_requirements"]:
        lines.append("-" * 70)
        lines.append("NMPA 特殊要求")
        lines.append("-" * 70)
        for r in report["nmpa_requirements"]:
            lines.append(f"[{r['requirement_id']}] {r['name']}")
            lines.append(f"  □ {r['check']}")
            lines.append(f"  依据: {r['reference']}")
            lines.append("")
    
    lines.append("=" * 70)
    lines.append(f"总计: {report['total_principles']} 项 GCP 原则 + {report['total_nmpa']} 项 NMPA 要求")
    lines.append("状态: 待确认 (pending) — 请逐项核实后更新状态")
    lines.append("=" * 70)
    
    return "\n".join(lines)


def main():
    p = argparse.ArgumentParser(description="GCP 13 原则合规检查报告")
    p.add_argument("--study_type", default="all", help="试验类型")
    p.add_argument("--scope", default="full",
                   choices=["full", "startup", "ongoing", "closure"],
                   help="检查范围")
    p.add_argument("--format", choices=["json", "ascii"], default="ascii",
                   help="输出格式")
    p.add_argument("--output", type=str, default=None, help="输出文件路径")
    
    args = p.parse_args()
    
    report = generate_audit_report(args.study_type, args.scope)
    
    if args.format == "json":
        out = json.dumps(report, ensure_ascii=False, indent=2)
    else:
        out = format_ascii(report)
    
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out)
        print(f"已写入: {args.output}")
    else:
        print(out)


if __name__ == "__main__":
    main()
