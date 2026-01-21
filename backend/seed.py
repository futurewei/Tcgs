"""
Seed script to create initial data for TCGS
Run: python seed.py
"""
from app.database import SessionLocal, engine, Base
from app.models import *
from app.services.auth import AuthService
from app.models.user import UserRole
from app.models.user import User
from app.models.capacity import SlotType

# Create all tables
Base.metadata.create_all(bind=engine)

db = SessionLocal()

try:
    # Check if admin exists
    admin = db.query(User).filter(User.email == "admin@tcgs.com").first()
    if not admin:
        # Create admin user
        admin = User(
            email="admin@tcgs.com",
            name="管理员",
            hashed_password=AuthService.get_password_hash("admin123"),
            role=UserRole.ADMIN
        )
        db.add(admin)
        print("Created admin user: admin@tcgs.com / admin123")

    # Create member user
    member = db.query(User).filter(User.email == "member@tcgs.com").first()
    if not member:
        member = User(
            email="member@tcgs.com",
            name="算法成员",
            hashed_password=AuthService.get_password_hash("member123"),
            role=UserRole.MEMBER
        )
        db.add(member)
        print("Created member user: member@tcgs.com / member123")

    # Create reviewer user
    reviewer = db.query(User).filter(User.email == "reviewer@tcgs.com").first()
    if not reviewer:
        reviewer = User(
            email="reviewer@tcgs.com",
            name="评审员",
            hashed_password=AuthService.get_password_hash("reviewer123"),
            role=UserRole.REVIEWER
        )
        db.add(reviewer)
        print("Created reviewer user: reviewer@tcgs.com / reviewer123")

    # Create external user
    external = db.query(User).filter(User.email == "external@tcgs.com").first()
    if not external:
        external = User(
            email="external@tcgs.com",
            name="外部协作者",
            hashed_password=AuthService.get_password_hash("external123"),
            role=UserRole.EXTERNAL
        )
        db.add(external)
        print("Created external user: external@tcgs.com / external123")

    # Create customer user (Requester / Client)
    customer = db.query(User).filter(User.email == "pdt@tcgs.com").first()
    if not customer:
        customer = User(
            email="pdt@tcgs.com",
            name="PDT需求方",
            hashed_password=AuthService.get_password_hash("pdt123"),
            role=UserRole.CUSTOMER
        )
        db.add(customer)
        print("Created customer user: pdt@tcgs.com / pdt123")

    db.flush()

    # Create default stage template (Chinese - Standard 6-stage)
    template = db.query(StageTemplate).filter(StageTemplate.name == "标准课题流程").first()
    if not template:
        template = StageTemplate(
            name="标准课题流程",
            description="标准6阶段课题流程，适用于大多数课题"
        )
        db.add(template)
        db.flush()

        stages = [
            StageTemplateStage(
                template_id=template.id,
                name="问题定义",
                description="定义问题范围和目标",
                order=0,
                is_terminal=False,
                allow_result=False,
                require_artifact=True
            ),
            StageTemplateStage(
                template_id=template.id,
                name="调研分析",
                description="分析可能的解决方案",
                order=1,
                is_terminal=False,
                allow_result=False,
                require_artifact=True
            ),
            StageTemplateStage(
                template_id=template.id,
                name="方案设计",
                description="设计详细的实施方案",
                order=2,
                is_terminal=False,
                allow_result=False,
                require_artifact=True
            ),
            StageTemplateStage(
                template_id=template.id,
                name="开发实现",
                description="实现所选方案",
                order=3,
                is_terminal=False,
                allow_result=False,
                require_artifact=True
            ),
            StageTemplateStage(
                template_id=template.id,
                name="算法SubPC",
                description="算法SubPC评审",
                order=4,
                is_terminal=False,
                allow_result=False,
                require_artifact=True
            ),
            StageTemplateStage(
                template_id=template.id,
                name="验收",
                description="最终验收并结题",
                order=5,
                is_terminal=True,
                allow_result=True,
                require_artifact=False
            ),
        ]
        for stage in stages:
            db.add(stage)
        print("Created 标准课题流程 template")

    # Also update the old English template if it exists
    old_template = db.query(StageTemplate).filter(StageTemplate.name == "Standard Workflow").first()
    if old_template:
        old_template.name = "标准流程 (旧版)"
        old_template.description = "旧版4阶段流程"
        print("Renamed old Standard Workflow template")

    # Create POC template (Chinese)
    poc_template = db.query(StageTemplate).filter(StageTemplate.name == "POC快速验证").first()
    if not poc_template:
        poc_template = StageTemplate(
            name="POC快速验证",
            description="快速概念验证流程"
        )
        db.add(poc_template)
        db.flush()

        stages = [
            StageTemplateStage(
                template_id=poc_template.id,
                name="问题探索",
                description="探索问题空间",
                order=0,
                is_terminal=False,
                allow_result=False,
                require_artifact=False
            ),
            StageTemplateStage(
                template_id=poc_template.id,
                name="POC实现",
                description="构建并测试概念验证",
                order=1,
                is_terminal=False,
                allow_result=False,
                require_artifact=True
            ),
            StageTemplateStage(
                template_id=poc_template.id,
                name="算法SubPC",
                description="算法SubPC评审",
                order=2,
                is_terminal=False,
                allow_result=False,
                require_artifact=True
            ),
            StageTemplateStage(
                template_id=poc_template.id,
                name="验收",
                description="做出继续/终止决定",
                order=3,
                is_terminal=True,
                allow_result=True,
                require_artifact=False
            ),
        ]
        for stage in stages:
            db.add(stage)
        print("Created POC快速验证 Template")

    # Also update the old POC template if it exists
    old_poc = db.query(StageTemplate).filter(StageTemplate.name == "POC Template").first()
    if old_poc:
        old_poc.name = "POC流程 (旧版)"
        old_poc.description = "旧版POC流程"
        print("Renamed old POC Template")

    # Create capacity slots (Chinese names)
    slot1 = db.query(CapacitySlot).filter(CapacitySlot.name == "张三").first()
    if not slot1:
        slot1 = CapacitySlot(
            name="张三",
            type=SlotType.ALGO,
            user_id=member.id if member else None,
            total_capacity=100
        )
        db.add(slot1)
        print("Created Algo slot: 张三")

    slot2 = db.query(CapacitySlot).filter(CapacitySlot.name == "李四").first()
    if not slot2:
        slot2 = CapacitySlot(
            name="李四",
            type=SlotType.ALGO,
            user_id=reviewer.id if reviewer else None,
            total_capacity=100
        )
        db.add(slot2)
        print("Created Algo slot: 李四")

    slot3 = db.query(CapacitySlot).filter(CapacitySlot.name == "王五").first()
    if not slot3:
        slot3 = CapacitySlot(
            name="王五",
            type=SlotType.ALGO,
            user_id=None,
            total_capacity=100
        )
        db.add(slot3)
        print("Created Algo slot: 王五")

    ext_slot = db.query(CapacitySlot).filter(CapacitySlot.name == "外部供应商A").first()
    if not ext_slot:
        ext_slot = CapacitySlot(
            name="外部供应商A",
            type=SlotType.EXTERNAL,
            user_id=external.id if external else None,
            total_capacity=50
        )
        db.add(ext_slot)
        print("Created External slot: 外部供应商A")

    ext_slot2 = db.query(CapacitySlot).filter(CapacitySlot.name == "协作团队B").first()
    if not ext_slot2:
        ext_slot2 = CapacitySlot(
            name="协作团队B",
            type=SlotType.EXTERNAL,
            user_id=None,
            total_capacity=80
        )
        db.add(ext_slot2)
        print("Created External slot: 协作团队B")

    # Create wiki direction
    wiki_dir = db.query(WikiDirection).filter(WikiDirection.name == "技术文档").first()
    if not wiki_dir:
        wiki_dir = WikiDirection(
            name="技术文档",
            description="系统技术文档和指南"
        )
        db.add(wiki_dir)
        print("Created Wiki direction: 技术文档")

    db.commit()
    print("\nSeed completed successfully!")
    print("\nDemo accounts:")
    print("  Admin:    admin@tcgs.com / admin123")
    print("  Member:   member@tcgs.com / member123")
    print("  Reviewer: reviewer@tcgs.com / reviewer123")
    print("  External: external@tcgs.com / external123")
    print("  Customer: pdt@tcgs.com / pdt123")

except Exception as e:
    print(f"Error: {e}")
    db.rollback()
finally:
    db.close()
