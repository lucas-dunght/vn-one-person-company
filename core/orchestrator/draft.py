"""Single-call document drafting — bypass debate engine cho boilerplate docs.

Use case: HĐLĐ, JD, nội quy, phiếu thu, SOP đơn giản — không cần multi-agent debate,
chỉ cần Brain context + 1 LLM call để render full content.

Trade-off: nhanh (~10-30s thay vì 1-3 phút) nhưng KHÔNG có pro/con review,
KHÔNG citation validation. Chỉ dùng cho doc có template/structure rõ ràng.

Khi nào nên dùng vn_meeting/vn_run thay thế:
  - Quyết định chiến lược (mở chi nhánh, đổi giá, tuyển senior)
  - Có rủi ro pháp lý/tài chính lớn
  - Cần multi-perspective review

Output: <vault>/02-Tasks/<ts>-draft-<slug>/draft.md (frontmatter + body).
"""
from __future__ import annotations
from datetime import datetime
from pathlib import Path

from core.brain.reader import BrainReader
from core.obsidian.vault import ObsidianVault


_DRAFT_PROMPT = """Bạn là chuyên viên soạn thảo tài liệu cho doanh nghiệp Việt Nam.

Soạn 1 tài liệu hoàn chỉnh dạng Markdown dựa trên yêu cầu CEO + Brain context.

YÊU CẦU CEO:
{brief}

LOẠI TÀI LIỆU: {doc_type}

BRAIN CONTEXT (thông tin DN):
{brain_summary}

QUY TẮC:
1. Tiếng Việt có dấu đầy đủ, văn phong DN chuyên nghiệp.
2. Tham chiếu luật/thông tư VN khi liên quan (vd Bộ luật Lao động 2019, Thông tư 200/2014/TT-BTC).
3. Điền thông tin DN từ Brain (tên, địa chỉ, MST nếu có); placeholder [...] cho phần CEO cần điền.
4. Format Markdown chuẩn: heading H1/H2, list, table khi cần.
5. KHÔNG thêm phần "Lưu ý / Ghi chú của AI" cuối file.

Trả về CHỈ nội dung Markdown (không kèm giải thích, không wrap trong code fence).
"""


def draft_document(
    brief: str,
    vault_root: Path,
    llm,
    doc_type: str = "tài liệu",
) -> dict:
    """Render single document via 1 LLM call. Skip debate.

    Args:
        brief: Yêu cầu CEO (vd "HĐLĐ tuyển trợ lý kế toán cafe Sao Việt, lương 10tr").
        vault_root: Vault path để load Brain + write output.
        llm: LLMProvider (MCPSamplingProvider khi qua Claude Desktop).
        doc_type: Loại doc gợi ý cho LLM (vd "hợp đồng lao động", "JD", "nội quy").

    Returns:
        dict: {task_folder, draft_path, message}
    """
    vault = ObsidianVault(vault_root)

    # Slug từ brief — reuse logic flow_controller
    from core.orchestrator.flow_controller import _slugify
    slug = "draft-" + _slugify(brief, max_len=40)
    task_folder = vault.create_task_folder(slug)

    # Brain context (best-effort — draft không bắt buộc Brain đầy đủ)
    brain_summary = "(Brain chưa khởi tạo)"
    try:
        brain = BrainReader(vault_root).load()
        brain_summary = brain.model_dump_json()[:2500]
    except Exception:
        pass

    # Save brief
    (task_folder / "00-brief.md").write_text(
        f"---\ntype: brief\ndoc_type: {doc_type}\n---\n# Brief\n\n{brief}\n",
        encoding="utf-8",
    )

    # Single LLM call
    messages = [
        {
            "role": "system",
            "content": _DRAFT_PROMPT.format(
                brief=brief,
                doc_type=doc_type,
                brain_summary=brain_summary,
            ),
        },
        {"role": "user", "content": f"Soạn {doc_type} theo yêu cầu trên."},
    ]
    body = llm.complete(messages)

    # Strip code fences if LLM wrapped despite instruction
    body = body.strip()
    if body.startswith("```"):
        lines = body.splitlines()
        if len(lines) >= 2:
            body = "\n".join(lines[1:-1] if lines[-1].startswith("```") else lines[1:])

    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    draft_path = task_folder / "draft.md"
    draft_path.write_text(
        f"---\ntype: draft\ndoc_type: {doc_type}\ngenerated_at: {ts}\n"
        f"source: vn_draft (single-call, no debate)\n---\n\n{body}\n",
        encoding="utf-8",
    )

    return {
        "task_folder": str(task_folder),
        "draft_path": str(draft_path),
        "message": (
            f"Đã soạn {doc_type} tại {draft_path.relative_to(vault_root)}. "
            "Lưu ý: bản nháp single-call, chưa qua review đa quan điểm. "
            "Nếu là quyết định lớn, hãy chạy vn_run/vn_meeting để debate."
        ),
    }
