from .base import Base

from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String

from flask_admin.model.template import EndpointLinkRowAction, LinkRowAction

class RiskVector(Base):
    __tablename__ = 'vectors'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    schedule_string = Column(String)
    configblob = Column(String)
    tests = relationship("Test", back_populates="vector")


    def __str__(self) -> str:
         return 'RiskVector(' + ', '.join(
            [n + '='+ str(self.__getattribute__(n)) for n in [
                'id',
                'name',
                'schedule_string',
                'configblob'
            ]]) + ')'



from flask_admin.contrib.sqla import ModelView

class RiskVectorModelView(ModelView):
    def __init__(self, session, name=None, category=None, endpoint=None, url=None, static_folder=None, menu_class_name=None, menu_icon_type=None, menu_icon_value=None):
         super().__init__(RiskVector, session, name, category, endpoint, url, static_folder, menu_class_name, menu_icon_type, menu_icon_value)
    can_delete = True
    column_display_pk = True
    column_hide_backrefs = False
    # column_list = ["id","name","type","vector"]
    # column_searchable_list = ["name"]
    # inline_models = (RiskVector,)
    # column_select_related_list = ["tests.vector_id"]
    column_extra_row_actions = [
        EndpointLinkRowAction('glyphicon glyphicon-arrow-right', 'test.index_view', title="Go to Tests ➡️", id_arg="flt1_0")
    ]

