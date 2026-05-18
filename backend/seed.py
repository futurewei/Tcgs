"""
Seed script to create initial data for AlgoHub
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
    admin = db.query(User).filter(User.email == "admin@algohub.com").first()
    if not admin:
        # Create admin user
        admin = User(
            email="admin@algohub.com",
            name="admin",
            hashed_password=AuthService.get_password_hash("admin123"),
            role=UserRole.ADMIN
        )
        db.add(admin)
        print("Created admin user: admin@algohub.com / admin123")

    # Create member user
    member = db.query(User).filter(User.email == "member@algohub.com").first()
    if not member:
        member = User(
            email="member@algohub.com",
            name="大峰",
            hashed_password=AuthService.get_password_hash("member123"),
            role=UserRole.MEMBER
        )
        db.add(member)
        print("Created member user: member@algohub.com / member123")

    # Create reviewer user
    reviewer = db.query(User).filter(User.email == "reviewer@algohub.com").first()
    if not reviewer:
        reviewer = User(
            email="reviewer@algohub.com",
            name="旭哥",
            hashed_password=AuthService.get_password_hash("reviewer123"),
            role=UserRole.REVIEWER
        )
        db.add(reviewer)
        print("Created reviewer user: reviewer@algohub.com / reviewer123")

    # Create external user
    external = db.query(User).filter(User.email == "external@algohub.com").first()
    if not external:
        external = User(
            email="external@algohub.com",
            name="外部协作者",
            hashed_password=AuthService.get_password_hash("external123"),
            role=UserRole.EXTERNAL
        )
        db.add(external)
        print("Created external user: external@algohub.com / external123")

    # Create customer user (PDU内 - Internal)
    customer_internal = db.query(User).filter(User.email == "pdt@algohub.com").first()
    if not customer_internal:
        customer_internal = User(
            email="pdt@algohub.com",
            name="PDT经理",
            hashed_password=AuthService.get_password_hash("pdt123"),
            role=UserRole.CUSTOMER_INTERNAL
        )
        db.add(customer_internal)
        print("Created customer (PDU内) user: pdt@algohub.com / pdt123")
    elif customer_internal.role not in [UserRole.CUSTOMER_INTERNAL, UserRole.CUSTOMER_EXTERNAL]:
        # 更新旧的 CUSTOMER 角色为 CUSTOMER_INTERNAL
        customer_internal.role = UserRole.CUSTOMER_INTERNAL
        print("Updated customer role to CUSTOMER_INTERNAL: pdt@algohub.com")

    # Create customer user (PDU外 - External)
    customer_external = db.query(User).filter(User.email == "partner@algohub.com").first()
    if not customer_external:
        customer_external = User(
            email="partner@algohub.com",
            name="外部合作方",
            hashed_password=AuthService.get_password_hash("partner123"),
            role=UserRole.CUSTOMER_EXTERNAL
        )
        db.add(customer_external)
        print("Created customer (PDU外) user: partner@algohub.com / partner123")

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
    slot1 = db.query(CapacitySlot).filter(CapacitySlot.name == member.name).first()
    if not slot1:
        slot1 = CapacitySlot(
            name=member.name,
            type=SlotType.ALGO,
            user_id=member.id if member else None,
            total_capacity=100
        )
        db.add(slot1)
        print("Created Algo slot: 张三")

    slot2 = db.query(CapacitySlot).filter(CapacitySlot.name == reviewer.name).first()
    if not slot2:
        slot2 = CapacitySlot(
            name=reviewer.name,
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

    ext_slot = db.query(CapacitySlot).filter(CapacitySlot.name == external.name).first()
    if not ext_slot:
        ext_slot = CapacitySlot(
            name=external.name,
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

    # ================================================================
    # Seed Capability Category Taxonomy Tree (by capability, NOT product)
    # ================================================================

    def seed_category(name, parent_id=None, display_order=0):
        existing = db.query(CapabilityCategory).filter(
            CapabilityCategory.name == name,
            CapabilityCategory.parent_id == parent_id,
        ).first()
        if existing:
            return existing
        cat = CapabilityCategory(
            name=name,
            parent_id=parent_id,
            display_order=display_order,
        )
        db.add(cat)
        db.flush()
        return cat

    # --- 空间感知与稳定 ---
    spatial = seed_category("空间感知与稳定", display_order=0)
    seed_category("空间稳定性", parent_id=spatial.id, display_order=0)
    seed_category("动态AR Anchoring", parent_id=spatial.id, display_order=1)
    seed_category("空间标定", parent_id=spatial.id, display_order=2)

    # --- 渲染与编排 ---
    render = seed_category("渲染与编排", display_order=1)
    seed_category("实时渲染", parent_id=render.id, display_order=0)
    seed_category("多VID编排", parent_id=render.id, display_order=1)
    seed_category("抗抖策略", parent_id=render.id, display_order=2)
    seed_category("动态编排", parent_id=render.id, display_order=3)

    # --- 投影与映射 ---
    project = seed_category("投影与映射", display_order=2)
    seed_category("空间投影", parent_id=project.id, display_order=0)
    seed_category("畸变矫正", parent_id=project.id, display_order=1)
    seed_category("地面映射", parent_id=project.id, display_order=2)
    seed_category("多平面映射", parent_id=project.id, display_order=3)
    seed_category("真彩校正", parent_id=project.id, display_order=4)
    seed_category("几何矫正", parent_id=project.id, display_order=5)

    # --- 表达与交互 ---
    express = seed_category("表达与交互", display_order=3)
    seed_category("路权表达", parent_id=express.id, display_order=0)
    seed_category("场景切换", parent_id=express.id, display_order=1)
    seed_category("交互表达", parent_id=express.id, display_order=2)

    # --- 标定与一致性 ---
    calib = seed_category("标定与一致性", display_order=4)
    seed_category("标定一致性", parent_id=calib.id, display_order=0)

    # --- 融合与感知 ---
    fusion = seed_category("融合与感知", display_order=5)
    seed_category("多传感器融合", parent_id=fusion.id, display_order=0)
    seed_category("感知融合", parent_id=fusion.id, display_order=1)

    # --- 参数与泛化 ---
    param = seed_category("参数与泛化", display_order=6)
    seed_category("参数泛化能力", parent_id=param.id, display_order=0)

    print("Seeded capability category taxonomy tree")

    db.commit()
    print("\nSeed completed successfully!")
    print("\nDemo accounts:")
    print("  Admin:              admin@algohub.com / admin123")
    print("  Member:             member@algohub.com / member123")
    print("  Reviewer:           reviewer@algohub.com / reviewer123")
    print("  External:           external@algohub.com / external123")
    print("  Customer (PDU内):   pdt@algohub.com / pdt123")
    print("  Customer (PDU外):   partner@algohub.com / partner123")

except Exception as e:
    print(f"Error: {e}")
    db.rollback()
finally:
    db.close()
