import csv
import random
from datetime import datetime, timedelta

# 可选企业名、地址样本
names = ["企业A", "企业B", "企业C", "企业D", "企业E", "企业F", "企业G", "企业H"]
cities = ["北京", "上海", "广州", "深圳", "杭州", "成都", "南京", "苏州"]

# 生成时间基准
base_time = datetime(2025, 11, 16, 9, 0, 0)

# 输出文件
file_name = "customers.csv"

total = 100000  # 10W条

with open(file_name, mode="w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)

    # 写表头
    writer.writerow(["id", "name", "email", "phone", "address", "created_at", "updated_at", "owner_id"])

    for i in range(6, total):
        name = random.choice(names) + str(i)     # 防止重复 企业A1 企业A2...
        email = f"user{i}@qq.com"
        phone = f"{random.randint(1000000, 9999999)}"
        address = random.choice(cities)

        # 每条时间略微增加避免完全相同
        created = base_time + timedelta(seconds=i)
        updated = created + timedelta(minutes=random.randint(0, 10))

        writer.writerow([
            i,
            name,
            email,
            phone,
            address,
            created.strftime("%Y-%m-%d %H:%M:%S"),
            updated.strftime("%Y-%m-%d %H:%M:%S"),
            1  # owner_id 固定为1
        ])

print(f"🎉 已生成 {total} 条数据 → {file_name}")
