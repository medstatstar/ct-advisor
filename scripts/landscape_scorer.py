#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
landscape_scorer.py — 竞品格局量化评分

计算三个维度评分（0-100）：
1. phase_lead_score（阶段领先度）— 与竞品相比所处临床阶段的领先程度
2. pipeline_overlap_score（管线重叠度）— 与竞品在适应症/靶点上的重叠程度
3. enrollment_speed_score（入组速度）— 相对于同类试验的入组效率

数据来源：ct-registry（临床试验注册数据）+ 可选手动输入
纯本地计算，零联网。

Usage:
  python scripts/landscape_scorer.py --drug "osimertinib" --indication "NSCLC" --format json
  python scripts/landscape_scorer.py --drug "osimertinib" --indication "NSCLC" --compare_drugs "gefitinib,erlotinib" --format ascii
"""

import argparse
import json
import math
import os
import sys
from typing import Dict, List, Optional

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


# 临床阶段权重映射（数值越大越靠前）
PHASE_WEIGHT = {
    "phase1": 10,
    "phase1/2": 20,
    "phase2": 30,
    "phase2/3": 40,
    "phase3": 50,
    "phase4": 60,
    "approved": 80,
    "marketed": 100,
    "withdrawn": 70,
    "terminated": 0,
    "unknown": 0,
}

# 默认模拟数据（当无法从 ct-registry 获取数据时使用）
DEFAULT_BENCHMARKS = {
    "NSCLC": {
        "avg_enrollment_months": 24,
        "avg_sample_size": 400,
        "competitors": [
            {"drug": "gefitinib", "phase": "approved", "start_year": 2003, "sample_size": 1218},
            {"drug": "erlotinib", "phase": "approved", "start_year": 2004, "sample_size": 1172},
            {"drug": "afatinib", "phase": "approved", "start_year": 2013, "sample_size": 1158},
            {"drug": "dacomitinib", "phase": "approved", "start_year": 2018, "sample_size": 920},
            {"drug": "alectinib", "phase": "approved", "start_year": 2017, "sample_size": 437},
        ],
    },
    "breast_cancer": {
        "avg_enrollment_months": 30,
        "avg_sample_size": 600,
        "competitors": [
            {"drug": "trastuzumab", "phase": "approved", "start_year": 2001, "sample_size": 1850},
            {"drug": "pertuzumab", "phase": "approved", "start_year": 2012, "sample_size": 1540},
            {"drug": "palbociclib", "phase": "approved", "start_year": 2015, "sample_size": 910},
        ],
    },
    "default": {
        "avg_enrollment_months": 24,
        "avg_sample_size": 400,
        "competitors": [],
    },
}


def compute_phase_lead_score(drug: str, indication: str,
                             own_phase: str = "phase2",
                             competitors: Optional[List[Dict]] = None) -> Dict:
    """计算阶段领先度（0-100）。
    
    基于自身阶段与竞品阶段比较：
    - 若竞品全部已上市，自身阶段为 phase2 → 得分较低（~30）
    - 若竞品处于相同阶段 → 中等（~50）
    - 若自身领先竞品 → 较高（~80）
    """
    own_weight = PHASE_WEIGHT.get(own_phase.lower(), 0)
    
    if not competitors:
        competitors = []
    
    if not competitors:
        return {
            "score": 50,
            "detail": "无竞品数据，默认中等评分",
            "own_phase": own_phase,
            "competitor_phases": [],
        }
    
    comp_weights = [PHASE_WEIGHT.get(c.get("phase", "unknown").lower(), 0) for c in competitors]
    max_comp = max(comp_weights) if comp_weights else 0
    avg_comp = sum(comp_weights) / len(comp_weights) if comp_weights else 0
    
    # 领先度 = 自身权重 - 竞品最高权重
    lead = own_weight - max_comp
    
    # 映射到 0-100
    if lead >= 20:
        score = 90  # 大幅领先
    elif lead >= 10:
        score = 75
    elif lead >= 0:
        score = 60
    elif lead >= -10:
        score = 45
    elif lead >= -20:
        score = 30
    else:
        score = 15
    
    # 微调：若竞品均值远低于自身，加分
    if own_weight > avg_comp + 10:
        score = min(100, score + 10)
    
    return {
        "score": score,
        "detail": f"自身阶段权重={own_weight}，竞品最高={max_comp}，均值={avg_comp:.1f}",
        "own_phase": own_phase,
        "competitor_phases": list(set(c.get("phase", "") for c in competitors)),
    }


def compute_pipeline_overlap_score(drug: str, indication: str,
                                   own_target: str = "",
                                   competitors: Optional[List[Dict]] = None) -> Dict:
    """计算管线重叠度（0-100）。
    
    高重叠 = 红海市场（得分高说明竞争激烈）
    低重叠 = 蓝海（得分低说明差异化优势）
    """
    if not competitors:
        competitors = []
    
    if not competitors:
        return {
            "score": 0,
            "detail": "无竞品数据，无重叠",
            "n_competitors": 0,
        }
    
    n_comp = len(competitors)
    
    # 重叠度 = 竞品数量 × 阶段系数
    # 已有上市产品的竞品权重更高
    overlap_count = 0
    for c in competitors:
        phase = c.get("phase", "unknown")
        if phase in ("approved", "marketed"):
            overlap_count += 3  # 上市竞品权重 3x
        elif phase in ("phase3", "phase2/3"):
            overlap_count += 2
        elif phase in ("phase2", "phase1/2"):
            overlap_count += 1
        # phase1 及以下不计入重叠
    
    # 映射到 0-100（经验值）
    if overlap_count >= 15:
        score = 95  # 极度红海
    elif overlap_count >= 10:
        score = 80
    elif overlap_count >= 6:
        score = 60
    elif overlap_count >= 3:
        score = 40
    elif overlap_count >= 1:
        score = 20
    else:
        score = 5
    
    return {
        "score": score,
        "detail": f"加权重叠计数={overlap_count}（{n_comp} 个竞品，上市权重3x/后期2x/早期1x）",
        "n_competitors": n_comp,
        "overlap_level": "高" if score >= 60 else ("中" if score >= 30 else "低"),
    }


def compute_enrollment_speed_score(enrollment_months: Optional[int] = None,
                                   sample_size: Optional[int] = None,
                                   indication: str = "default") -> Dict:
    """计算入组速度评分（0-100）。
    
    同类试验平均入组周期 vs 自身入组周期。
    越快得分越高。
    """
    bench = DEFAULT_BENCHMARKS.get(indication, DEFAULT_BENCHMARKS["default"])
    avg_months = bench["avg_enrollment_months"]
    avg_size = bench["avg_sample_size"]
    
    if enrollment_months is None or enrollment_months <= 0:
        return {
            "score": 50,
            "detail": f"未提供入组周期数据，默认中等（同类平均 {avg_months} 个月）",
            "enrollment_months": None,
            "avg_months_reference": avg_months,
        }
    
    # 月度入组速度比
    speed_ratio = avg_months / enrollment_months  # >1 表示比平均快
    
    if speed_ratio >= 2.0:
        score = 100  # 远超平均
    elif speed_ratio >= 1.5:
        score = 85
    elif speed_ratio >= 1.2:
        score = 70
    elif speed_ratio >= 0.9:
        score = 55
    elif speed_ratio >= 0.7:
        score = 40
    else:
        score = 20
    
    return {
        "score": score,
        "detail": f"入组周期 {enrollment_months} 月 vs 同类平均 {avg_months} 月（速度比 {speed_ratio:.2f}）",
        "enrollment_months": enrollment_months,
        "avg_months_reference": avg_months,
    }


def compute_composite_score(phase_score: int, overlap_score: int,
                            enrollment_score: int,
                            weights: Optional[List[float]] = None) -> Dict:
    """计算综合评分。
    
    默认权重：阶段领先度 40% + 管线重叠度反向 30% + 入组速度 30%
    注意：overlap 越高越不好，所以反向处理（100 - overlap）
    """
    if weights is None:
        weights = [0.4, 0.3, 0.3]
    
    w_phase, w_overlap, w_enroll = weights
    
    # overlap 反向（低重叠 = 差异化优势 = 高分）
    overlap_inverse = 100 - overlap_score
    
    composite = (
        w_phase * phase_score +
        w_overlap * overlap_inverse +
        w_enroll * enrollment_score
    )
    
    # 映射等级
    if composite >= 80:
        grade = "A"
        grade_zh = "优秀"
    elif composite >= 65:
        grade = "B"
        grade_zh = "良好"
    elif composite >= 50:
        grade = "C"
        grade_zh = "中等"
    elif composite >= 35:
        grade = "D"
        grade_zh = "偏弱"
    else:
        grade = "E"
        grade_zh = "较弱"
    
    return {
        "composite_score": round(composite, 1),
        "grade": grade,
        "grade_zh": grade_zh,
        "weights": {
            "phase_lead": weights[0],
            "pipeline_uniqueness": weights[1],
            "enrollment_speed": weights[2],
        },
        "components": {
            "phase_lead_score": phase_score,
            "pipeline_uniqueness_score": overlap_inverse,
            "enrollment_speed_score": enrollment_score,
        },
    }


def full_analysis(drug: str, indication: str,
                  own_phase: str = "phase2",
                  compare_drugs: Optional[List[str]] = None,
                  enrollment_months: Optional[int] = None,
                  sample_size: Optional[int] = None) -> Dict:
    """执行完整竞品格局分析。"""
    # 获取竞品数据（从 benchmark 或 ct-registry）
    bench = DEFAULT_BENCHMARKS.get(indication, DEFAULT_BENCHMARKS["default"])
    competitors = bench.get("competitors", [])
    
    # 如果指定了 compare_drugs，过滤或添加
    if compare_drugs:
        specified = []
        for d in compare_drugs:
            found = [c for c in competitors if c["drug"].lower() == d.lower()]
            if found:
                specified.append(found[0])
            else:
                specified.append({"drug": d, "phase": "unknown", "start_year": None, "sample_size": None})
        competitors = specified
    
    # 计算各维度评分
    phase_result = compute_phase_lead_score(drug, indication, own_phase, competitors)
    overlap_result = compute_pipeline_overlap_score(drug, indication, "", competitors)
    enroll_result = compute_enrollment_speed_score(enrollment_months, sample_size, indication)
    
    composite = compute_composite_score(
        phase_result["score"],
        overlap_result["score"],
        enroll_result["score"],
    )
    
    return {
        "drug": drug,
        "indication": indication,
        "own_phase": own_phase,
        "competitors": competitors,
        "phase_lead": phase_result,
        "pipeline_overlap": overlap_result,
        "enrollment_speed": enroll_result,
        "composite": composite,
    }


def format_ascii(result: Dict) -> str:
    """格式化为 ASCII 表格。"""
    lines = []
    lines.append("=" * 70)
    lines.append(f"竞品格局量化评分: {result['drug']} / {result['indication']}")
    lines.append("=" * 70)
    lines.append("")
    
    # 各维度
    lines.append(f"阶段领先度:  {result['phase_lead']['score']:>3}/100  — {result['phase_lead']['detail']}")
    lines.append(f"管线重叠度:  {result['pipeline_overlap']['score']:>3}/100  — {result['pipeline_overlap']['detail']}")
    lines.append(f"入组速度:    {result['enrollment_speed']['score']:>3}/100  — {result['enrollment_speed']['detail']}")
    lines.append("")
    lines.append("-" * 70)
    comp = result["composite"]
    lines.append(f"综合评分: {comp['composite_score']}/100  等级: {comp['grade']} ({comp['grade_zh']})")
    lines.append(f"权重: 阶段领先 {comp['weights']['phase_lead']*100:.0f}% + "
                 f"管线差异化 {comp['weights']['pipeline_uniqueness']*100:.0f}% + "
                 f"入组速度 {comp['weights']['enrollment_speed']*100:.0f}%")
    lines.append("")
    
    # 竞品列表
    if result["competitors"]:
        lines.append("竞品列表:")
        for c in result["competitors"]:
            lines.append(f"  - {c['drug']:<20} 阶段: {c.get('phase', 'unknown'):<10} 启动: {c.get('start_year', '-')}")
    lines.append("=" * 70)
    
    return "\n".join(lines)


def main():
    p = argparse.ArgumentParser(description="竞品格局量化评分")
    p.add_argument("--drug", required=True, help="药物名")
    p.add_argument("--indication", required=True, help="适应症")
    p.add_argument("--own_phase", default="phase2", help="自身临床阶段")
    p.add_argument("--compare_drugs", type=str, default=None,
                   help="竞品列表逗号分隔（如 'gefitinib,erlotinib'）")
    p.add_argument("--enrollment_months", type=int, default=None,
                   help="实际入组周期（月）")
    p.add_argument("--sample_size", type=int, default=None,
                   help="目标样本量")
    p.add_argument("--format", choices=["json", "ascii"], default="ascii")
    p.add_argument("--output", type=str, default=None)
    
    args = p.parse_args()
    
    compare_drugs = None
    if args.compare_drugs:
        compare_drugs = [d.strip() for d in args.compare_drugs.split(",")]
    
    result = full_analysis(
        drug=args.drug,
        indication=args.indication,
        own_phase=args.own_phase,
        compare_drugs=compare_drugs,
        enrollment_months=args.enrollment_months,
        sample_size=args.sample_size,
    )
    
    if args.format == "json":
        out = json.dumps(result, ensure_ascii=False, indent=2)
    else:
        out = format_ascii(result)
    
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out)
        print(f"已写入: {args.output}")
    else:
        print(out)


if __name__ == "__main__":
    main()
