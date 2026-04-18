"""
初始化测试数据脚本
生成 100+ 条工单数据，包含 first_response_at 和 completed_at，
响应时长随机分布在 0.5-48 小时之间。

使用方法：
    python scripts/init_test_data.py
"""

import sys
import os
import asyncio
import random
import datetime

# 将项目根目录添加到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.future import select
from models import Base, User, Ticket
from db import DATABASE_URL

engine = create_async_engine(DATABASE_URL, echo=False, future=True)
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

CATEGORIES = ["维修", "采购", "请求", "咨询", "投诉", "其他"]
PRIORITIES = ["low", "medium", "high", "urgent"]
STATUSES = ["open", "in_progress", "resolved", "closed"]

TITLES = [
    "办公室空调维修申请",
    "打印机耗材采购请求",
    "会议室投影仪故障",
    "网络连接不稳定问题",
    "办公椅损坏更换申请",
    "门禁卡补办申请",
    "电脑键盘故障维修",
    "办公桌调配申请",
    "楼道灯光维修",
    "消防设备检查请求",
    "清洁用品补充申请",
    "停车场车位申请",
    "电话系统故障报修",
    "复印机卡纸问题",
    "窗户玻璃破损维修",
    "电梯故障报修",
    "饮水机维护申请",
    "办公室绿植养护",
    "监控设备故障",
    "电路跳闸维修",
]


async def get_or_create_test_user(db: AsyncSession) -> User:
    """获取或创建测试用户"""
    result = await db.execute(select(User).where(User.username == "test_admin"))
    user = result.scalar_one_or_none()
    if user is None:
        import hashlib
        user = User(
            username="test_admin",
            password_hash=hashlib.sha256(b"testpass123").hexdigest(),
            role="staff",
        )
        db.add(user)
        await db.flush()
    return user


async def init_test_data():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as db:
        user = await get_or_create_test_user(db)

        today = datetime.date.today()
        tickets_created = 0

        for i in range(120):
            # 随机创建日期（过去 90 天内）
            days_ago = random.randint(0, 89)
            created_date = today - datetime.timedelta(days=days_ago)
            created_dt = datetime.datetime.combine(created_date, datetime.time(
                hour=random.randint(8, 17),
                minute=random.randint(0, 59),
            ))

            status = random.choices(STATUSES, weights=[20, 30, 30, 20])[0]
            has_response = random.random() < 0.85  # 85% 的工单有回复

            first_response_at = None
            completed_at = None

            if has_response:
                # 响应时长随机分布在 0.5-48 小时之间
                response_hours = random.uniform(0.5, 48.0)
                first_response_at = created_dt + datetime.timedelta(hours=response_hours)

            if status in ("resolved", "closed"):
                # 完成时间在响应后 1-72 小时
                base_dt = first_response_at if first_response_at else created_dt
                complete_hours = random.uniform(1.0, 72.0)
                completed_at = base_dt + datetime.timedelta(hours=complete_hours)

            # 随机截止日期（部分工单有截止日期）
            due_date = None
            if random.random() < 0.6:
                due_offset = random.randint(-10, 30)
                due_date = created_date + datetime.timedelta(days=due_offset)

            title_base = random.choice(TITLES)
            ticket = Ticket(
                title=f"{title_base}#{i + 1}",
                description=f"工单描述：{title_base}，需要及时处理。",
                category=random.choice(CATEGORIES),
                priority=random.choice(PRIORITIES),
                status=status,
                created_at=created_date,
                updated_at=created_date,
                due_date=due_date,
                user_id=user.id,
                assignee_id=user.id,
                first_response_at=first_response_at,
                completed_at=completed_at,
            )
            db.add(ticket)
            tickets_created += 1

        await db.commit()
        print(f"✅ 成功创建 {tickets_created} 条测试工单数据")


if __name__ == "__main__":
    asyncio.run(init_test_data())
