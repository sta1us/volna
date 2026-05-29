import enum
from datetime import datetime
from typing import List, Optional

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class UserRole(enum.Enum):
    ADMIN = "ADMIN"
    CLIENT = "CLIENT"


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.CLIENT)

    # Данные из Telegram
    tg_id: Mapped[int | None] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(50))
    first_name: Mapped[str | None] = mapped_column(String(100))
    # Связь с реакциями
    participations: Mapped[List["EventReaction"]] = relationship(back_populates="user")

    media: Mapped[List["Media"]] = relationship("Media", back_populates="user")


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(100))
    date_time: Mapped[datetime] = mapped_column(DateTime)
    image_path: Mapped[str] = mapped_column(String(255))
    tg_file_id: Mapped[str | None] = mapped_column(String(255))

    reactions: Mapped[List["EventReaction"]] = relationship(
        back_populates="event", cascade="all, delete-orphan"
    )

    media: Mapped[List["Media"]] = relationship(
        "Media", back_populates="event", cascade="all, delete-orphan"
    )


class MenuCategory(enum.Enum):
    KITCHEN = "kitchen"
    BAR = "bar"


class MenuPage(Base):
    __tablename__ = "menu_pages"

    id: Mapped[int] = mapped_column(primary_key=True)
    category: Mapped[MenuCategory] = mapped_column(Enum(MenuCategory))  # Кухня или Бар
    image_path: Mapped[str] = mapped_column(String(255))
    tg_file_id: Mapped[str | None] = mapped_column(String(255))  # Для кэша Telegram
    order_num: Mapped[int] = mapped_column(default=0)


class TeamMember(Base):
    __tablename__ = "team"

    id: Mapped[int] = mapped_column(primary_key=True)

    # ФИО (разбиваем для удобства сортировки и поиска)
    last_name: Mapped[str] = mapped_column(String(50))  # Фамилия
    first_name: Mapped[str] = mapped_column(String(50))  # Имя
    middle_name: Mapped[Optional[str]] = mapped_column(String(50))  # Отчество

    role: Mapped[str] = mapped_column(
        String(100)
    )  # Текущая должность (напр. "Шеф-повар")
    description: Mapped[Optional[str]] = mapped_column(Text)  # Описание/Биография

    # МЕДИА
    image_path: Mapped[str] = mapped_column(String(255))  # Путь в uploads/team/
    tg_file_id: Mapped[Optional[str]] = mapped_column(String(255))  # Кэш для Telegram

    # Порядок отображения на сайте (кто выше в списке)
    order_priority: Mapped[int] = mapped_column(default=0)

    @property
    def full_name(self):
        """Удобный метод для получения полного имени в коде"""
        if self.middle_name:
            return f"{self.last_name} {self.first_name} {self.middle_name}"
        return f"{self.last_name} {self.first_name}"


class ReviewStatus(enum.Enum):
    PENDING = "pending"  # Ожидает проверки
    APPROVED = "approved"  # Одобрен (виден на сайте)
    REJECTED = "rejected"  # Отклонен


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Кто оставил (для авторизованных через ТГ)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )

    # Данные для неавторизованных (Guest)
    guest_name: Mapped[str | None] = mapped_column(String(100))
    guest_contact: Mapped[str | None] = mapped_column(String(100))  # Телефон или @nick

    text: Mapped[str] = mapped_column(Text)
    rating: Mapped[int] = mapped_column(default=5)  # Оценка 1-5

    status: Mapped[ReviewStatus] = mapped_column(
        Enum(ReviewStatus), default=ReviewStatus.PENDING
    )
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class SuggestionStatus(enum.Enum):
    PENDING = "pending"  # Ожидает проверки
    PLANNED = "planned"  # Запланированно
    REJECTED = "rejected"  # Отклонен


class Suggestion(Base):
    __tablename__ = "suggestions"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Кто оставил (для авторизованных через ТГ)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )

    # Данные для неавторизованных (Guest)
    guest_name: Mapped[str | None] = mapped_column(String(100))
    guest_contact: Mapped[str | None] = mapped_column(String(100))

    subject: Mapped[str | None] = mapped_column(String(200))  # Тема предложения
    text: Mapped[str] = mapped_column(Text)

    is_read: Mapped[bool] = mapped_column(default=False)  # Прочитано админом или нет

    status: Mapped[SuggestionStatus] = mapped_column(
        Enum(SuggestionStatus), default=SuggestionStatus.PENDING
    )

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class Location(Base):
    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(primary_key=True)
    address: Mapped[str] = mapped_column(String(255))
    latitude: Mapped[float] = mapped_column(nullable=False)
    longitude: Mapped[float] = mapped_column(nullable=False)

    # map
    map_image_path: Mapped[Optional[str]] = mapped_column(String(255))
    map_tg_file_id: Mapped[Optional[str]] = mapped_column(String(255))

    # ФОТО ВХОДА / ЗДАНИЯ
    image_path: Mapped[Optional[str]] = mapped_column(String(255))
    tg_file_id: Mapped[Optional[str]] = mapped_column(String(255))

    working_hours: Mapped[Optional[str]] = mapped_column(String(200))
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    email: Mapped[Optional[str]] = mapped_column(String(200))


class ReactionStatus(enum.Enum):
    GOING = "going"  # Точно пойду
    MAYBE = "maybe"  # Возможно
    NOT_GOING = "not"  # Не пойду (отмена)


class EventReaction(Base):
    __tablename__ = "event_reactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    status: Mapped[ReactionStatus] = mapped_column(
        Enum(ReactionStatus), default=ReactionStatus.GOING
    )

    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        onupdate=datetime.utcnow,  # Авто-дата при изменении решения
    )

    user: Mapped["User"] = relationship(back_populates="participations")
    event: Mapped["Event"] = relationship(back_populates="reactions")


class MediaType(enum.Enum):
    IMAGE = "image"
    VIDEO = "video"


class Media(Base):
    __tablename__ = "media"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Кто загрузил (ссылка на твою модель User)
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Прямой ID из телеграма (удобно для бота)
    tg_file_id: Mapped[Optional[str]] = mapped_column(String(255))

    # Привязка к событию (опционально)
    event_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("events.id", ondelete="SET NULL"), nullable=True
    )

    file_path: Mapped[str] = mapped_column(String)
    media_type: Mapped[MediaType] = mapped_column(Enum(MediaType))
    caption: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Связи
    event: Mapped[Optional["Event"]] = relationship(back_populates="media")
    user: Mapped[Optional["User"]] = relationship()  # Чтобы знать автора
