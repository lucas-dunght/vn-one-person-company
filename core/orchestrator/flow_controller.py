"""Điều phối toàn bộ flow: brief → router → gap → clarify (Stop pre) →
   research → meeting → synthesizer (Stop 1) → execution (Stop 2)."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional
import re

from core.brain.reader import BrainReader
from core.brain.gap_analyzer import GapAnalyzer
from core.clarifier.question_generator import QuestionGenerator
from core.clarifier.clarification_io import (
    write_clarification, read_answers,
)
from core.obsidian.vault import ObsidianVault
from core.orchestrator.router import Router
from core.utils.config import load_config


class FlowStage(str, Enum):
    PAUSE_CLARIFICATION = "PAUSE_CLARIFICATION"
    PAUSE_DECISION_REPORT = "PAUSE_DECISION_REPORT"
    PAUSE_EXECUTE = "PAUSE_EXECUTE"
    DONE = "DONE"
    ERROR = "ERROR"


@dataclass
class FlowResult:
    stage: FlowStage
    task_folder: Path
    message: str = ""
    error: Optional[str] = None


def _slugify(brief: str, max_len: int = 50) -> str:
    s = re.sub(r"[^\w\s-]", "", brief.lower())
    s = re.sub(r"\s+", "-", s.strip())[:max_len]
    return s.strip("-") or "task"


class FlowController:
    def __init__(self, vault_root: Path, llm):
        self.vault = ObsidianVault(vault_root)
        self.llm = llm
        self.config = load_config()

    def run(self, brief: str) -> FlowResult:
        """Stage 1: brief → router → gap → clarification (PAUSE)."""
        # 1. Create task folder
        task_folder = self.vault.create_task_folder(_slugify(brief))
        (task_folder / "00-brief.md").write_text(
            f"---\ntype: brief\n---\n# Brief\n\n{brief}\n", encoding="utf-8",
        )

        # 2. Read Brain
        brain = BrainReader(self.vault.root).load()

        # 3. Router classify
        rules_path = Path(__file__).parent / "classifier_rules.yaml"
        router = Router(self.llm, rules_path=rules_path)
        classification = router.classify(brief, brain)

        (task_folder / "01-routing.md").write_text(
            f"---\ntype: routing\n---\n# Phân loại task\n\n"
            f"- **Class:** {classification.class_.value}\n"
            f"- **Departments:** {', '.join(classification.departments)}\n"
            f"- **Reasoning:** {classification.reasoning}\n",
            encoding="utf-8",
        )

        # 4. Context dump
        (task_folder / "02-context.md").write_text(
            "---\ntype: context\n---\n# Brain context loaded\n\n"
            f"```yaml\n{brain.model_dump_json(indent=2)}\n```\n",
            encoding="utf-8",
        )

        # 5. Gap analysis
        analyzer = GapAnalyzer(self.llm)
        gaps = analyzer.analyze(brief, brain)

        if not gaps:
            return FlowResult(
                stage=FlowStage.PAUSE_DECISION_REPORT,
                task_folder=task_folder,
                message="Không có gap, sẵn sàng chạy meeting (Phase 4+5 sẽ wire).",
            )

        # 6. Generate questions
        qg = QuestionGenerator(self.llm)
        questions = qg.generate(gaps, brain.model_dump(), brief)

        if not questions:
            return FlowResult(
                stage=FlowStage.PAUSE_DECISION_REPORT,
                task_folder=task_folder,
                message="Gap có nhưng không CRITICAL/WARN, skip clarification.",
            )

        # 7. Write clarification + PAUSE
        clarification_path = task_folder / "03-clarification.md"
        write_clarification(clarification_path, questions)

        return FlowResult(
            stage=FlowStage.PAUSE_CLARIFICATION,
            task_folder=task_folder,
            message=f"Vui lòng trả lời {len(questions)} câu trong {clarification_path.name}",
        )

    def resume_after_clarification(self, task_folder: Path) -> FlowResult:
        """Stage 2: read answers → continue flow (Phase 4+ sẽ wire research+meeting)."""
        clarification_path = task_folder / "03-clarification.md"
        if not clarification_path.exists():
            return FlowResult(
                stage=FlowStage.ERROR, task_folder=task_folder,
                error="Không tìm thấy 03-clarification.md",
            )

        answers = read_answers(clarification_path)
        unanswered = [a for a in answers if a.choice is None and not a.free_text_answer]
        if unanswered:
            return FlowResult(
                stage=FlowStage.PAUSE_CLARIFICATION,
                task_folder=task_folder,
                message=f"Còn {len(unanswered)} câu chưa trả lời",
            )

        # Save normalized answers
        (task_folder / "03-clarification-answered.md").write_text(
            "---\ntype: answers\n---\n"
            + "\n".join(f"- Q: {a.question_text}\n  A: {a.choice or a.free_text_answer}"
                       for a in answers),
            encoding="utf-8",
        )

        # Phase 4-5 wires research + meeting here
        return FlowResult(
            stage=FlowStage.PAUSE_DECISION_REPORT,
            task_folder=task_folder,
            message="Đã ghi nhận trả lời. Phase 4+5 sẽ wire research + meeting.",
        )
