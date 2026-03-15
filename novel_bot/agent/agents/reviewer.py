import re
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger

from novel_bot.agent.agents.base import SubAgent, AgentResponse
from novel_bot.agent.agents import AgentRole


class ReviewVerdict(Enum):
    PASS = "通过"
    NEEDS_REVISION = "需修改"
    NEEDS_REWRITE = "需重写"


@dataclass
class DimensionScore:
    name: str
    score: int
    max_score: int = 5
    comment: str = ""
    
    @property
    def percentage(self) -> float:
        return (self.score / self.max_score) * 100
    
    def is_passing(self, threshold: int = 3) -> bool:
        return self.score >= threshold


@dataclass
class ReviewResult:
    total_score: float
    verdict: ReviewVerdict
    dimension_scores: Dict[str, int] = field(default_factory=dict)
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    raw_content: str = ""
    
    @property
    def max_score(self) -> int:
        return 50
    
    @property
    def percentage(self) -> float:
        return (self.total_score / self.max_score) * 100
    
    def get_failing_dimensions(self, threshold: int = 3) -> List[str]:
        return [
            name for name, score in self.dimension_scores.items()
            if score < threshold
        ]
    
    def get_dimension_score(self, dimension: str) -> Optional[int]:
        return self.dimension_scores.get(dimension)


class ReviewParser:
    DIMENSIONS = [
        "情节连贯性",
        "角色一致性",
        "对话质量",
        "叙事节奏",
        "描写技巧",
        "情感表达",
        "悬念设置",
        "信息揭示",
        "语言风格",
        "整体质量",
    ]
    
    @classmethod
    def parse(cls, content: str) -> ReviewResult:
        dimension_scores = cls._parse_dimension_scores(content)
        total_score = cls._parse_total_score(content, dimension_scores)
        verdict = cls._determine_verdict(content, total_score)
        issues = cls._parse_issues(content)
        suggestions = cls._parse_suggestions(content)
        
        return ReviewResult(
            total_score=total_score,
            verdict=verdict,
            dimension_scores=dimension_scores,
            issues=issues,
            suggestions=suggestions,
            raw_content=content,
        )
    
    @classmethod
    def _parse_dimension_scores(cls, content: str) -> Dict[str, int]:
        scores = {}
        
        for dim in cls.DIMENSIONS:
            patterns = [
                rf"{dim}[：:]\s*(\d+)/?\d*",
                rf"\|\s*{dim}\s*\|\s*(\d+)/?\d*",
                rf"{dim}\s*[:：]\s*(\d+)",
            ]
            
            for pattern in patterns:
                match = re.search(pattern, content)
                if match:
                    scores[dim] = int(match.group(1))
                    break
        
        return scores
    
    @classmethod
    def _parse_total_score(cls, content: str, dimension_scores: Dict[str, int]) -> float:
        patterns = [
            r"总分[：:]\s*(\d+(?:\.\d+)?)",
            r"Total[：:]\s*(\d+(?:\.\d+)?)",
            r"(\d+(?:\.\d+)?)/50",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return float(match.group(1))
        
        if dimension_scores:
            return float(sum(dimension_scores.values()))
        
        return 35.0
    
    @classmethod
    def _determine_verdict(cls, content: str, total_score: float) -> ReviewVerdict:
        content_lower = content.lower()
        
        if "通过" in content and "需修改" not in content and "需重写" not in content:
            return ReviewVerdict.PASS
        
        if "需重写" in content or total_score < 25:
            return ReviewVerdict.NEEDS_REWRITE
        
        if "需修改" in content or total_score < 35:
            return ReviewVerdict.NEEDS_REVISION
        
        if total_score >= 35:
            return ReviewVerdict.PASS
        
        return ReviewVerdict.NEEDS_REVISION
    
    @classmethod
    def _parse_issues(cls, content: str) -> List[str]:
        issues = []
        
        patterns = [
            r"主要问题[^\n]*\n((?:\d+\.[^\n]+\n?)+)",
            r"问题[：:][^\n]*\n((?:[-•]\s*[^\n]+\n?)+)",
            r"##\s*主要问题\n((?:[-•\d]+\.[^\n]+\n?)+)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                block = match.group(1)
                found = re.findall(r"(?:\d+\.|[-•])\s*([^\n]+)", block)
                issues.extend(found)
                break
        
        return issues
    
    @classmethod
    def _parse_suggestions(cls, content: str) -> List[str]:
        suggestions = []
        
        patterns = [
            r"改进建议[^\n]*\n((?:\d+\.[^\n]+\n?)+)",
            r"建议[：:][^\n]*\n((?:[-•]\s*[^\n]+\n?)+)",
            r"##\s*改进建议\n((?:[-•\d]+\.[^\n]+\n?)+)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                block = match.group(1)
                found = re.findall(r"(?:\d+\.|[-•])\s*([^\n]+)", block)
                suggestions.extend(found)
                break
        
        return suggestions


class Reviewer:
    def __init__(self, agent: SubAgent):
        if agent.role != AgentRole.REVIEWER:
            raise ValueError(f"Expected REVIEWER agent, got {agent.role}")
        self.agent = agent
    
    async def review_chapter(self, chapter_content: str, chapter_num: int) -> ReviewResult:
        instruction = f"""审查第 {chapter_num} 章的质量。

请使用10维度检查清单进行审查，并输出：
1. 每个维度的评分（1-5分）
2. 总分（满分50分）
3. 主要问题列表
4. 改进建议
5. 最终裁决（通过/需修改/需重写）

评分标准：
- 35分以上：通过
- 25-34分：需修改
- 25分以下：需重写"""
        
        response = await self.agent.process(
            instruction,
            context=f"章节内容:\n{chapter_content}"
        )
        
        if not response.success:
            return ReviewResult(
                total_score=0,
                verdict=ReviewVerdict.NEEDS_REWRITE,
                issues=[f"审查失败: {response.content}"],
            )
        
        return ReviewParser.parse(response.content)
    
    async def quick_review(self, chapter_content: str) -> tuple[float, ReviewVerdict]:
        instruction = """快速审查章节质量。

只需要输出：
1. 总分（满分50分）
2. 裁决（通过/需修改/需重写）"""
        
        response = await self.agent.process(
            instruction,
            context=f"章节内容:\n{chapter_content}"
        )
        
        if not response.success:
            return 0.0, ReviewVerdict.NEEDS_REWRITE
        
        result = ReviewParser.parse(response.content)
        return result.total_score, result.verdict
    
    @staticmethod
    def format_review_report(result: ReviewResult, chapter_num: int) -> str:
        lines = [
            f"# 第 {chapter_num} 章审查报告",
            "",
            f"**总分**: {result.total_score:.1f}/50 ({result.percentage:.1f}%)",
            f"**裁决**: {result.verdict.value}",
            "",
        ]
        
        if result.dimension_scores:
            lines.append("## 维度评分")
            lines.append("")
            lines.append("| 维度 | 评分 | 状态 |")
            lines.append("|------|------|------|")
            for dim, score in result.dimension_scores.items():
                status = "✓" if score >= 3 else "✗"
                lines.append(f"| {dim} | {score}/5 | {status} |")
            lines.append("")
        
        if result.issues:
            lines.append("## 主要问题")
            lines.append("")
            for i, issue in enumerate(result.issues, 1):
                lines.append(f"{i}. {issue}")
            lines.append("")
        
        if result.suggestions:
            lines.append("## 改进建议")
            lines.append("")
            for i, suggestion in enumerate(result.suggestions, 1):
                lines.append(f"{i}. {suggestion}")
            lines.append("")
        
        return "\n".join(lines)
