# VN One Person Company — Hướng dẫn cho người không biết code

> Bạn là chủ doanh nghiệp 1 người (freelancer / chủ quán / shop online / startup solo).
> Bạn muốn có **13 phòng ban AI** (Pháp lý, Tài chính, Marketing, Vận hành, Nhân sự, ...) họp bàn để ra quyết định và soạn tài liệu giúp bạn.
> Bạn **không cần biết code**. Hướng dẫn này từng bước, copy-paste, ai cũng làm được.

---

## ✨ Bạn sẽ làm được gì sau khi setup?

Sau khi cài đặt xong (~45 phút), bạn có thể chat với Claude và ra lệnh kiểu:

| Bạn nói | Hệ thống làm gì |
|---|---|
| "Soạn hợp đồng lao động cho store manager 13tr/tháng" | Phòng Pháp lý + Nhân sự debate → HĐLĐ chuẩn Bộ luật Lao động 2019, có BHXH 23.5%, đầy đủ điều khoản |
| "Lập kế hoạch chiến dịch quảng cáo Tết 50 triệu" | 5 phòng họp 3 vòng → kế hoạch + content calendar + phân bổ ngân sách |
| "Phân tích nên mở chi nhánh 2 ở quận nào" | Phòng Tài chính + Vận hành + Tăng trưởng debate → báo cáo có CAPEX, payback period, rủi ro |
| "Soạn nội quy nhân viên cho quán cafe" | Phòng Nhân sự + Pháp lý → nội quy có lương, ca làm, kỷ luật, đồng phục, thưởng |

→ **Bạn không cần thuê CFO, CMO, COO, luật sư riêng. Hệ thống là họ.**

---

## 📋 Cần chuẩn bị gì trước khi cài đặt

### Phần cứng + thời gian
- [ ] Máy tính chạy Windows 10 hoặc 11 (Mac/Linux cũng được nhưng hướng dẫn này tập trung Windows)
- [ ] Khoảng **45 phút** rảnh để cài đặt
- [ ] Internet ổn định

### Tài khoản (đăng ký miễn phí)
- [ ] Tài khoản **Anthropic Claude Pro** (~480k VNĐ/tháng) — đăng ký tại https://claude.ai
- [ ] Tài khoản **DeepSeek** (free, có $5 credit khi đăng ký mới — đủ chạy hàng trăm task)
- [ ] **Tavily** (free tier 1000 lượt search/tháng — KHUYẾN NGHỊ, để AI tự tra cứu luật/đối thủ trên web)

### Phần mềm sẽ cài (trong hướng dẫn)
- Python 3.11+
- Node.js 18+
- Obsidian (ghi chú + lưu trữ — "bộ nhớ" của DN)
- Claude Desktop (chat với AI — sẽ dùng tab **"</> Code"** bên trong)

> 🎯 **Lưu ý quan trọng:** Claude Desktop có 3 tab: **Chat** | **Cowork** | **</> Code**.
> Hệ thống VN OS được thiết kế chạy trong tab **Code** (timeout 10 phút, gọi được mọi tool MCP).
> Tab Cowork (timeout 60s) chỉ chạy được task nhẹ. Tab Chat không có MCP.

> 💡 **Đừng lo nếu chưa biết các phần mềm này là gì.** Mỗi bước hướng dẫn có link tải + thao tác cụ thể.

---

## 🚀 PHẦN 1 — CÀI ĐẶT (1 lần duy nhất, ~45 phút)

> ⚠️ **Trước khi bắt đầu:** đảm bảo bạn có quyền admin trên máy (cài phần mềm). Nếu máy công ty bị chặn — liên hệ IT.

---

### Bước 1: Cài Python (10 phút)

Python là ngôn ngữ chạy "động cơ" của hệ thống. Bạn không cần lập trình Python, chỉ cần cài để chương trình chạy được.

**Thao tác:**

1. Mở trình duyệt → vào https://www.python.org/downloads/
2. Click nút **"Download Python 3.12.x"** (hoặc bản 3.11 trở lên — không cài Python 3.10 hoặc thấp hơn)
3. Mở file vừa tải (vd `python-3.12.x-amd64.exe`)
4. **CỰC KỲ QUAN TRỌNG:** Tích vào ô **"Add python.exe to PATH"** ở dưới cùng cửa sổ install
5. Click **"Install Now"**
6. Đợi 2-3 phút đến khi thấy "Setup was successful"
7. Click **Close**

**Kiểm tra đã cài thành công:**

1. Nhấn phím **`Windows + R`** → gõ `powershell` → Enter
2. Trong cửa sổ PowerShell màu xanh đen, gõ:
   ```
   python --version
   ```
3. Nhấn Enter. Phải hiện ra: `Python 3.12.x` (hoặc 3.11.x)

❌ Nếu hiện "command not found" → Python chưa vào PATH. Cài lại bước 4 đảm bảo tích ô "Add to PATH".

---

### Bước 2: Cài Node.js (5 phút)

Node.js dùng để chạy MCP (cách Claude kết nối với các công cụ khác).

**Thao tác:**

1. Vào https://nodejs.org
2. Click nút **"LTS"** (Long Term Support — phiên bản ổn định)
3. Mở file vừa tải (vd `node-v20.x.x-x64.msi`)
4. Click **Next** → **Next** → ... → **Install** (chấp nhận mọi mặc định)
5. Đợi cài xong → **Finish**

**Kiểm tra:**

Trong PowerShell (mở mới):
```
node --version
```
Phải hiện: `v20.x.x` hoặc cao hơn.

---

### Bước 3: Cài Obsidian + plugin Local REST API (8 phút)

Obsidian là phần mềm ghi chú. Hệ thống dùng Obsidian làm "bộ nhớ" lưu mọi quyết định + tài liệu của doanh nghiệp.

**3.1 — Tải và cài Obsidian:**

1. Vào https://obsidian.md → click **"Download"**
2. Chọn **Windows installer** (hoặc 64-bit ZIP)
3. Mở file → cài đặt mặc định → Open Obsidian

**3.2 — Tạo vault (kho ghi chú) cho doanh nghiệp:**

1. Khi mở Obsidian lần đầu, click **"Create new vault"**
2. **Vault name:** đặt tên doanh nghiệp của bạn, vd: `Sao Việt`, `My Cafe`, `Acme Co`
3. **Location:** chọn ổ đĩa lớn, vd `F:\vaults` (tự tạo folder này nếu chưa có)
4. Click **Create**

→ Obsidian sẽ mở vault rỗng. Đường dẫn vault sẽ là `F:\vaults\<tên>` (vd `F:\vaults\Sao Việt`)

**3.3 — Bật chế độ cài community plugin:**

1. Click icon ⚙️ Settings (góc trái dưới Obsidian)
2. Bên trái: chọn **"Community plugins"**
3. Click **"Turn on community plugins"** → click **"Turn on"** xác nhận

**3.4 — Cài plugin "Local REST API":**

1. Vẫn ở tab Community plugins → click **"Browse"**
2. Trong ô search, gõ: `Local REST API`
3. Click vào plugin **"Local REST API"** (tác giả: coddingtonbear)
4. Click **"Install"**
5. Sau khi install xong → click **"Enable"**
6. Click **"Options"** (gear icon bên phải plugin)

**3.5 — Lấy API key của plugin:**

1. Trong settings của plugin Local REST API, tìm dòng **"API Key"**
2. Bạn sẽ thấy 1 chuỗi dài tự sinh, vd `0e957bd6...`
3. **Copy chuỗi này** → dán vào Notepad → save tạm vào file `F:\setup-keys.txt` (sau này xóa)
4. Đảm bảo plugin đang **Enabled** (toggle xanh)

> ⚠️ **Cảnh báo bảo mật:** API key này cho phép đọc/ghi/xóa toàn bộ vault. **Không chia sẻ key này cho ai.** Đừng paste vào chat AI hoặc forum công khai.

---

### Bước 4: Tải repo VN One Person Company (5 phút)

Đây là "động cơ" của hệ thống — chứa code 13 phòng ban + 192 template.

**Thao tác:**

1. Vào https://github.com/<owner>/vn-one-person-company *(thay link thật khi public)*
2. Click nút xanh **"Code"** → **"Download ZIP"**
3. Giải nén file ZIP vào ổ đĩa lớn, vd `F:\.work\vn-one-person-company`
4. Đường dẫn cuối cùng phải có dạng `F:\.work\vn-one-person-company\README.md` *(file README tồn tại trực tiếp trong folder, không nằm trong subfolder)*

> 💡 *Tip:* nếu bạn biết Git, có thể `git clone` thay vì tải ZIP — sau này update repo dễ hơn. Nhưng không bắt buộc.

---

### Bước 5: Cài thư viện Python cho repo (5 phút)

**Thao tác:**

1. Mở PowerShell (Windows + R → `powershell` → Enter)
2. Vào folder repo:
   ```powershell
   cd "F:\.work\vn-one-person-company"
   ```
3. Tạo môi trường Python ảo:
   ```powershell
   python -m venv .venv
   ```
   (Đợi 30 giây)
4. Kích hoạt môi trường:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```
   - Nếu có lỗi "execution policy", chạy 1 lần:
     ```powershell
     Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
     ```
     (Trả lời `Y` khi hỏi). Sau đó chạy lại lệnh activate.
   - Khi thành công, dòng prompt sẽ có `(.venv)` ở đầu.
5. **(Quan trọng nếu bạn từng cài bản cũ)** Gỡ install cũ trước:
   ```powershell
   pip uninstall vn-business-os vn-one-person-company -y
   ```
   (Nếu báo "not found" — bỏ qua, bạn chưa cài bản nào.)

6. Cài thư viện:
   ```powershell
   pip install -e .
   ```
   (Đợi 3-5 phút — sẽ thấy nhiều dòng cài đặt)

7. Kiểm tra cài đặt:
   ```powershell
   vn-os --version
   ```
   Phải hiện: `vn-os, version 0.2.0` (hoặc cao hơn).

8. **Verify install trỏ đúng folder repo** (tránh lỗi "sửa code không có hiệu lực" sau này):
   ```powershell
   python -c "import json; from pathlib import Path; p = Path([d for d in __import__('site').getsitepackages() + [__import__('site').getusersitepackages()] if (Path(d) / 'vn_one_person_company-0.2.0.dist-info').exists()][0]) / 'vn_one_person_company-0.2.0.dist-info' / 'direct_url.json'; print(json.loads(p.read_text())['url'])"
   ```
   Phải hiện: `file:///F:/.work/vn-one-person-company` (đường dẫn repo bạn vừa giải nén).

   ❌ Nếu hiện đường khác (vd `file:///F:/OneDrive/.../vn-one-person-company`) → bạn còn install cũ. Quay lại bước 5, uninstall, install lại.

---

### Bước 6: Đăng ký DeepSeek + lấy API key (5 phút)

DeepSeek là dịch vụ AI giúp các phòng ban "suy nghĩ". Rẻ hơn Claude API ~10 lần, đủ free credit chạy hàng trăm task.

**Thao tác:**

1. Vào https://platform.deepseek.com → click **"Sign up"**
2. Đăng ký bằng email hoặc Google
3. Sau khi login → vào **"API Keys"** (menu bên trái)
4. Click **"Create new API key"** → đặt tên vd `vn-business-os`
5. **COPY KEY NGAY** (chỉ hiện 1 lần) → dán vào `F:\setup-keys.txt` cùng với key Obsidian
6. Key có dạng `sk-xxxxxxxxxxxxxxxxxxxx`

> ⚠️ **Bảo mật:** Key này cho phép gọi DeepSeek tốn tiền. **Không chia sẻ.** Nếu lỡ lộ → quay lại trang API Keys → Delete key cũ → tạo key mới.

> 💰 **Chi phí thực tế:** $5 free credit của DeepSeek đủ chạy ~200-300 task. Sau đó nạp thêm khoảng $5-10/tháng cho usage trung bình của 1 DN.

---

### Bước 6.5: Đăng ký Tavily (khuyến nghị — 3 phút)

Tavily là search engine để các phòng ban tra cứu **luật mới**, **đối thủ**, **dữ liệu địa phương** thật trên web. **Không có Tavily** → decision report vẫn ra nhưng chỉ dựa Brain + kiến thức training của LLM (có thể outdated).

**Thao tác:**

1. Vào https://app.tavily.com → click **"Sign up"** (đăng ký free bằng email/Google)
2. Sau khi login → bên trái chọn **"API Keys"**
3. Click **"Generate API Key"** → đặt tên vd `vn-business-os`
4. Copy key (dạng `tvly-xxxxxxxxxxxxxxxxxxxxxxxxx`) → dán vào `F:\setup-keys.txt` cùng các key khác

**Free tier:** 1000 lượt search/tháng. Đủ cho 1 DN dùng full pipeline ~50-80 task/tháng (mỗi task tốn 5-15 search).

> 💡 **Có thể skip nếu chỉ muốn test nhanh.** Bạn vẫn chạy được toàn bộ pipeline nhưng 4 tool research (`web_search`, `vn_law_search`, `vn_local_regulation`, `competitor_research`) sẽ bị skip. Có thể add key sau bất cứ lúc nào → sửa `.env` → restart Claude Desktop.

---

### Bước 7: Tạo file config (5 phút)

Đây là 2 file nhỏ để hệ thống biết DN của bạn ở đâu + dùng AI nào.

**7.1 — File `.env` trong vault:**

> 🚨 **CỰC KỲ QUAN TRỌNG:** `DEEPSEEK_API_KEY` là LLM provider chính. Thiếu → mọi task `vn_draft`/`vn_run`/`vn_meeting` sẽ báo lỗi `Method not found` (vì code fallback đến MCP sampling mà Claude Code tab không support).

Trong PowerShell, gõ (đổi `Sao Việt` thành tên vault của bạn):

```powershell
notepad "F:\vaults\Sao Việt\.env"
```

Notepad sẽ mở file rỗng. Paste nội dung sau:

```
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxx
TAVILY_API_KEY=tvly-xxxxxxxxxxxxxxxxxxxxxxxxx
```

→ Thay 2 key bằng key thật của bạn (lấy từ `F:\setup-keys.txt`).

→ Nếu chưa có Tavily key → để trống sau dấu `=` (vẫn chạy được, chỉ skip 4 tool research).

→ **Save** (Ctrl+S) → **Close**

**Verify .env load đúng:**

```powershell
Get-Content "F:\vaults\Sao Việt\.env"
```

→ Phải thấy 2 dòng key (không bị BOM, không thừa khoảng trắng).

**7.2 — File `.vncoderc` trong home folder:**

Trong PowerShell, paste cả block sau (toàn bộ, từ `@"` đến `"@`):

```powershell
@"
llm:
  primary: deepseek-v4-pro
  secondary: deepseek-v4-flash
  max_retries: 3
  max_tokens_per_task: 100000

meeting:
  max_debate_rounds: 1
  total_max: 3

translator_mode: final_only
"@ | Out-File -FilePath "$HOME\.vncoderc" -Encoding utf8
```

Nhấn Enter. Không có output gì — vậy là xong.

---

### Bước 8: Cài Claude Desktop + 2 MCP servers (5 phút)

Claude Desktop là app chat với AI — nơi bạn ra lệnh "soạn HD lao động", "phân tích chi nhánh"...

> 🎯 **QUAN TRỌNG — Dùng tab "Code", không dùng tab "Chat" hay "Cowork".**
> Claude Desktop có 3 tab: **Chat** | **Cowork** | **</> Code** (góc trên bên phải).
> - **Code tab** = Claude Code, timeout 10 phút, gọi được **mọi MCP tool** (kể cả debate đa phòng kéo dài 2-3 phút).
> - **Cowork tab** = timeout 60 giây — chỉ gọi được tool nhẹ (vn_status, đọc/sửa file). Task nặng (soạn doc, debate) sẽ **fail**.
>
> → **Sau khi cài xong, luôn click tab "</> Code" trước khi chat.**

**8.1 — Cài Claude Desktop:**

1. Vào https://claude.ai/download → tải Claude Desktop cho Windows
2. Cài đặt → Login bằng tài khoản Claude Pro của bạn
3. Mở Claude Desktop → **click tab "</> Code"** ở góc trên bên phải (cạnh Chat / Cowork)

**8.2 — Cài MCP Obsidian (kết nối Claude với vault Obsidian):**

Mở PowerShell, paste:

```powershell
$configPath = "$env:APPDATA\Claude\claude_desktop_config.json"

# Tạo file config nếu chưa có
if (!(Test-Path $configPath)) {
    New-Item -Path $configPath -ItemType File -Force | Out-Null
    '{"mcpServers": {}}' | Out-File -FilePath $configPath -Encoding utf8
}

# Mở file config trong Notepad
notepad $configPath
```

Notepad sẽ mở file `claude_desktop_config.json`. **Thay toàn bộ nội dung** bằng:

```json
{
  "mcpServers": {
    "mcp-obsidian": {
      "command": "npx",
      "args": ["-y", "mcp-obsidian"],
      "env": {
        "OBSIDIAN_API_KEY": "PASTE_OBSIDIAN_KEY_VAO_DAY",
        "OBSIDIAN_HOST": "127.0.0.1",
        "OBSIDIAN_PORT": "27124"
      }
    },
    "vn-business-os": {
      "command": "F:\\.work\\vn-one-person-company\\.venv\\Scripts\\vn-os-mcp.exe",
      "args": []
    }
  }
}
```

→ Thay `PASTE_OBSIDIAN_KEY_VAO_DAY` bằng API key Obsidian Local REST API (từ Bước 3.5)

→ Save (Ctrl+S) → Close

**8.3 — Restart Claude Desktop ĐÚNG CÁCH:**

> ⚠️ **CẢNH BÁO LỚN:** Click nút X (đóng cửa sổ) **KHÔNG quit** Claude Desktop — chỉ minimize xuống **system tray** (góc dưới phải màn hình). MCP server cũ vẫn chạy ngầm → mọi sửa code/config đều không có hiệu lực.

**Cách Quit chuẩn:**

1. Nhìn **góc dưới phải màn hình**, gần đồng hồ
2. Click mũi tên `^` "Show hidden icons" (nếu cần)
3. Tìm icon **Claude** (hình bông hoa cam)
4. **Right-click** icon Claude → chọn **"Quit"** (KHÔNG phải Close)

**Verify đã Quit hết (PowerShell):**

```powershell
Get-Process claude, vn-os-mcp -ErrorAction SilentlyContinue | Measure-Object | Select-Object -ExpandProperty Count
```

→ Phải in ra `0`. Nếu > 0 → còn process. Force kill:
```powershell
Get-Process claude, vn-os-mcp -ErrorAction SilentlyContinue | Stop-Process -Force
```

**Mở lại Claude Desktop:**

1. Mở Claude Desktop từ Start Menu
2. **Click tab "</> Code"** ở góc trên bên phải (cạnh Chat / Cowork)
3. **Quan trọng:** Obsidian app cũng phải đang chạy (vault Sao Việt đang mở). Nếu chưa → mở Obsidian.

---

### Bước 9: Verify mọi thứ chạy được (3 phút)

> Mở Claude Desktop → **click tab "</> Code"** → **"+ New session"** ở sidebar trái → cửa sổ chat mới hiện ra.

**9.1 — Test MCP Obsidian:**

Trong Claude Code session, gõ:

```
Liệt kê các file trong vault Obsidian của tôi
```

→ Claude phải gọi tool `obsidian_list_files_in_vault` và trả về danh sách. Nếu được → **Obsidian MCP OK**.

❌ Nếu lỗi `connection refused` → Obsidian không mở hoặc plugin Local REST API tắt. Kiểm tra lại Bước 3.

**9.2 — Test MCP vn-business-os:**

Trong Claude Code session, gõ:

```
Chạy vn_status với vault F:\vaults\Sao Việt
```

→ Claude gọi tool `vn_status`. Lần đầu sẽ báo lỗi `Brain dir not found` — bình thường, vì vault chưa khởi tạo. Nhưng nghĩa là MCP đã kết nối.

❌ Nếu lỗi `Method not found` → MCP vn-business-os chưa load. Restart Claude Desktop.

---

### ✅ Cài đặt xong!

Tới đây bạn đã có:

| Thành phần | Trạng thái |
|---|---|
| Python 3.12 + Node.js 20 | ✅ |
| Obsidian + plugin Local REST API | ✅ |
| Repo vn-business-os + thư viện Python | ✅ |
| DeepSeek API key trong `.env` | ✅ |
| Tavily API key trong `.env` (khuyến nghị) | ✅ |
| Config `.vncoderc` cho model | ✅ |
| Claude Desktop + 2 MCP servers | ✅ |
| Đã biết dùng tab **"</> Code"** trong Claude Desktop | ✅ |

**Bước tiếp theo:** Phần 2 — Khởi tạo doanh nghiệp (tạo Brain + áp pack ngành).

---

## 🏢 PHẦN 2 — KHỞI TẠO DOANH NGHIỆP (1 lần duy nhất per công ty, ~30 phút)

> Bước này tạo "bộ não" của doanh nghiệp — gồm 8 file thông tin (chiến lược, sản phẩm, ngân sách, nhân sự, luật, lịch sử quyết định, tình trạng, từ điển) và cấu trúc 13 phòng ban.
>
> Sau bước này, mỗi lần bạn chat với Claude, **AI đã biết doanh nghiệp bạn là ai, đang ở giai đoạn nào** — không phải nhập lại context mỗi lần.

---

### Bước 10: Tạo cấu trúc vault Obsidian (5 phút)

Vault Obsidian cần 5 folder chính:

```
F:\vaults\<Tên DN>\
├── 00-Brain/              ← 8 file thông tin DN (AI đọc trước mỗi task)
├── 00-Templates-Custom/   ← Template riêng của bạn (tùy chọn)
├── 01-Departments/        ← 13 phòng ban core + pack ngành
├── 02-Tasks/              ← Lịch sử mọi task CEO giao
├── 03-Outputs/            ← File .docx/.xlsx được sinh ra
└── 99-Archive/            ← Task cũ đã archive
```

**Cách 1 — Tự động (khuyến nghị):**

Trong **Claude Code session** (tab "</> Code" của Claude Desktop, sau khi đã setup MCP ở Bước 8), gõ:

```
Khởi tạo cấu trúc vault VN Business OS tại F:\vaults\<TênDN>.
Áp pack ngành: F&B (hoặc Retail / Tech-SaaS — chọn 1).
```

→ Claude sẽ gọi tool `vn_onboard` tự động tạo các folder + copy template.

**Cách 2 — Thủ công (nếu Cách 1 lỗi):**

1. Mở **PowerShell** (Win+R → `powershell`)
2. Paste (đổi `Sao Việt` thành tên vault của bạn):

```powershell
$vault = "F:\vaults\Sao Việt"
$repo = "F:\.work\vn-one-person-company"

# Tạo 5 folder chính
New-Item -ItemType Directory -Force -Path "$vault\00-Brain" | Out-Null
New-Item -ItemType Directory -Force -Path "$vault\00-Templates-Custom" | Out-Null
New-Item -ItemType Directory -Force -Path "$vault\01-Departments" | Out-Null
New-Item -ItemType Directory -Force -Path "$vault\02-Tasks" | Out-Null
New-Item -ItemType Directory -Force -Path "$vault\03-Outputs" | Out-Null
New-Item -ItemType Directory -Force -Path "$vault\99-Archive" | Out-Null

# Copy 8 file Brain template
Copy-Item "$repo\vault-template\00-Brain\*.md" -Destination "$vault\00-Brain\" -Force

# Copy 13 phòng ban core
Copy-Item "$repo\departments\*" -Destination "$vault\01-Departments\" -Recurse -Force

Write-Host "✓ Cấu trúc vault đã tạo xong tại $vault"
```

**Verify:**

Mở Obsidian, refresh (F5). Bạn sẽ thấy 5 folder bên trái + 8 file `.md` trong `00-Brain/`.

---

### Bước 11: Áp pack ngành (5 phút)

Pack ngành thêm các phòng ban đặc thù cho doanh nghiệp của bạn:

| Pack | Phòng ban thêm | Phù hợp với |
|---|---|---|
| **F&B** | 13-kitchen, 14-food-safety | Quán ăn / cafe / nhà hàng / quán bar |
| **Retail** | 13-warehouse, 14-logistics | Shop / e-commerce / D2C / dropshipping |
| **Tech-SaaS** | 13-engineering, 14-product-design, 15-data | Startup phần mềm / app / platform |
| *(không pack)* | Chỉ 13 phòng core | Freelance / agency / dịch vụ tư vấn |

**Áp pack qua PowerShell:**

```powershell
$vault = "F:\vaults\Sao Việt"
$repo = "F:\.work\vn-one-person-company"
$pack = "fnb"   # ← Đổi thành: fnb / retail / tech-saas

# Copy phòng ban đặc thù từ pack
Copy-Item "$repo\packs\$pack\departments\*" -Destination "$vault\01-Departments\" -Recurse -Force

# Áp brain template chuyên ngành (merge với template chung)
Copy-Item "$repo\packs\$pack\brain-template\*" -Destination "$vault\00-Brain\" -Force

Write-Host "✓ Đã áp pack $pack"
```

**Verify trong Obsidian:**

Folder `01-Departments/` giờ có 13-15 sub-folder (13 core + 2-3 từ pack).

---

### Bước 12: Fill 8 file Brain — Phỏng vấn với Claude (15 phút)

Đây là bước **quan trọng nhất**. Brain rỗng = AI không biết DN bạn → output lung tung. Brain đầy đủ = AI ra quyết định chuẩn xác.

**8 file cần fill (trong `00-Brain/`):**

| File | Nội dung | Bắt buộc? |
|---|---|---|
| `strategy.md` | Tầm nhìn 3-5 năm, ICP (khách hàng mục tiêu), USP, mục tiêu năm | ✅ Bắt buộc |
| `products.md` | Menu/sản phẩm + giá + margin | ✅ Bắt buộc |
| `state.md` | Giai đoạn (pre-seed/seed/growth/mature), runway, KPI hiện tại | ✅ Bắt buộc |
| `headcount.md` | Founding team + plan tuyển + phòng ban active | ✅ Bắt buộc |
| `budget.md` | Tổng ngân sách năm, CAPEX, OPEX | 🟡 Khuyên có |
| `laws.md` | Luật/quy định ngành cần tuân thủ | 🟡 Khuyên có |
| `decisions-log.md` | Nhật ký quyết định lớn (sẽ tự sinh khi dùng) | 🟢 Tự sinh |
| `glossary.md` | Từ điển thuật ngữ DN | 🟢 Tự sinh |

> 💡 **Cách làm:** Bạn tự đọc 16 câu hỏi dưới đây + tự gõ câu trả lời vào file Brain trong Obsidian. Quy trình thủ công nhưng **an toàn 100%** — bạn kiểm soát chính xác mọi thông tin DN của mình.
>
> *Tại sao không nhờ Claude tự fill?* — Brain là nền tảng AI dựa vào để ra mọi quyết định sau này. Tự fill đảm bảo data đúng 100% + bạn hiểu rõ hệ thống đang biết gì về DN.
>
> *Mẹo nhanh:* nếu lười, sau khi đọc xong 16 câu hỏi, bạn có thể chat với Claude Code: "Đây là câu trả lời của tôi: [paste 16 câu]. Generate giúp 8 file Brain theo format trong README-USER.md Bước 12.2, dùng obsidian_patch_content ghi vào vault."

**Bước 12.1 — Trả lời 16 câu hỏi (chuẩn bị nội dung)**

Mở **Notepad** (hoặc bất kỳ trình soạn thảo nào), tạo file tạm `brain-answers.txt`. Trả lời lần lượt 16 câu sau (cứ ghi gọn, sau này paste vào file thật):

**🎯 LƯỢT 1 — Chiến lược (4 câu):**

1. **Tầm nhìn 3-5 năm** — Doanh nghiệp bạn muốn đạt gì trong 3-5 năm tới? *(VD: "Trở thành chuỗi 5-10 chi nhánh cafe tầm trung tại TP.HCM")*
2. **ICP — Khách hàng mục tiêu** — Khách hàng lý tưởng là ai? Bao nhiêu tuổi? Thu nhập bao nhiêu? Pain point chính? *(VD: "Nhân viên văn phòng TP.HCM, 22-40 tuổi, thu nhập 10-30tr, ngại chờ >5 phút")*
3. **USP — Điểm khác biệt** — Bạn khác đối thủ ở chỗ nào? Tối đa 2 USP. *(VD: "Grab&go nhanh + hạt cà phê Việt chất lượng cao tầm trung")*
4. **Mục tiêu doanh thu năm đầu** — VND/năm? Bao nhiêu khách/ngày? AOV (giá trị trung bình 1 đơn) bao nhiêu? *(VD: "1.5-3 tỷ/năm, 80-150 ly/ngày, AOV 60-80k")*

**💰 LƯỢT 2 — Tài chính & quy mô (4 câu):**

5. **Vốn đầu tư ban đầu (CAPEX)** — Tổng vốn bạn có cho khởi nghiệp? Chi nhánh đầu cần bao nhiêu? *(VD: "1 tỷ tổng, 500-800tr cho chi nhánh đầu")*
6. **Nguồn vốn** — Tự có / vay / đồng sáng lập / nhà đầu tư? *(VD: "100% tự có")*
7. **Timeline khai trương** — Bao lâu nữa thì mở? *(VD: "1-3 tháng, đã có location")*
8. **Giai đoạn hiện tại** — Chọn 1 trong 5: `pre-seed` (chưa mở/ý tưởng), `seed` (mở rồi, đang test), `growth` (đang mở rộng), `mature` (ổn định), `pivot` (đang đổi hướng). *(VD: "pre-seed")*

**🍳 LƯỢT 3 — Sản phẩm & nhân sự (4 câu):**

9. **Menu/sản phẩm chính** — 5-10 SKU chính + giá + biên lợi nhuận ước. *(VD: "Cà phê đen 32k margin 70%, cà phê sữa 38k margin 70%, bánh mì 32k margin 50%")*
10. **Supplier chính** — Mua nguyên liệu/sản phẩm ở đâu? *(VD: "Hạt từ Cau Đất / Buôn Mê / Sơn La. Bánh từ supplier địa phương")*
11. **Nhân sự chi nhánh/team đầu** — Bao nhiêu người? Vai trò gì? Lương bao nhiêu? *(VD: "5-7 người: 1 quản lý 12-15tr, 1 lead barista 9-11tr, 1-2 barista 7-9tr, 2-3 phục vụ 6-8tr")*
12. **Founding team hiện tại** — Bạn solo hay có co-founder? *(VD: "Solo founder, chưa có co-founder")*

**📊 LƯỢT 4 — KPI & vận hành (4 câu):**

13. **KPI ưu tiên track hàng tuần** — Số ly/ngày? AOV? Food cost%? Customer return rate? Revenue/m²? *(VD: "Số ly/ngày + AOV")*
14. **Kế hoạch nhượng quyền (franchise)** — Có / Không / Sau Y3 / Chưa quyết. *(VD: "Có, sau khi prove model 2-3 chi nhánh self-owned")*
15. **Compliance — luật cần tuân thủ** — Liệt kê các quy định ngành. *(VD: "VSATTP NĐ 15/2018, PCCC TCVN 5738:2021, Bộ luật Lao động 2019, Luật BVNTD 2023")*
16. **Brand identity** — Tên thương hiệu + slogan (nếu có) + positioning. *(VD: "Tên: Sao Việt. Slogan: 'Hạt Việt đậm. Gọn trong tay.' Positioning: cafe Việt nhanh-tiện cho văn phòng")*

---

**Bước 12.2 — Mở 8 file template trong Obsidian + paste câu trả lời**

Trong Obsidian (vault Sao Việt đang mở), mở từng file trong folder `00-Brain/` và điền theo hướng dẫn dưới.

⚠️ **CỰC KỲ QUAN TRỌNG về format heading** — Hệ thống parser yêu cầu heading **CHÍNH XÁC**, không có suffix. Sai 1 chữ là parser không đọc được.

---

**📄 File 1: `strategy.md`** *(dùng câu 1, 2, 3, 4)*

Mở file → xóa toàn bộ → paste:

```markdown
---
type: brain
section: strategy
aliases: ["Chiến lược", "Strategy", "Tầm nhìn"]
last_updated: 2026-05-08
---
# Chiến lược DN — <Tên DN>

## Tầm nhìn
<Trả lời câu 1 — không thêm ngoặc kép, không thêm "(3-5 năm)" vào heading>

## Sứ mệnh
<1-2 câu mô tả lý do tồn tại của DN>

## Khách hàng mục tiêu (ICP)
- **Phân khúc:** <từ câu 2>
- **Tuổi:** <từ câu 2>
- **Thu nhập:** <từ câu 2>
- **Hành vi:** <từ câu 2>
- **Pain point:** <từ câu 2>

## Mục tiêu năm đầu
- Doanh thu: <từ câu 4>
- Số khách/ngày: <từ câu 4>
- AOV: <từ câu 4>

## Định vị thương hiệu
<1 câu positioning, từ câu 16 nếu có>

## USP
<từ câu 3, ghi 1-2 dòng bullet>
```

✅ **Heading bắt buộc đúng:** `## Tầm nhìn` và `## Khách hàng mục tiêu (ICP)` — viết y hệt.

---

**📄 File 2: `state.md`** *(dùng câu 8)*

```markdown
---
type: brain
section: state
last_updated: 2026-05-08
---
# Trạng thái DN hiện tại

## Giai đoạn
[<từ câu 8 — chọn 1: pre-seed / seed / growth / mature / pivot>]

<1-2 đoạn mô tả thêm về tình trạng hiện tại>

## Quý hiện tại
- Doanh thu: <số nếu có, hoặc "0 (chưa mở)">
- KPI chính: <từ câu 13>
- Vấn đề nóng: <liệt kê 2-3 vấn đề lớn nhất>

## Runway / sức khoẻ tài chính
- Tiền mặt: <từ câu 5>
- Burn/tháng: <ước>
- Runway: <số tháng>
```

✅ **Bắt buộc:** dòng `[pre-seed]` (hoặc giai đoạn khác trong dấu ngoặc vuông) — parser tìm chuỗi này.

---

**📄 File 3: `products.md`** *(dùng câu 9)*

```markdown
---
type: brain
section: products
last_updated: 2026-05-08
---
# Sản phẩm — <Tên DN>

## Menu chính

| Code | Tên | price | margin | status |
|---|---|---|---|---|
| CFD | Cà phê đen phin | 32000 | 70 | active |
| CFS | Cà phê sữa phin | 38000 | 70 | active |
| BX | Bạc xỉu | 42000 | 65 | active |
<thêm các SKU từ câu 9, mỗi dòng 1 SKU>

## Supplier
<từ câu 10>
```

✅ **Bắt buộc:** Table phải có **đúng 5 cột với header `Code | Tên | price | margin | status`**. Code viết HOA (vd `CFD`, không `cfd`). Price ghi số nguyên (32000, không 32k).

---

**📄 File 4: `headcount.md`** *(dùng câu 11, 12)*

```markdown
---
type: brain
section: headcount
last_updated: 2026-05-08
---
# Nhân sự & Phòng ban — <Tên DN>

## Founding team
- CEO: <tên + email từ câu 12>
<liệt kê co-founder nếu có>

## Phòng ban active

- 01-governance — <ai phụ trách, vd "CEO direct">
- 02-strategy — CEO direct
- 03-finance — CEO direct
- 04-people — CEO direct
- 05-operations — CEO direct
- 06-sales — <vai trò>
- 07-marketing — <vai trò>
- 08-customer — <vai trò>
- 10-training — <vai trò>
- 11-reporting — <vai trò>
- 12-growth — <vai trò>
<thêm phòng pack ngành nếu có:>
- 13-kitchen — <F&B pack>
- 14-food-safety — <F&B pack>

## Kế hoạch nhân sự chi nhánh đầu
<từ câu 11>
```

✅ **Bắt buộc:** mỗi phòng ban là 1 dòng bullet bắt đầu bằng `- <số 2 chữ số>-<tên>` (vd `- 01-governance`). Parser dùng regex tìm pattern này.

---

**📄 File 5: `budget.md`** *(dùng câu 5)*

```markdown
---
type: brain
section: budget
last_updated: 2026-05-08
---
# Ngân sách — <Tên DN>

Tổng ngân sách: <số nguyên VND, vd "1000000000" cho 1 tỷ>

## CAPEX (chi nhánh đầu)
<liệt kê các hạng mục từ câu 5>

## OPEX (vận hành tháng)
<liệt kê thuê, lương, COGS, điện nước...>

## Buffer / Runway
<tính dựa trên vốn còn lại>
```

✅ **Bắt buộc:** Dòng `Tổng ngân sách: <số>` viết y hệt (parser tìm pattern này). Số ghi nguyên, không có dấu phẩy/chấm/từ "tỷ".

---

**📄 File 6: `laws.md`** *(dùng câu 15)*

```markdown
---
type: brain
section: laws
last_updated: 2026-05-08
---
# Luật & Compliance — <Tên DN>

## Nhóm 1: Đăng ký kinh doanh
- [ ] GPKD hộ cá thể hoặc công ty TNHH
- [ ] Mã số thuế

## Nhóm 2: Compliance ngành
<từ câu 15, liệt kê>

## Nhóm 3: Lao động
- Bộ luật Lao động 2019
- BHXH/BHYT 23.5%

## Nhóm 4: Thuế
- VAT 8% (F&B, ưu đãi 2024-2026)
- TNDN 20%
```

---

**📄 File 7: `decisions-log.md`** — *(để trống lúc đầu, AI tự ghi sau khi chạy task)*

```markdown
---
type: brain
section: decisions
last_updated: 2026-05-08
---
# Nhật ký quyết định

> Append-only. Mỗi quyết định lớn được ghi ở đây.

## [2026-05-08] Khởi tạo Brain DN
**Quyết định:** Setup VN Business OS với industry pack <ngành của bạn>.
**Người ra quyết định:** CEO
```

---

**📄 File 8: `glossary.md`** — *(template tối thiểu, AI sẽ thêm thuật ngữ mới khi gặp)*

```markdown
---
type: brain
section: glossary
last_updated: 2026-05-08
---
# Từ điển thuật ngữ

## Tài chính
- **AOV**: Giá trị trung bình một đơn hàng (Average Order Value).
- **CAPEX**: Chi phí đầu tư ban đầu, mua tài sản dài hạn.
- **OPEX**: Chi phí vận hành hàng tháng.
- **COGS**: Giá vốn hàng bán.
- **Break-even**: Điểm hòa vốn.
- **Runway**: Số tháng trụ được nếu doanh thu = 0.

## Pháp lý VN
- **VSATTP**: Vệ sinh An toàn Thực phẩm. NĐ 15/2018/NĐ-CP.
- **PCCC**: Phòng cháy chữa cháy. TCVN 5738/2021.
- **GPKD**: Giấy phép kinh doanh.
- **VAT**: Thuế giá trị gia tăng.
- **TNDN**: Thuế thu nhập doanh nghiệp 20%.
- **TNCN**: Thuế thu nhập cá nhân.
- **ICP**: Hồ sơ khách hàng lý tưởng (Ideal Customer Profile).
```

✅ **Bắt buộc:** Mỗi thuật ngữ format `- **Term**: định nghĩa` (có dấu hai chấm `:` ngay sau dấu `**` đóng). Không dùng em dash `—`.

---

**Bước 12.3 — Save tất cả file**

Trong Obsidian, mỗi file sau khi paste content + thay placeholder, nhấn **Ctrl+S** để save.

Nếu Obsidian có config "Auto-save" (mặc định bật) → file tự save khi chuyển tab.

---

### Bước 13: Verify Brain đã đầy đủ (2 phút)

Trong **Claude Code session**, gõ:

```
Chạy vn_status với vault F:\vaults\Sao Việt
```

**Kết quả mong đợi:**

```json
{
  "vault": "F:\\vaults\\Sao Việt",
  "icp": "- Phân khúc: Nhân viên văn phòng TP.HCM\n- Tuổi: 22-40...",   ✅ KHÔNG được là "(chưa điền)"
  "vision": "Trở thành chuỗi 5-10 chi nhánh...",                          ✅ KHÔNG được là "(chưa điền)"
  "products": 10,                                                          ✅ Phải > 0
  "active_departments": ["01-governance", "02-strategy", ...],            ✅ Phải có ≥ 13 entries
  "state": "pre-seed",                                                    ✅ KHÔNG được là "unknown"
  "tools_live": ["web_search", "vn_law_search", ...],                     ✅ 6 tools nếu có Tavily key
  "packs": []
}
```

**Nếu thấy:**

- `vision: "(chưa điền)"` → Brain chưa fill hoặc heading sai format. Quay lại Bước 12.
- `products: 0` → File `products.md` thiếu table với schema `| Code | Tên | price | margin | status |`.
- `state: "unknown"` → File `state.md` thiếu dòng `[pre-seed]` (hoặc giai đoạn khác trong ngoặc vuông).
- `active_departments: []` → File `headcount.md` thiếu bullet list phòng ban dạng `- 01-governance`.

---

### ✅ Khởi tạo xong!

Tới đây bạn có:

| Thành phần | Trạng thái |
|---|---|
| Vault với 5 folder chuẩn | ✅ |
| 13 phòng ban core + pack ngành | ✅ |
| 8 file Brain đầy đủ thông tin DN | ✅ |
| `vn_status` báo các trường đều có data | ✅ |

**Bước tiếp theo:** Phần 3 — Sử dụng hàng ngày.

---

## 💼 PHẦN 3 — SỬ DỤNG HÀNG NGÀY

> Đây là phần bạn sẽ đọc đi đọc lại nhiều nhất. Phần 1-2 chỉ làm 1 lần, **Phần 3 là cách bạn vận hành DN hàng ngày**.

---

### 📌 Quy tắc duy nhất — Luôn dùng tab Code

Mở Claude Desktop → click **"</> Code"** ở góc trên bên phải → **"+ New session"**.

Trong session Code tab:
- ✅ Mọi MCP tool đều gọi được trực tiếp (timeout 10 phút)
- ✅ Không cần phân biệt "task nhẹ" vs "task nặng"
- ✅ Không cần mở PowerShell riêng

> 🚫 **Đừng dùng tab Cowork để chạy task nặng** (vd "Soạn HĐLĐ", "Phân tích chi nhánh"). Cowork có timeout 60s → debate đa phòng (60-180s) sẽ fail. Để dành Cowork cho việc nhẹ như "tóm tắt vault" hoặc đọc/sửa file.

**Bảng minh hoạ — cùng 1 task, 2 tab khác nhau:**

| Task của bạn | Code tab | Cowork tab |
|---|---|---|
| "Tóm tắt vault, DN tôi đang giai đoạn nào?" | ✅ OK | ✅ OK |
| "Mở file decision-report.md task X" | ✅ OK | ✅ OK |
| "Sửa file budget.md, thêm 20tr chi marketing" | ✅ OK | ✅ OK |
| "Soạn JD barista" | ✅ OK (~30s) | ⚠️ Borderline |
| "Soạn HĐLĐ store manager 13tr" | ✅ OK (~30s) | ⚠️ Borderline |
| "Brainstorm slogan + visual identity" | ✅ OK (~3-5 phút) | ❌ Timeout |
| "Phân tích nên mở chi nhánh 2 ở quận nào" | ✅ OK (~5-10 phút) | ❌ Timeout |
| "Lập kế hoạch chiến dịch QC Tết 50tr" | ✅ OK (~5-10 phút) | ❌ Timeout |

→ **Mặc định dùng Code tab.** Cowork chỉ nên dùng khi đang đa nhiệm với Chat tab và task chắc chắn nhẹ.

---

### 🎬 Workflow chuẩn — 2 con đường

Trong Code tab, bạn cứ chat tự nhiên. Claude tự phân loại task và chọn 1 trong 2 con đường:

#### Đường A — Fast path (`vn_draft`) cho doc boilerplate

Áp dụng cho: HĐLĐ, JD, nội quy, phiếu thu, SOP đơn giản, thư mời họp...

**Bạn:**
> Soạn JD nhân viên pha chế cho Sao Việt, lương 8tr/tháng, Q1 TPHCM.

**Claude:** (tự gọi `vn_draft`, ~10-30s)
> Đã tạo draft tại `02-Tasks/2026-MM-DD-HHMM-jd-pha-che/draft.md`. Mở Obsidian xem. Tóm tắt: yêu cầu 6 tháng KN espresso, ca 8h x 6 ngày/tuần, BHXH theo Luật LĐ 2019...

→ **1 lần gọi, ra ngay file.** Không qua debate, không có decision report. Phù hợp cho doc đã có template chuẩn.

---

#### Đường B — Full pipeline 5 stage cho quyết định chiến lược

Áp dụng cho: quyết định lớn (mở chi nhánh, ngân sách quảng cáo, rebrand), doc rủi ro pháp lý cao, brainstorm cần đa góc nhìn.

**5 stage tuần tự:**

| # | Tool MCP | Output | Thời gian |
|---|---|---|---|
| 1 | `vn_run(brief, vault)` | `01-routing.md`, `02-context.md`, (có thể) `03-clarification.md` | 20-50s |
| 2 | `vn_resume(task_folder)` (nếu cần) | `03-clarification-answered.md` | <10s |
| 3 | `vn_meeting(task_folder)` | `04..06-meeting-*.md`, **`07-decision-report.md`** ← Stop 1 | 60-180s |
| 4 | `vn_approve(task_folder)` | **`08-execution-plan.md`** ← Stop 2 | 10-30s |
| 5 | `vn_execute(task_folder)` | File `.docx`/`.xlsx` trong `03-Outputs/<task>/` | 10-30s |

**Ví dụ thực tế:**

**Bạn:**
> Tôi muốn phân tích nên mở chi nhánh 2 Sao Việt ở Q1 hay Q3.

**Claude:** (gọi `vn_run` ~30s)
> Đã tạo task folder `02-Tasks/2026-MM-DD-HHMM-chi-nhanh-2/`. Có 5 câu clarification cần bạn trả lời trong `03-clarification.md` (mở Obsidian xem). Tôi đợi.

**Bạn:** (mở Obsidian, trả lời 5 câu, save Ctrl+S)
> Xong rồi, tiếp đi.

**Claude:** (gọi `vn_resume` → `vn_meeting` ~2-3 phút)
> Decision report đã sinh tại `07-decision-report.md`. Tóm tắt: hệ thống khuyến nghị **Q3** với CAPEX 650tr, payback 18 tháng. Lý do chính: ... Có 3 cảnh báo: ...
>
> **Stop 1 — bạn duyệt:** mở `07-decision-report.md` đọc kỹ. Đồng ý → tôi chạy `vn_approve`. Muốn sửa → sửa thẳng file rồi báo tôi.

**Bạn:**
> OK, approve đi.

**Claude:** (gọi `vn_approve` ~30s → `vn_execute` ~15s)
> Execution plan tại `08-execution-plan.md`. File `.docx` deliverable cuối cùng tại `03-Outputs/chi-nhanh-2/phan-tich-vi-tri.docx`. Mở xem.

---

### 🛑 Stop 1 + Stop 2 — Tại sao quan trọng

Hệ thống có **2 điểm dừng cố ý** để bạn (CEO) duyệt:

- **Stop 1 — sau `vn_meeting`**: bạn xem `07-decision-report.md` trước khi approve. Đây là cơ hội **từ chối / sửa quyết định** trước khi hệ thống render docx.
- **Stop 2 — sau `vn_approve`**: bạn xem `08-execution-plan.md` trước khi execute. Đây là cơ hội xem **plan triển khai chi tiết**, sửa trước khi tốn template render.

→ **Đừng bỏ qua 2 điểm dừng này.** Nếu hệ thống đề xuất tệ → sửa thẳng file trong Obsidian, save, rồi báo Claude tiếp stage sau.

**Files xuất hiện sau mỗi stage:**

| Stage | File mới trong task folder | Bạn làm gì |
|---|---|---|
| `vn_run` | `00-brief.md`, `01-routing.md`, `02-context.md`, có thể `03-clarification.md` | Nếu có `03-clarification.md` → mở, trả lời, save |
| `vn_resume` | `03-clarification-answered.md` | (tự động) |
| `vn_meeting` | `04..06-meeting-*.md`, `07-decision-report.md` | **Mở `07-decision-report.md` đọc + duyệt** |
| `vn_approve` | `08-execution-plan.md` | Đọc plan, OK chưa? |
| `vn_execute` | `03-Outputs/<task>/<file>.docx` | **Mở file .docx → deliverable cuối cùng** |

---

### 📖 Cách review decision report

File `07-decision-report.md` có cấu trúc chuẩn:

```markdown
# Báo cáo quyết định: <chủ đề>

## 📌 Tóm lại (đọc 30 giây)
- 3-5 dòng tóm tắt cho CEO
- Khuyến nghị chính

## Khuyến nghị
**Tiến hành / Tiến hành nhưng có điều chỉnh / Không tiến hành** — <giải thích>

## Phân tích chi tiết
### Mỗi bộ phận nói gì
<phòng Marketing nói..., phòng Tài chính nói..., ...>

### Tranh luận Ủng hộ vs Phản đối
| Phe | Luận điểm | Dẫn nguồn |

### 3 góc nhìn (Tăng trưởng / Thận trọng / Cân bằng)

## Việc cần làm ngay (Action items)
| # | Việc | Ai | Hạn | Chi phí |

## Cột mốc đo hiệu quả
| Tuần X | KPI | Ngưỡng | Hành động nếu fail |

## Câu hỏi cần CEO quyết
A. ...  B. ...  C. ...  D. ...

## ⚠️ Cảnh báo: Claims thiếu trích nguồn
<liệt kê các claim cần verify>
```

**Cách đọc nhanh (5 phút):**

1. Đọc **TL;DR** ở đầu (30 giây)
2. Đọc **Khuyến nghị** (xem hệ thống bảo "Tiến hành" hay "Không")
3. Scan **Việc cần làm ngay** (có item nào quá đắt hay quá gấp không?)
4. Đọc **Cảnh báo Claims thiếu trích nguồn** — nếu có số liệu quan trọng → tự verify
5. Trả lời **Câu hỏi CEO quyết** (A/B/C/D) → ghi vào file decision-log hoặc edit thẳng file decision-report

**Khi nào KHÔNG nên approve:**

- 🔴 Khuyến nghị "Tiến hành" nhưng claims thiếu citation cho số liệu lớn (vd: "doanh thu sẽ tăng 30%" không có nguồn)
- 🔴 Action items có chi phí vượt budget
- 🔴 Phe Phản đối có argument mạnh mà phe Ủng hộ chưa rebuttal được
- 🔴 Bạn cảm thấy "không hợp lý" — instinct của founder thường đúng

→ Edit thẳng `07-decision-report.md` (sửa khuyến nghị, thêm note), rồi chạy `approve` sau.

---

### ⏱️ Bảng thời gian ước tính (Claude Code tab)

| Tool | Thời gian thực tế |
|---|---|
| `vn_status` | < 1 giây |
| Đọc/sửa file (obsidian_*) | 1-5 giây |
| `vn_draft` | 10-30 giây |
| `vn_run` (1 task SIMPLE) | 20-50 giây |
| `vn_run` (cần clarification) | 20-50 giây + thời gian bạn trả lời |
| `vn_resume` | <10 giây |
| `vn_meeting` (DeepSeek v4-pro) | 1-3 phút |
| `vn_approve` | 10-30 giây |
| `vn_execute` (render docx) | 10-30 giây |
| **Tổng pipeline 1 task SIMPLE** | **3-5 phút** |
| **Tổng pipeline 1 task có clarification** | **5-10 phút** |

→ **Nếu chậm hơn benchmark này nhiều** (vd meeting > 10 phút) → có thể bị treo. Trong session Code, gõ `/abort`, kiểm tra Obsidian xem file nào đã tạo, retry từ stage gần nhất.

---

### 🔄 Quy trình "Một ngày làm việc với VN OS"

Đây là pattern bạn sẽ làm mỗi ngày khi đã quen — **tất cả trong 1 tab Code, không cần switch app.**

**Sáng (5 phút):**
1. Mở Claude Desktop → tab Code → **+ New session**
2. Gõ: "Vault Sao Việt có gì mới? KPI tuần này?"
3. Claude tự gọi `vn_status` + list tasks → tóm tắt focus hôm nay

**Khi có task lớn (3-10 phút):**
1. Trong session Code đang mở, gõ tự nhiên: "Soạn HĐLĐ cho store manager 13tr"
2. Claude tự chọn Fast path (`vn_draft`) hoặc Full pipeline (`vn_run → meeting → ...`)
3. Đợi (đi việc khác — vẫn ở trong cùng 1 session, không cần PowerShell)
4. Claude báo "xong" → mở Obsidian xem file deliverable

**Cuối tuần (10 phút):**
1. Trong Code session: "Liệt kê quyết định lớn tuần này trong 02-Tasks/"
2. "Update `00-Brain/decisions-log.md` với 3 quyết định quan trọng nhất"
3. Claude tự sửa file qua Obsidian MCP

---

## 🔧 PHẦN 4 — KHẮC PHỤC LỖI THƯỜNG GẶP

### 🩺 Health-check 30 giây (chạy khi nghi ngờ có vấn đề)

Mở **PowerShell**, paste cả block sau:

```powershell
Write-Host "`n=== VN OS Health Check ===" -ForegroundColor Cyan

Write-Host "`n[1/5] Python version:" -ForegroundColor Yellow
python --version

Write-Host "`n[2/5] Package install location:" -ForegroundColor Yellow
python -c "import json; from pathlib import Path; p = Path([d for d in __import__('site').getsitepackages() + [__import__('site').getusersitepackages()] if (Path(d) / 'vn_one_person_company-0.2.0.dist-info').exists()][0]) / 'vn_one_person_company-0.2.0.dist-info' / 'direct_url.json'; print(json.loads(p.read_text())['url'])"

Write-Host "`n[3/5] Claude Desktop processes:" -ForegroundColor Yellow
(Get-Process claude -ErrorAction SilentlyContinue | Measure-Object).Count

Write-Host "`n[4/5] vn-os-mcp processes:" -ForegroundColor Yellow
(Get-Process vn-os-mcp -ErrorAction SilentlyContinue | Measure-Object).Count

Write-Host "`n[5/5] Vault .env file:" -ForegroundColor Yellow
$envFile = Read-Host "  Nhập vault path (vd F:\vaults\Sao Việt)"
if (Test-Path "$envFile\.env") {
    Get-Content "$envFile\.env" | ForEach-Object { if ($_ -match "^DEEPSEEK|^TAVILY") { ($_ -split "=")[0] + "=" + (($_ -split "=")[1].Substring(0,[Math]::Min(8,($_ -split "=")[1].Length))) + "..." } }
} else { Write-Host "  ❌ .env not found!" -ForegroundColor Red }
```

**Kết quả mong đợi:**
- [1/5] Python 3.11+ hoặc 3.12+
- [2/5] `file:///F:/.work/vn-one-person-company` (đường repo thực tế)
- [3/5] 1-12 (Claude Desktop đang chạy)
- [4/5] 1-3 (MCP đang chạy — nhiều process bình thường nếu mở nhiều session)
- [5/5] `DEEPSEEK_API_KEY=sk-xxxxx...` (có key, không rỗng)

Nếu mục nào sai → tìm "Lỗi" tương ứng dưới đây.

---

### Lỗi 1: Tool MCP timeout / không phản hồi

**Triệu chứng:** Claude gọi `vn_meeting` nhưng > 5 phút không trả về.

**Cách fix:**
1. Kiểm tra bạn đang ở tab **"</> Code"** chưa? Nếu đang ở **Cowork** → switch sang Code.
2. Mở Obsidian, vào `02-Tasks/<task_folder>/` xem file nào đã sinh:
   - Có `04-meeting-r1-perspectives.md` nhưng chưa có `07-decision-report.md` → đang chạy meeting, đợi thêm.
   - Đã có `07-decision-report.md` → meeting xong, bảo Claude "đã thấy decision report, tiếp `vn_approve`".
3. Nếu thực sự treo → trong session Code gõ `/abort`, rồi retry stage.

### Lỗi 2: `vn_status` báo `error: Brain dir not found`

**Triệu chứng:** `{"error": "...00-Brain not found..."}`

**Cách fix:**
- Vault path sai → check spelling, đặc biệt dấu khoảng trắng (`"F:\vaults\Sao Việt"` phải có ngoặc kép).
- Vault chưa onboard → chạy `vn_onboard` (Bước 10 Cách 1).

### Lỗi 3: `tools_skipped` chứa `web_search / vn_law_search`

**Triệu chứng:** vn_status báo 4 tools bị skip vì thiếu `TAVILY_API_KEY`.

**Cách fix:**
1. Đăng ký Tavily free tại https://app.tavily.com → Settings → API Keys → tạo key (dạng `tvly-xxxxx`).
2. Mở `F:\vaults\<TênDN>\.env`, thêm dòng:
   ```
   TAVILY_API_KEY=tvly-xxxxxxxxxxx
   ```
3. Restart Claude Desktop (đóng hoàn toàn → mở lại).
4. Test: `vn_status` → `tools_live` phải có 6 tools.

> 💡 **Không có Tavily key vẫn dùng được** — chỉ là decision report không có research live (luật mới, đối thủ thực tế). Hệ thống vẫn dùng Brain + LLM knowledge để debate.

### Lỗi 4: `Method not found` khi gọi vn_draft / vn_run / vn_meeting

Có **2 nguyên nhân khác nhau** cho cùng error message:

#### 4.A — MCP server chưa load tool

**Triệu chứng:** Claude báo "I don't have access to vn_status tool" hoặc Method not found ở **mọi tool** vn_*.

**Cách fix:**
1. Check `claude_desktop_config.json` có entry `vn-business-os` không:
   ```powershell
   notepad "$env:APPDATA\Claude\claude_desktop_config.json"
   ```
2. Đường dẫn `vn-os-mcp.exe` đúng chưa: `F:\\.work\\vn-one-person-company\\.venv\\Scripts\\vn-os-mcp.exe` (escape dấu `\` thành `\\`).
3. **Quit Claude Desktop ĐÚNG CÁCH** từ tray (xem Bước 8.3) — KHÔNG chỉ đóng cửa sổ.

#### 4.B — Thiếu DEEPSEEK_API_KEY (LLM sampling unavailable)

**Triệu chứng:** `vn_status` chạy OK, nhưng `vn_draft` / `vn_run` / `vn_meeting` báo `Method not found`.

**Root cause:** Code fallback đến MCP sampling khi không có `DEEPSEEK_API_KEY` / `ANTHROPIC_API_KEY`. Nhưng Claude Code tab KHÔNG implement MCP sampling protocol → báo `Method not found`.

**Cách fix:**
1. Mở `F:\vaults\<TênDN>\.env`, đảm bảo có dòng:
   ```
   DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxx
   ```
2. **Verify key load đúng**: Trong Claude Code chat:
   > Gọi vn_status với vault F:\vaults\<TênDN>
   → Field `tools_live` phải có `industry_benchmark`, `tax_calculator`. Nếu thiếu cả 2 → `.env` chưa load.
3. **Quit + restart Claude Desktop** từ tray (Bước 8.3) để MCP server pick up env vars mới.

### Lỗi 4.5: Sửa code nhưng MCP không pick up

**Triệu chứng:** Sửa file `.py` trong repo xong, restart Claude Desktop, gọi tool — vẫn dùng code cũ.

**Root cause:** Process `vn-os-mcp.exe` cũ còn chạy ngầm (Claude Desktop khi "close" chỉ minimize tray).

**Cách fix:**
```powershell
# 1. Kill mọi MCP process cũ
Get-Process vn-os-mcp -ErrorAction SilentlyContinue | Stop-Process -Force

# 2. Quit Claude Desktop từ tray (right-click icon → Quit)

# 3. Verify
Get-Process claude, vn-os-mcp -ErrorAction SilentlyContinue | Measure-Object | Select-Object -ExpandProperty Count
# → phải là 0

# 4. Mở lại Claude Desktop → click tab "</> Code"
```

### Lỗi 4.6: Sửa code không có hiệu lực vì install trỏ folder khác

**Triệu chứng:** Sửa file trong `F:\.work\vn-one-person-company\` nhưng MCP server vẫn load code cũ từ folder khác (vd OneDrive copy).

**Cách kiểm tra:**
```powershell
python -c "import json; from pathlib import Path; p = Path([d for d in __import__('site').getsitepackages() + [__import__('site').getusersitepackages()] if (Path(d) / 'vn_one_person_company-0.2.0.dist-info').exists()][0]) / 'vn_one_person_company-0.2.0.dist-info' / 'direct_url.json'; print(json.loads(p.read_text())['url'])"
```

Nếu output **không phải** `file:///F:/.work/vn-one-person-company` → đang load từ folder khác.

**Cách fix:**
```powershell
# Gỡ install cũ
pip uninstall vn-business-os vn-one-person-company -y

# Kill MCP process (giữ file exe không bị lock)
Get-Process vn-os-mcp -ErrorAction SilentlyContinue | Stop-Process -Force

# Cài lại từ đúng folder
cd "F:\.work\vn-one-person-company"
pip install -e .

# Quit + restart Claude Desktop từ tray
```

### Lỗi 5: DeepSeek lỗi `API key invalid`

**Triệu chứng:** `vn_run` / `vn_draft` báo `Authentication failed`.

**Cách fix:**
1. Mở `F:\vaults\<TênDN>\.env`, kiểm tra `DEEPSEEK_API_KEY=sk-...` có đúng key không.
2. Vào https://platform.deepseek.com → API Keys → kiểm tra key còn active không, có credit không.
3. Sửa lại key → save .env → restart Claude Desktop.

### Lỗi 6: Obsidian MCP `connection refused`

**Triệu chứng:** `obsidian_list_files_in_vault` báo lỗi connection.

**Cách fix:**
1. Obsidian app phải đang chạy (mở vault).
2. Plugin Local REST API phải Enabled (Settings → Community plugins).
3. OBSIDIAN_API_KEY trong `claude_desktop_config.json` đúng chưa? Lấy lại từ Settings → Local REST API → API Key.

### Lỗi 7: `pip install -e .` báo lỗi

**Triệu chứng:** Bước 5 fail với `error: subprocess-exited-with-error`.

**Cách fix:**
1. Python version ≥ 3.11 chưa? `python --version` check.
2. venv đã activate chưa? Prompt phải có `(.venv)` ở đầu.
3. Nếu lỗi `Microsoft Visual C++ 14.0 required` → cài [VC++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/).

---

## 💡 PHẦN 5 — MẸO DÙNG TỐT NHẤT

### Mẹo 1: Brain càng đầy đủ, decision càng chuẩn

Mỗi câu trong Brain bạn fill → Claude/DeepSeek dùng để debate. Brain rỗng = AI "đoán" → output chung chung. Đầu tư 30 phút fill Brain kỹ = tiết kiệm hàng giờ sửa decision report sai sau này.

### Mẹo 2: Update Brain mỗi tháng

Kết thúc mỗi tháng, mở 8 file Brain, cập nhật:
- `state.md` — doanh thu thực tế tháng vừa qua, vấn đề nóng mới
- `budget.md` — chi thực tế vs ngân sách
- `decisions-log.md` — append các quyết định lớn trong tháng

Brain "sống" → mỗi task mới sẽ reflect tình hình DN hiện tại, không phải state lúc onboard.

### Mẹo 3: Brief càng cụ thể, output càng tốt

❌ Brief tệ: "Soạn JD nhân viên"
✅ Brief tốt: "Soạn JD nhân viên pha chế cho Sao Việt, lương 8tr/tháng Q1 TPHCM, yêu cầu 6 tháng KN máy espresso, ca 8h x 6 ngày/tuần, BHXH theo Luật LĐ 2019, ưu tiên ứng viên biết latte art"

Brief tốt = giảm số câu clarification = output ra đúng ý ngay lần đầu.

### Mẹo 4: Dùng `vn_draft` cho doc đơn giản, full pipeline cho quyết định lớn

| Task | Tool nên dùng |
|---|---|
| HĐLĐ, JD, nội quy, phiếu thu, thư mời, SOP đơn giản | `vn_draft` |
| Phân tích chiến lược, mở chi nhánh, ngân sách lớn, rebrand | Full pipeline (`vn_run → meeting → approve → execute`) |
| Quyết định pháp lý cao (hợp đồng đối tác lớn, IPO docs) | Full pipeline + tự thuê luật sư review |

### Mẹo 5: Cuối session, archive task cũ

Sau 30 ngày, các task trong `02-Tasks/` cũ → move sang `99-Archive/<năm-tháng>/`:

> "Move các task trong 02-Tasks/ tạo trước ngày 2026-04-01 sang 99-Archive/2026-Q1/"

Claude tự gọi `obsidian_*` chuyển file. Giữ `02-Tasks/` gọn → load vault nhanh hơn.

### Mẹo 6: Backup vault định kỳ

Vault là toàn bộ "bộ não" DN bạn. Mất = mất hết quyết định + tài liệu lịch sử.

**Cách 1 — Git private repo (khuyến nghị):**
```powershell
cd "F:\vaults\Sao Việt"
git init
git add .
git commit -m "init vault"
# Tạo private repo trên GitHub → push
git remote add origin https://github.com/<bạn>/sao-viet-vault.git
git push -u origin main
```
Mỗi tuần: `git add . && git commit -m "weekly backup" && git push`.

**Cách 2 — Copy thủ công:**
Định kỳ copy folder `F:\vaults\Sao Việt` sang OneDrive/Google Drive.

---

### Mẹo 7: Workflow khi update repo / sửa code

Khi bạn pull bản mới của repo, hoặc tự sửa code Python:

```powershell
# 1. Pull bản mới (nếu dùng git)
cd "F:\.work\vn-one-person-company"
git pull

# 2. Kill MCP process cũ
Get-Process vn-os-mcp -ErrorAction SilentlyContinue | Stop-Process -Force

# 3. (Nếu pyproject.toml đổi) reinstall:
pip install -e .

# 4. Quit Claude Desktop từ tray (right-click icon → Quit)

# 5. Mở lại Claude Desktop → tab Code → test:
#    "Chạy vn_status với vault F:\vaults\<TênDN>"
```

> ⚠️ **Bỏ bước nào cũng có thể gây "code không có hiệu lực".** Đặc biệt bước 2 (kill MCP) và bước 4 (Quit tray) — đây là 2 lỗi học viên hay quên.

---

## 🤝 PHẦN 6 — DÀNH CHO DEV (advanced)

### Chạy MCP server ở chế độ debug

```powershell
cd "F:\.work\vn-one-person-company"
.\.venv\Scripts\Activate.ps1
$env:MCP_DEBUG = "1"
vn-os-mcp
```

Logs in trực tiếp ra console → debug được tool calls.

### Override config qua `.vncoderc`

File `$HOME\.vncoderc` (đã tạo ở Bước 7.2) chỉnh:

```yaml
llm:
  primary: deepseek-v4-pro          # hoặc claude-sonnet-4-6
  secondary: deepseek-v4-flash
  max_retries: 3
  max_tokens_per_task: 100000

meeting:
  max_debate_rounds: 1     # 1 = nhanh, 2 = kỹ hơn
  total_max: 3

translator_mode: final_only   # off | final_only | all_intermediate
```

### Test pack mới

Tạo `packs/<your-pack>/` theo cấu trúc `packs/fnb/`. Test:
```powershell
pytest tests/ -k "your_pack" -v
```

### Contribute

PR tại https://github.com/&lt;owner&gt;/vn-one-person-company. Đặc biệt cần:
- Pack mới: Real Estate, Healthcare, Education, Beauty
- Translation: thêm thuật ngữ VN→EN trong glossary
- Test coverage: real-LLM E2E

---

**Có vấn đề trong Phần 1-6?** Mở issue tại: https://github.com/&lt;owner&gt;/vn-one-person-company/issues
