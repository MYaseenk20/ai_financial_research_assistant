from datetime import datetime

from sqlalchemy import String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column, relationship

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id : Mapped[int] = mapped_column(primary_key=True,index=True)
    email: Mapped[str] = mapped_column(String(255),index=True,unique=True,nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255),nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # reports: Mapped[list["Report"]] = relationship("Report", back_populates="user", cascade="all, delete")

# class Report(Base):
#     __tablename__ = "reports"