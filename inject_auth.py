import os
from pathlib import Path

root = Path(r"c:\D_volume\FYP\Projects\AI-Empowered-Fintech-Fraud-Detection-and-Control-Automation-System")
main_file = root / "backend" / "main.py"
main_content = main_file.read_text("utf-8")

# Let's inject import for auth_service
if "from backend.services import auth_service" not in main_content:
    import_block = "from backend import models, schemas\nfrom backend.services import auth_service\nfrom datetime import timedelta\n"
    main_content = main_content.replace("from backend import models, schemas\n", import_block)

# Add the Auth Endpoints
auth_routes = """
# =============================================================================
# AUTHENTICATION ENDPOINTS
# =============================================================================

@app.post("/api/v1/auth/register", response_model=schemas.UserRegister, tags=["Authentication"])
async def register(user: schemas.UserRegister, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = auth_service.get_password_hash(user.password)
    new_user = models.User(
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        hashed_password=hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return user

@app.post("/api/v1/auth/login", response_model=schemas.TokenResponse, tags=["Authentication"])
async def login(user_login: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user_login.email).first()
    if not db_user or not auth_service.verify_password(user_login.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    access_token_expires = timedelta(minutes=auth_service.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth_service.create_access_token(
        data={"sub": db_user.email}, expires_delta=access_token_expires
    )
    return schemas.TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=db_user.id,
        email=db_user.email
    )

# =============================================================================
# VERIFY ENDPOINT (combined approve/reject)
# =============================================================================

@app.post("/api/v1/transactions/{transaction_id}/verify", tags=["Workflow"])
async def verify_transaction(transaction_id: str, request: schemas.VerifyRequest, db: Session = Depends(get_db)):
    if request.action == "approve":
        return await approve_transaction(transaction_id, db)
    elif request.action == "reject":
        return await reject_transaction(transaction_id, db)
    else:
        raise HTTPException(status_code=400, detail="Invalid action")
"""

if "AUTHENTICATION ENDPOINTS" not in main_content:
    main_content += auth_routes

# Alias stats endpoint
if '@app.get("/api/v1/dashboard/stats"' not in main_content:
    main_content = main_content.replace(
        '@app.get(\n    "/api/v1/stats",',
        '@app.get("/api/v1/dashboard/stats", response_model=schemas.StatsResponse, tags=["Analytics"])\n@app.get(\n    "/api/v1/stats",'
    )

main_file.write_text(main_content, "utf-8")
print("main.py auth injection finished")
