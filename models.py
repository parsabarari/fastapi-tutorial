from sqlalchemy import String, Float
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None]
    price: Mapped[float] = mapped_column(Float)
    tax: Mapped[float | None]
