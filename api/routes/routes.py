from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from api import service
from api.Database import get_db
from api.Dependencies import get_current_user
from api.Schemas import UserOut, UserRegister, UserLogin, Token, ReportResultOut
from api.models import User
from backend.core import build_graph, AgentState

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(payload: UserRegister, db: AsyncSession = Depends(get_db)):
    """Register a new user."""
    existing = await service.get_user_by_email(db, payload.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered.",
        )

    user = await service.create_user(db, payload.email, payload.password, payload.full_name)
    return user


@router.post("/login", response_model=Token)
async def login(payload: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    """Login and receive a JWT access token."""
    user = await service.authenticate_user(db, payload.username, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = service.create_access_token(data={"sub": str(user.id)})
    return Token(access_token=token)


@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)):
    """Return the currently authenticated user."""
    return current_user

@router.get("/analyze", response_model=ReportResultOut)
async def analyze_report(company: str= Query(...,description="Company name to analyze"),current_user: User = Depends(get_current_user)):
    """Analyze a Company report."""
    graph = build_graph()

    initial_state: AgentState = {
        "query": f"Analyze {company} for investment",
        "company": company,
        "research_result": "",
        "rag_result": "",
        "risk_result": "",
        "final_result": "",
        "next": "",
    }
    final_state = await graph.ainvoke(initial_state)
    result = final_state["final_result"]
    return ReportResultOut(
        final_result = result
    )