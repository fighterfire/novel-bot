import os
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger


class SuspenseStatus(Enum):
    ACTIVE = "活跃"
    RESOLVED = "已回收"


class ForeshadowStatus(Enum):
    ACTIVE = "活跃"
    REVEALED = "已揭示"


class TensionLevel(Enum):
    HIGH = "高"
    MEDIUM = "中"
    LOW = "低"


@dataclass
class Suspense:
    id: str
    description: str
    planted_chapter: int
    planned_resolve_chapter: int
    tension: TensionLevel = TensionLevel.MEDIUM
    status: SuspenseStatus = SuspenseStatus.ACTIVE
    resolved_chapter: Optional[int] = None
    effect: str = ""

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "description": self.description,
            "planted_chapter": self.planted_chapter,
            "planned_resolve_chapter": self.planned_resolve_chapter,
            "tension": self.tension.value,
            "status": self.status.value,
            "resolved_chapter": self.resolved_chapter,
            "effect": self.effect,
        }


@dataclass
class Foreshadow:
    id: str
    description: str
    planted_chapter: int
    plant_method: str
    planned_reveal_chapter: int
    status: ForeshadowStatus = ForeshadowStatus.ACTIVE
    revealed_chapter: Optional[int] = None
    reveal_method: str = ""
    effect: str = ""

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "description": self.description,
            "planted_chapter": self.planted_chapter,
            "plant_method": self.plant_method,
            "planned_reveal_chapter": self.planned_reveal_chapter,
            "status": self.status.value,
            "revealed_chapter": self.revealed_chapter,
            "reveal_method": self.reveal_method,
            "effect": self.effect,
        }


@dataclass
class CharacterState:
    name: str
    chapter: int
    changes: str
    location: str = ""
    relationships: Dict[str, str] = field(default_factory=dict)


@dataclass
class ChapterArchive:
    chapter_num: int
    summary: str
    key_events: List[str] = field(default_factory=list)
    character_changes: List[CharacterState] = field(default_factory=list)
    new_suspenses: List[Suspense] = field(default_factory=list)
    resolved_suspenses: List[str] = field(default_factory=list)
    new_foreshadows: List[Foreshadow] = field(default_factory=list)
    revealed_foreshadows: List[str] = field(default_factory=list)
    word_count: int = 0


class BibleManager:
    def __init__(self, workspace_path: str):
        self.workspace_path = Path(workspace_path)
        self.bible_path = self.workspace_path / "bible"
        self._ensure_structure()

    def _ensure_structure(self):
        dirs = [
            self.bible_path,
            self.bible_path / "characters" / "main",
            self.bible_path / "characters" / "supporting",
            self.bible_path / "characters" / "minor",
            self.bible_path / "plot",
            self.bible_path / "world",
        ]
        
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
        
        default_files = {
            "plot/outline.md": self._default_outline(),
            "plot/suspense.md": self._default_suspense(),
            "plot/foreshadow.md": self._default_foreshadow(),
            "changelog.md": self._default_changelog(),
        }
        
        for rel_path, content in default_files.items():
            file_path = self.bible_path / rel_path
            if not file_path.exists():
                file_path.write_text(content, encoding="utf-8")

    def _default_outline(self) -> str:
        return """# 大纲

## 故事概述

[一句话概括故事核心]

## 主题

[故事探讨的主题]

## 章节列表

| 章节 | 标题 | 核心事件 | 状态 |
|------|------|----------|------|
| 1 | | | 待写 |
"""

    def _default_suspense(self) -> str:
        return """# 悬念追踪

## 活跃悬念

| ID | 悬念描述 | 埋设章节 | 计划回收 | 紧张度 | 状态 |
|----|----------|----------|----------|--------|------|

## 已回收悬念

| ID | 悬念描述 | 埋设章节 | 回收章节 | 效果评估 |
|----|----------|----------|----------|----------|
"""

    def _default_foreshadow(self) -> str:
        return """# 伏笔追踪

## 活跃伏笔

| ID | 伏笔描述 | 埋设章节 | 埋设方式 | 计划揭示 | 状态 |
|----|----------|----------|----------|----------|------|

## 已揭示伏笔

| ID | 伏笔描述 | 埋设章节 | 揭示章节 | 揭示方式 | 效果 |
|----|----------|----------|----------|----------|------|
"""

    def _default_changelog(self) -> str:
        return f"""# 更新日志

本文件记录故事圣经的所有重要变更。

---

## {datetime.now().strftime("%Y-%m-%d")}

### 新增
- 创建故事圣经目录结构

"""

    def add_suspense(
        self,
        description: str,
        planted_chapter: int,
        planned_resolve_chapter: int,
        tension: TensionLevel = TensionLevel.MEDIUM,
    ) -> Suspense:
        existing = self.get_active_suspenses()
        next_id = f"S{len(existing) + 1:03d}"
        
        suspense = Suspense(
            id=next_id,
            description=description,
            planted_chapter=planted_chapter,
            planned_resolve_chapter=planned_resolve_chapter,
            tension=tension,
        )
        
        self._add_suspense_to_file(suspense)
        self._log_change("悬念", f"新增悬念 {next_id}: {description}")
        
        return suspense

    def resolve_suspense(self, suspense_id: str, resolved_chapter: int, effect: str = "满意") -> bool:
        suspense = self._find_suspense(suspense_id)
        if not suspense:
            return False
        
        suspense.status = SuspenseStatus.RESOLVED
        suspense.resolved_chapter = resolved_chapter
        suspense.effect = effect
        
        self._move_suspense_to_resolved(suspense)
        self._log_change("悬念", f"回收悬念 {suspense_id}: {suspense.description}")
        
        return True

    def add_foreshadow(
        self,
        description: str,
        planted_chapter: int,
        plant_method: str,
        planned_reveal_chapter: int,
    ) -> Foreshadow:
        existing = self.get_active_foreshadows()
        next_id = f"F{len(existing) + 1:03d}"
        
        foreshadow = Foreshadow(
            id=next_id,
            description=description,
            planted_chapter=planted_chapter,
            plant_method=plant_method,
            planned_reveal_chapter=planned_reveal_chapter,
        )
        
        self._add_foreshadow_to_file(foreshadow)
        self._log_change("伏笔", f"新增伏笔 {next_id}: {description}")
        
        return foreshadow

    def reveal_foreshadow(
        self,
        foreshadow_id: str,
        revealed_chapter: int,
        reveal_method: str = "直接说明",
        effect: str = "满意",
    ) -> bool:
        foreshadow = self._find_foreshadow(foreshadow_id)
        if not foreshadow:
            return False
        
        foreshadow.status = ForeshadowStatus.REVEALED
        foreshadow.revealed_chapter = revealed_chapter
        foreshadow.reveal_method = reveal_method
        foreshadow.effect = effect
        
        self._move_foreshadow_to_revealed(foreshadow)
        self._log_change("伏笔", f"揭示伏笔 {foreshadow_id}: {foreshadow.description}")
        
        return True

    def get_active_suspenses(self) -> List[Suspense]:
        return self._parse_suspenses_from_file(active=True)

    def get_resolved_suspenses(self) -> List[Suspense]:
        return self._parse_suspenses_from_file(active=False)

    def get_active_foreshadows(self) -> List[Foreshadow]:
        return self._parse_foreshadows_from_file(active=True)

    def get_revealed_foreshadows(self) -> List[Foreshadow]:
        return self._parse_foreshadows_from_file(active=False)

    def update_character(
        self,
        name: str,
        chapter: int,
        changes: str,
        category: str = "main",
    ) -> bool:
        char_file = self.bible_path / "characters" / category / f"{name}.md"
        
        if not char_file.exists():
            self._create_character_file(name, category)
        
        content = char_file.read_text(encoding="utf-8")
        
        change_entry = f"| {chapter} | {changes} |\n"
        
        if "## 状态变化记录" in content:
            content = content.replace(
                "## 状态变化记录\n\n| 章节 | 变化描述 |\n|------|----------|\n",
                f"## 状态变化记录\n\n| 章节 | 变化描述 |\n|------|----------|\n{change_entry}"
            )
        else:
            content += f"\n## 状态变化记录\n\n| 章节 | 变化描述 |\n|------|----------|\n{change_entry}"
        
        char_file.write_text(content, encoding="utf-8")
        self._log_change("角色", f"更新角色 {name} - 第{chapter}章: {changes}")
        
        return True

    def archive_chapter(self, archive: ChapterArchive) -> bool:
        self._update_outline(archive)
        
        for change in archive.character_changes:
            self.update_character(
                change.name,
                change.chapter,
                change.changes,
            )
        
        for suspense in archive.new_suspenses:
            self._add_suspense_to_file(suspense)
        
        for suspense_id in archive.resolved_suspenses:
            self.resolve_suspense(suspense_id, archive.chapter_num)
        
        for foreshadow in archive.new_foreshadows:
            self._add_foreshadow_to_file(foreshadow)
        
        for foreshadow_id in archive.revealed_foreshadows:
            self.reveal_foreshadow(foreshadow_id, archive.chapter_num)
        
        self._log_change(
            "章节",
            f"归档第 {archive.chapter_num} 章 - 字数: {archive.word_count}"
        )
        
        return True

    def get_chapter_summary(self, chapter_num: int) -> Optional[str]:
        outline_file = self.bible_path / "plot" / "outline.md"
        if not outline_file.exists():
            return None
        
        content = outline_file.read_text(encoding="utf-8")
        pattern = rf"\| {chapter_num} \| [^|]+ \| ([^|]+) \|"
        match = re.search(pattern, content)
        
        return match.group(1).strip() if match else None

    def get_bible_summary(self) -> Dict[str, Any]:
        return {
            "active_suspenses": len(self.get_active_suspenses()),
            "resolved_suspenses": len(self.get_resolved_suspenses()),
            "active_foreshadows": len(self.get_active_foreshadows()),
            "revealed_foreshadows": len(self.get_revealed_foreshadows()),
            "characters": self._count_characters(),
        }

    def _parse_suspenses_from_file(self, active: bool = True) -> List[Suspense]:
        file_path = self.bible_path / "plot" / "suspense.md"
        if not file_path.exists():
            return []
        
        content = file_path.read_text(encoding="utf-8")
        section = "活跃悬念" if active else "已回收悬念"
        
        pattern = rf"{section}[^\n]*\n((?:\|[^|]+\|[^|]+\|[^|]+\|[^|]+\|[^|]+\|[^|]+\|\n?)+)"
        match = re.search(pattern, content)
        
        if not match:
            return []
        
        suspenses = []
        for line in match.group(1).strip().split("\n"):
            if line.startswith("|") and not line.startswith("| ID"):
                parts = [p.strip() for p in line.split("|") if p.strip()]
                if len(parts) >= 5:
                    suspense = Suspense(
                        id=parts[0],
                        description=parts[1],
                        planted_chapter=int(re.search(r"\d+", parts[2]).group() or 0),
                        planned_resolve_chapter=int(re.search(r"\d+", parts[3]).group() or 0),
                        tension=TensionLevel(parts[4]) if parts[4] in ["高", "中", "低"] else TensionLevel.MEDIUM,
                        status=SuspenseStatus.ACTIVE if active else SuspenseStatus.RESOLVED,
                    )
                    suspenses.append(suspense)
        
        return suspenses

    def _parse_foreshadows_from_file(self, active: bool = True) -> List[Foreshadow]:
        file_path = self.bible_path / "plot" / "foreshadow.md"
        if not file_path.exists():
            return []
        
        content = file_path.read_text(encoding="utf-8")
        section = "活跃伏笔" if active else "已揭示伏笔"
        
        pattern = rf"{section}[^\n]*\n((?:\|[^|]+\|[^|]+\|[^|]+\|[^|]+\|[^|]+\|[^|]+\|\n?)+)"
        match = re.search(pattern, content)
        
        if not match:
            return []
        
        foreshadows = []
        for line in match.group(1).strip().split("\n"):
            if line.startswith("|") and not line.startswith("| ID"):
                parts = [p.strip() for p in line.split("|") if p.strip()]
                if len(parts) >= 5:
                    foreshadow = Foreshadow(
                        id=parts[0],
                        description=parts[1],
                        planted_chapter=int(re.search(r"\d+", parts[2]).group() or 0),
                        plant_method=parts[3] if len(parts) > 3 else "",
                        planned_reveal_chapter=int(re.search(r"\d+", parts[4]).group() or 0),
                        status=ForeshadowStatus.ACTIVE if active else ForeshadowStatus.REVEALED,
                    )
                    foreshadows.append(foreshadow)
        
        return foreshadows

    def _add_suspense_to_file(self, suspense: Suspense):
        file_path = self.bible_path / "plot" / "suspense.md"
        content = file_path.read_text(encoding="utf-8")
        
        new_line = f"| {suspense.id} | {suspense.description} | 第{suspense.planted_chapter}章 | 第{suspense.planned_resolve_chapter}章 | {suspense.tension.value} | {suspense.status.value} |\n"
        
        pattern = r"(## 活跃悬念[^\n]*\n\|[^|]+\|[^|]+\|[^|]+\|[^|]+\|[^|]+\|[^|]+\|\n)"
        if re.search(pattern, content):
            content = re.sub(pattern, r"\1" + new_line, content)
        else:
            content = content.replace(
                "## 活跃悬念\n\n",
                f"## 活跃悬念\n\n| ID | 悬念描述 | 埋设章节 | 计划回收 | 紧张度 | 状态 |\n|----|----------|----------|----------|--------|------|\n{new_line}"
            )
        
        file_path.write_text(content, encoding="utf-8")

    def _move_suspense_to_resolved(self, suspense: Suspense):
        file_path = self.bible_path / "plot" / "suspense.md"
        content = file_path.read_text(encoding="utf-8")
        
        pattern = rf"\| {suspense.id} \| [^|]+ \| [^|]+ \| [^|]+ \| [^|]+ \| 活跃 \|\n"
        content = re.sub(pattern, "", content)
        
        new_line = f"| {suspense.id} | {suspense.description} | 第{suspense.planted_chapter}章 | 第{suspense.resolved_chapter}章 | {suspense.effect} |\n"
        
        pattern = r"(## 已回收悬念[^\n]*\n\|[^|]+\|[^|]+\|[^|]+\|[^|]+\|[^|]+\|\n)"
        if re.search(pattern, content):
            content = re.sub(pattern, r"\1" + new_line, content)
        else:
            content = content.replace(
                "## 已回收悬念\n\n",
                f"## 已回收悬念\n\n| ID | 悬念描述 | 埋设章节 | 回收章节 | 效果评估 |\n|----|----------|----------|----------|----------|\n{new_line}"
            )
        
        file_path.write_text(content, encoding="utf-8")

    def _add_foreshadow_to_file(self, foreshadow: Foreshadow):
        file_path = self.bible_path / "plot" / "foreshadow.md"
        content = file_path.read_text(encoding="utf-8")
        
        new_line = f"| {foreshadow.id} | {foreshadow.description} | 第{foreshadow.planted_chapter}章 | {foreshadow.plant_method} | 第{foreshadow.planned_reveal_chapter}章 | {foreshadow.status.value} |\n"
        
        pattern = r"(## 活跃伏笔[^\n]*\n\|[^|]+\|[^|]+\|[^|]+\|[^|]+\|[^|]+\|[^|]+\|\n)"
        if re.search(pattern, content):
            content = re.sub(pattern, r"\1" + new_line, content)
        else:
            content = content.replace(
                "## 活跃伏笔\n\n",
                f"## 活跃伏笔\n\n| ID | 伏笔描述 | 埋设章节 | 埋设方式 | 计划揭示 | 状态 |\n|----|----------|----------|----------|----------|------|\n{new_line}"
            )
        
        file_path.write_text(content, encoding="utf-8")

    def _move_foreshadow_to_revealed(self, foreshadow: Foreshadow):
        file_path = self.bible_path / "plot" / "foreshadow.md"
        content = file_path.read_text(encoding="utf-8")
        
        pattern = rf"\| {foreshadow.id} \| [^|]+ \| [^|]+ \| [^|]+ \| [^|]+ \| 活跃 \|\n"
        content = re.sub(pattern, "", content)
        
        new_line = f"| {foreshadow.id} | {foreshadow.description} | 第{foreshadow.planted_chapter}章 | 第{foreshadow.revealed_chapter}章 | {foreshadow.reveal_method} | {foreshadow.effect} |\n"
        
        pattern = r"(## 已揭示伏笔[^\n]*\n\|[^|]+\|[^|]+\|[^|]+\|[^|]+\|[^|]+\|[^|]+\|\n)"
        if re.search(pattern, content):
            content = re.sub(pattern, r"\1" + new_line, content)
        else:
            content = content.replace(
                "## 已揭示伏笔\n\n",
                f"## 已揭示伏笔\n\n| ID | 伏笔描述 | 埋设章节 | 揭示章节 | 揭示方式 | 效果 |\n|----|----------|----------|----------|----------|------|\n{new_line}"
            )
        
        file_path.write_text(content, encoding="utf-8")

    def _find_suspense(self, suspense_id: str) -> Optional[Suspense]:
        for s in self.get_active_suspenses():
            if s.id == suspense_id:
                return s
        return None

    def _find_foreshadow(self, foreshadow_id: str) -> Optional[Foreshadow]:
        for f in self.get_active_foreshadows():
            if f.id == foreshadow_id:
                return f
        return None

    def _create_character_file(self, name: str, category: str = "main"):
        char_file = self.bible_path / "characters" / category / f"{name}.md"
        
        template = f"""# {name}

## 基本信息

- **姓名**：{name}
- **首次出场**：

## 性格特点

[待补充]

## 状态变化记录

| 章节 | 变化描述 |
|------|----------|
"""
        
        char_file.write_text(template, encoding="utf-8")

    def _update_outline(self, archive: ChapterArchive):
        outline_file = self.bible_path / "plot" / "outline.md"
        content = outline_file.read_text(encoding="utf-8")
        
        pattern = rf"\| {archive.chapter_num} \| [^|]+ \| [^|]+ \| [^|]+ \|"
        replacement = f"| {archive.chapter_num} | | {archive.summary[:50]} | 已完成 |"
        
        if re.search(pattern, content):
            content = re.sub(pattern, replacement, content)
        else:
            new_line = f"| {archive.chapter_num} | | {archive.summary[:50]} | 已完成 |\n"
            content = content.rstrip() + "\n" + new_line
        
        outline_file.write_text(content, encoding="utf-8")

    def _log_change(self, category: str, description: str):
        changelog_file = self.bible_path / "changelog.md"
        content = changelog_file.read_text(encoding="utf-8")
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        if today in content:
            pattern = rf"(## {today}[^\n]*\n)"
            new_entry = f"\n- [{category}] {description}\n"
            content = re.sub(pattern, r"\1" + new_entry, content)
        else:
            new_section = f"""

---

## {today}

- [{category}] {description}
"""
            content = content.rstrip() + new_section
        
        changelog_file.write_text(content, encoding="utf-8")

    def _count_characters(self) -> int:
        count = 0
        for category in ["main", "supporting", "minor"]:
            char_dir = self.bible_path / "characters" / category
            if char_dir.exists():
                count += len(list(char_dir.glob("*.md")))
        return count
