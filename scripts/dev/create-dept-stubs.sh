#!/usr/bin/env bash
set -euo pipefail

declare -a DEPTS=(
  "01-governance|Quản trị & Pháp lý|1"
  "02-strategy|Chiến lược & Kế hoạch|1"
  "03-finance|Tài chính & Kế toán|2"
  "04-people|Nhân sự & Con người|2"
  "05-operations|Hành chính & Vận hành|2"
  "06-sales|Kinh doanh & Bán hàng|3"
  "07-marketing|Marketing & Thương hiệu|3"
  "08-customer|Khách hàng & Dịch vụ|3"
  "09-product-tech|Sản phẩm & Công nghệ|4"
  "10-training|Đào tạo & Phát triển|4"
  "11-reporting|Báo cáo & Đo lường|4"
  "12-growth|Tăng trưởng & Đầu tư|5"
)

for entry in "${DEPTS[@]}"; do
  IFS='|' read -r code name tier <<< "$entry"
  mkdir -p "departments/$code/agents" "departments/$code/refs"

  cat > "departments/$code/department.yaml" << YAML
code: "$code"
name_vn: "$name"
tier: $tier
description: "Phòng $name."
agents: []
default_speaker: ""
refs_folder: refs/
depends_on: []
debate_role:
  default: pro
YAML
done

echo "✅ Created 12 department stubs"
