# Plan v3 — Việt hóa Toàn diện (Folder + File rename)

> **Trạng thái:** ⏸ Postponed. Sẽ triển khai trong phiên sau.
>
> **Lý do hoãn:** P2 (aliases) đã giải quyết 80% UX VN trong Obsidian (graph,
> search, autocomplete, wikilinks). P3 là refactor lớn (15 file code + 38 prompts
> + tests + migration) chỉ để fix nốt 20% còn lại (sidebar tree, tab title,
> Windows File Explorer).

## Phạm vi

Đổi toàn bộ folder + file Brain sang tiếng Việt **không dấu** (an toàn path).
Filesystem thật sẽ là tiếng Việt → mọi nơi (Obsidian sidebar, tab title, Windows
File Explorer, Git, terminal, MCP path) hiện tiếng Việt.

## Bảng rename đề xuất (chốt sau khi user duyệt)

### Top-level folders

| English (hiện tại) | Tiếng Việt không dấu | Ghi chú |
|---|---|---|
| `00-Brain` | `00-Bo-Nao` | hub tri thức |
| `00-Templates-Custom` | `00-Mau-Rieng` | BYOT |
| `01-Departments` | `01-Phong-Ban` | |
| `02-Tasks` | `02-Nhiem-Vu` | |
| `03-Outputs` | `03-Ket-Qua` | render docx/xlsx |
| `99-Archive` | `99-Luu-Tru` | |

### Brain files

| English | Tiếng Việt | Ghi chú |
|---|---|---|
| `strategy.md` | `chien-luoc.md` | |
| `laws.md` | `luat.md` | |
| `budget.md` | `ngan-sach.md` | |
| `products.md` | `san-pham.md` | |
| `headcount.md` | `nhan-su.md` | |
| `state.md` | `tinh-trang.md` | |
| `glossary.md` | `tu-dien.md` | |
| `decisions-log.md` | `nhat-ky-quyet-dinh.md` | |

### Department folders (12 core)

| English | Tiếng Việt | Giữ nguyên? |
|---|---|---|
| `01-governance` | `01-Quan-Tri-Phap-Ly` | đổi |
| `02-strategy` | `02-Chien-Luoc` | đổi |
| `03-finance` | `03-Tai-Chinh` | đổi |
| `04-people` | `04-Nhan-Su` | đổi |
| `05-operations` | `05-Van-Hanh` | đổi |
| `06-sales` | `06-Kinh-Doanh` | đổi |
| `07-marketing` | `07-Marketing` | **GIỮ** (term quốc tế) |
| `08-customer` | `08-Khach-Hang` | đổi |
| `09-product-tech` | `09-San-Pham-Cong-Nghe` | đổi |
| `10-training` | `10-Dao-Tao` | đổi |
| `11-reporting` | `11-Bao-Cao` | đổi |
| `12-growth` | `12-Tang-Truong` | đổi |

### Pack departments

| English | Tiếng Việt |
|---|---|
| `13-kitchen` | `13-Bep` |
| `14-food-safety` | `14-An-Toan-Thuc-Pham` |
| `13-warehouse` | `13-Kho-Van` |
| `14-logistics` | `14-Logistics` (giữ) |
| `13-engineering` | `13-Ky-Thuat` |
| `14-product-design` | `14-Thiet-Ke-San-Pham` |
| `15-data` | `15-Du-Lieu` |

## Files cần refactor

### Core code (15 files)

- `core/brain/reader.py` — đọc 8 Brain files theo tên
- `core/brain/memory.py` — append decisions-log
- `core/brain/schema.py` — reference path
- `core/brain/gap_analyzer.py` — citation format
- `core/orchestrator/flow_controller.py` — `00-Brain/glossary.md`, `03-Outputs/`
- `core/orchestrator/router.py` — list `01-governance, 02-strategy, ...`
- `core/cli.py` — `02-Tasks/`, `03-Outputs/`
- `core/mcp_server.py` — task folder paths
- `core/obsidian/vault.py` — `02-Tasks/`
- `core/obsidian/template_resolver.py` — `01-Departments/`
- `core/onboard.py` — `00-Brain/`, `01-Departments/`, BYOT keywords
- `core/upgrade.py` — paths
- `core/wikilinks.py` — paths
- `core/agents/pro_advocate.py` — agent prompt mention `strategy.md, products.md`
- `core/clarifier/question_generator.py` — citation format

**Đề xuất kiến trúc:** Tạo `core/paths.py` — 1 nguồn sự thật:

```python
class VaultPaths:
    BRAIN = "00-Bo-Nao"
    DEPARTMENTS = "01-Phong-Ban"
    TASKS = "02-Nhiem-Vu"
    OUTPUTS = "03-Ket-Qua"
    ARCHIVE = "99-Luu-Tru"

class BrainFiles:
    STRATEGY = "chien-luoc.md"
    LAWS = "luat.md"
    # ...
```

→ Mọi file core import từ `core.paths`. Đổi 1 chỗ là toàn bộ đổi.

### Source content (40+ files)

- 38 agent prompts: rewrite citations từ `strategy.md` → `chien-luoc.md`, từ
  `laws.md` → `luat.md`, ...
- `pack.yaml` (3 packs): có thể không cần đổi (chỉ ref dept code, code đã đổi
  trong department folder)
- `vault-template/00-Brain/*` → rename + đổi tên thư mục cha
- `departments/*` folder structure
- `packs/*/departments/*` folder structure

### Tests

- `tests/fixtures/techco-vault/` — rename thư mục theo cấu trúc mới
- Mọi test reference path trực tiếp

### Migration script

```python
# core/migrate_to_vn.py
def migrate_vault_to_vn(vault_path: Path) -> dict:
    """Rename folders + files trong vault hiện có sang tiếng Việt.
    
    Sequence:
    1. Rename top-level folders (00-Brain → 00-Bo-Nao, ...)
    2. Rename Brain files (strategy.md → chien-luoc.md, ...)
    3. Rename department folders (01-governance → 01-Quan-Tri-Phap-Ly, ...)
    4. Update wikilinks trong index.md hubs (regenerate bằng wikilinks.py)
    5. Update agent ## Liên kết blocks (regenerate)
    """
```

→ Add MCP tool `vn_migrate_to_vn(vault)` để CEO chạy từ Claude Desktop.

## Risk Matrix

| Risk | Severity | Mitigation |
|---|---|---|
| Code reads hardcoded path → file not found | Cao | Tập trung paths trong `core/paths.py`, search-replace có hệ thống |
| Agent prompts cite `strategy.md` → broken citation | Cao | Re-run agent enrichment script với mapping mới |
| `pack.yaml` reference dept code cũ | Trung | Update `extends_departments.target` theo mapping |
| Migration script fail giữa chừng → vault corrupt | Cao | Backup vault trước migration; transactional approach (rename all hoặc rollback) |
| Test fixtures reference path cũ | Trung | Rename fixture folder + update test asserts |
| User vault đã chỉnh manual → conflict | Trung | Migration script preserve user content, chỉ rename folder/file |
| Dấu tiếng Việt trong path → Windows/Git edge case | Thấp | Dùng **không dấu** + dấu nối `-` |
| Tab title trong Obsidian vẫn hiện filename | Đã chấp nhận | Filename giờ là tiếng Việt rồi → OK |

## Estimate

- **3-4 giờ** implementation + testing
- **Sequence:**
  1. Create `core/paths.py` constants (15 phút)
  2. Refactor 15 core files import paths constants (45 phút)
  3. Rename source folders + files (30 phút)
  4. Rewrite 38 agent prompts via script (30 phút)
  5. Update tests + fixtures (45 phút)
  6. Write migration script + MCP tool (30 phút)
  7. Test on temp vault + ABC Coffee (30 phút)
  8. Commit + docs (15 phút)

## Acceptance Criteria

- [ ] `python -m pytest tests/ -q` pass 143+
- [ ] Onboard vault mới → folders + files tất cả tiếng Việt không dấu
- [ ] Agent prompts cite đúng filename mới
- [ ] `vn_migrate_to_vn` MCP tool migrate vault cũ thành công
- [ ] ABC Coffee vault migrated → Brain/Departments/Tasks tất cả tiếng Việt
- [ ] Obsidian sidebar + Windows File Explorer hiện tiếng Việt
- [ ] Backward-compat: vault cũ chưa migrate vẫn chạy được? (Quyết định: KHÔNG —
      bắt buộc migrate, plugin tốt hơn giữ 1 cấu trúc)

## Câu hỏi mở (cần CEO quyết khi triển khai)

1. **Có dấu hay không dấu?** Đề xuất: KHÔNG dấu để an toàn path. (`Quan-Tri-Phap-Ly`)
2. **Backward-compat mode?** Đề xuất: KHÔNG — yêu cầu migrate.
3. **`07-Marketing` giữ tiếng Anh?** Đề xuất: GIỮ.
4. **Có đổi tên agent ID (cfo → giam-doc-tai-chinh)?** Đề xuất: KHÔNG —
   agent ID là technical identifier, giữ tiếng Anh.

## Liên kết

- Plan trước: `plans/v2-mcp-sampling-260506.md`
- Commit P2 (aliases): `bc395be`
- Implementation log: `SESSION-LOG.md`
