from .base import Base

from .riskvector import RiskVector

from enum import Enum as PyEnum

from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, Enum, ForeignKey, Float


class T(PyEnum):
    one = 1
    two = 2
    three = 3


class Test(Base):
    __tablename__ = 'tests'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    type = Column(Enum(T))
    vector_id = Column(Integer, ForeignKey(RiskVector.id))
    vector = relationship("RiskVector")
    risk = Column(Float)
    detail = Column(String)
    # fk = ForeignKeyConstraint(['id'], [RiskVector.id])

    def __str__(self) -> str:
        return 'Test(' + ', '.join(
        [n + '='+ str(self.__getattribute__(n)) for n in [
            'id',
            'name',
            'type',
            'vector_id',
        ]]) + ')'


from flask_admin.contrib.sqla import ModelView

class TestModelView(ModelView):
    def __init__(self, session, name=None, category=None, endpoint=None, url=None, static_folder=None, menu_class_name=None, menu_icon_type=None, menu_icon_value=None):
         super().__init__(Test, session, name, category, endpoint, url, static_folder, menu_class_name, menu_icon_type, menu_icon_value)
    can_delete = True
    column_display_pk = True
    column_hide_backrefs = False
    column_list = ["id","name","type","vector", "risk", "detail"]
    column_searchable_list = ["name"]
    # inline_models = (RiskVector,)
    

