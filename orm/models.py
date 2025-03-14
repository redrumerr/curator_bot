from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, PrimaryKeyConstraint, event
from sqlalchemy.orm import Mapped, mapped_column, relationship
from orm.database import Base, async_session
from datetime import datetime


class Student(Base):
    __tablename__ = "Student"

    id: Mapped[int] = mapped_column(primary_key=True)
    vk_id: Mapped[int]
    name: Mapped[str]


class AlmostCurator(Student):
    __tablename__ = "AlmostCurator"

    id: Mapped[int] = mapped_column(ForeignKey("Student.id"), primary_key=True)
    group_number: Mapped[str]
    birthday_date = Column(DateTime,)
    strikes_number: Mapped[int] = mapped_column(default=0)
    rating: Mapped[float] = mapped_column(default=10)
    inst_or_tg: Mapped[str]
    phone_number: Mapped[str]
    hw_completion: Mapped[bool] = mapped_column(default=True)
    meeting_attendance: Mapped[int] = mapped_column(default=0)
    competition_activity_rate: Mapped[float] = mapped_column(default=10)
    competition_responsibility_rate: Mapped[float] = mapped_column(default=10)
    competition_interactions_rate: Mapped[float] = mapped_column(default=10)
    competition_rules_rate: Mapped[float] = mapped_column(default=10)
    competition_additional_rate: Mapped[float] = mapped_column(default=10)

    student = relationship(Student, cascade='all,delete', backref='almostcurator')

    def __str__(self):
        return f'ФИО: {self.name}\n' \
               f'Группа: {self.group_number}\n' \
               f'День рождения: {self.birthday_date.strftime("%d.%m.%Y")}\n' \
               f'Количество страйков: {self.strikes_number}\n' \
               f'Количество пропусков: {self.meeting_attendance}\n' \
               f'Тг: {self.inst_or_tg}\n' \
               f'Номер телефона: {self.phone_number}'

    def __repr__(self):
        return f'ФИО: {self.name}\n' \
               f'Группа: {self.group_number}\n' \
               f'День рождения: {self.birthday_date.strftime("%d.%m.%Y")}\n' \
               f'Количество страйков: {self.strikes_number}\n' \
               f'Количество пропусков: {self.meeting_attendance}\n' \
               f'Тг: {self.inst_or_tg}\n' \
               f'Номер телефона: {self.phone_number}\n\n' \
               f'Рейтинг: {self.rating}\n' \
               f'Пропуски: {self.meeting_attendance}\n\n' \
               f'Компетенции:\n' \
               f'Активность: {self.competition_activity_rate}\n' \
               f'Ответственность: {self.competition_responsibility_rate}\n' \
               f'Взаимодействия: {self.competition_interactions_rate}\n' \
               f'Соблюдение правил: {self.competition_rules_rate}'


class Competition(Base):
    __abstract__ = True

    iras_rate: Mapped[str] = mapped_column(default='10')
    fedas_rate: Mapped[str] = mapped_column(default='10')
    sashas_rate: Mapped[str] = mapped_column(default='10')
    katyas_rate: Mapped[str] = mapped_column(default='10')
    alinas_rate: Mapped[str] = mapped_column(default='10')
    artems_rate: Mapped[str] = mapped_column(default='10')


class CompetitionActivity(Competition):
    __tablename__ = "CompetitionActivity"

    almost_curator_id: Mapped[int] = mapped_column(ForeignKey("AlmostCurator.id"), primary_key=True)

    ac = relationship(AlmostCurator, cascade='all,delete', backref='competition_activity')

    def __str__(self):
        return f'Оценка Феди: {self.fedas_rate}\n' \
               f'Оценка Иры: {self.iras_rate}\n' \
               f'Оценка Кати: {self.katyas_rate}\n' \
               f'Оценка Саши: {self.sashas_rate}\n' \
               f'Оценка Тёмы: {self.artems_rate}\n' \
               f'Оценка Алины: {self.alinas_rate}'


class CompetitionResponsibility(Competition):
    __tablename__ = "CompetitionResponsibility"

    almost_curator_id: Mapped[int] = mapped_column(ForeignKey("AlmostCurator.id"), primary_key=True)

    ac = relationship(AlmostCurator, cascade='all,delete', backref='competition_responsibility')

    def __str__(self):
        return f'Оценка Феди: {self.fedas_rate}\n' \
               f'Оценка Иры: {self.iras_rate}\n' \
               f'Оценка Кати: {self.katyas_rate}\n' \
               f'Оценка Саши: {self.sashas_rate}\n' \
               f'Оценка Тёмы: {self.artems_rate}\n' \
               f'Оценка Алины: {self.alinas_rate}'


class CompetitionInteractions(Competition):
    __tablename__ = "CompetitionInteractions"

    almost_curator_id: Mapped[int] = mapped_column(ForeignKey("AlmostCurator.id"), primary_key=True)

    ac = relationship(AlmostCurator, cascade='all,delete', backref='competition_interactions')

    def __str__(self):
        return f'Оценка Феди: {self.fedas_rate}\n' \
               f'Оценка Иры: {self.iras_rate}\n' \
               f'Оценка Кати: {self.katyas_rate}\n' \
               f'Оценка Саши: {self.sashas_rate}\n' \
               f'Оценка Тёмы: {self.artems_rate}\n' \
               f'Оценка Алины: {self.alinas_rate}'


class CompetitionRules(Competition):
    __tablename__ = "CompetitionRules"

    almost_curator_id: Mapped[int] = mapped_column(ForeignKey("AlmostCurator.id"), primary_key=True)

    ac = relationship(AlmostCurator, cascade='all,delete', backref='competition_rules')

    def __str__(self):
        return f'Оценка Феди: {self.fedas_rate}\n' \
               f'Оценка Иры: {self.iras_rate}\n' \
               f'Оценка Кати: {self.katyas_rate}\n' \
               f'Оценка Саши: {self.sashas_rate}\n' \
               f'Оценка Тёмы: {self.artems_rate}\n' \
               f'Оценка Алины: {self.alinas_rate}'


class CompetitionAdditional(Competition):
    __tablename__ = "CompetitionAdditional"

    almost_curator_id: Mapped[int] = mapped_column(ForeignKey("AlmostCurator.id"), primary_key=True)

    ac = relationship(AlmostCurator, cascade='all,delete', backref='competition_additional')

    def __str__(self):
        return f'Оценка Феди: {self.fedas_rate}\n' \
               f'Оценка Иры: {self.iras_rate}\n' \
               f'Оценка Кати: {self.katyas_rate}\n' \
               f'Оценка Саши: {self.sashas_rate}\n' \
               f'Оценка Тёмы: {self.artems_rate}\n' \
               f'Оценка Алины: {self.alinas_rate}'


class Deadline(Base):
    __tablename__ = "Deadline"

    id: Mapped[int] = mapped_column(primary_key=True)
    time = Column(DateTime,)
    name: Mapped[str]
    birthday: Mapped[bool] = mapped_column(default=False)

    def __str__(self):
        return f'Название: {self.name}\n\n' \
               f'Срок: {self.time}'
