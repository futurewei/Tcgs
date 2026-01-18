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
            name="Admin User",
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
            name="Member User",
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
            name="Reviewer User",
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
            name="External Partner",
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
            name="PDT",
            hashed_password=AuthService.get_password_hash("pdt123"),
            role=UserRole.CUSTOMER
        )
        db.add(customer)
        print("Created customer user: pdt@tcgs.com / pdt123")

    db.flush()

    # Create default stage template
    template = db.query(StageTemplate).filter(StageTemplate.name == "Standard Workflow").first()
    if not template:
        template = StageTemplate(
            name="Standard Workflow",
            description="Standard 4-stage workflow for most topics"
        )
        db.add(template)
        db.flush()

        stages = [
            StageTemplateStage(
                template_id=template.id,
                name="Definition",
                description="Define the problem and scope",
                order=0,
                is_terminal=False,
                allow_result=False,
                require_artifact=True
            ),
            StageTemplateStage(
                template_id=template.id,
                name="Analysis",
                description="Analyze possible solutions",
                order=1,
                is_terminal=False,
                allow_result=False,
                require_artifact=True
            ),
            StageTemplateStage(
                template_id=template.id,
                name="Implementation",
                description="Implement the chosen solution",
                order=2,
                is_terminal=False,
                allow_result=False,
                require_artifact=True
            ),
            StageTemplateStage(
                template_id=template.id,
                name="Closure",
                description="Review and close the topic",
                order=3,
                is_terminal=True,
                allow_result=True,
                require_artifact=False
            ),
        ]
        for stage in stages:
            db.add(stage)
        print("Created Standard Workflow template")

    # Create POC template
    poc_template = db.query(StageTemplate).filter(StageTemplate.name == "POC Template").first()
    if not poc_template:
        poc_template = StageTemplate(
            name="POC Template",
            description="Quick proof-of-concept workflow"
        )
        db.add(poc_template)
        db.flush()

        stages = [
            StageTemplateStage(
                template_id=poc_template.id,
                name="Exploration",
                description="Explore the problem space",
                order=0,
                is_terminal=False,
                allow_result=False,
                require_artifact=False
            ),
            StageTemplateStage(
                template_id=poc_template.id,
                name="POC",
                description="Build and test proof of concept",
                order=1,
                is_terminal=False,
                allow_result=False,
                require_artifact=True
            ),
            StageTemplateStage(
                template_id=poc_template.id,
                name="Decision",
                description="Make go/no-go decision",
                order=2,
                is_terminal=True,
                allow_result=True,
                require_artifact=False
            ),
        ]
        for stage in stages:
            db.add(stage)
        print("Created POC Template")

    # Create capacity slots
    slot1 = db.query(CapacitySlot).filter(CapacitySlot.name == "Alice Chen").first()
    if not slot1:
        slot1 = CapacitySlot(
            name="Alice Chen",
            type=SlotType.ALGO,
            user_id=member.id if member else None,
            total_capacity=100
        )
        db.add(slot1)
        print("Created Algo slot: Alice Chen")

    slot2 = db.query(CapacitySlot).filter(CapacitySlot.name == "Bob Wang").first()
    if not slot2:
        slot2 = CapacitySlot(
            name="Bob Wang",
            type=SlotType.ALGO,
            user_id=reviewer.id if reviewer else None,
            total_capacity=100
        )
        db.add(slot2)
        print("Created Algo slot: Bob Wang")

    ext_slot = db.query(CapacitySlot).filter(CapacitySlot.name == "External Vendor").first()
    if not ext_slot:
        ext_slot = CapacitySlot(
            name="External Vendor",
            type=SlotType.EXTERNAL,
            user_id=external.id if external else None,
            total_capacity=50
        )
        db.add(ext_slot)
        print("Created External slot: External Vendor")

    # Create wiki direction
    wiki_dir = db.query(WikiDirection).filter(WikiDirection.name == "Documentation").first()
    if not wiki_dir:
        wiki_dir = WikiDirection(
            name="Documentation",
            description="System documentation and guides"
        )
        db.add(wiki_dir)
        print("Created Wiki direction: Documentation")

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
