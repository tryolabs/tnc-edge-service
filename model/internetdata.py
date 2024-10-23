from sqlalchemy import Column, DateTime, Float, Integer, String, text

from .base import Base


class InternetData(Base):
    __tablename__ = "internetdata"

    id = Column(Integer, primary_key=True)
    traceroute = Column(String)
    ping = Column(Float())
    packetloss = Column(Float())
    returncode = Column(Integer())
    datetime = Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    # fk = ForeignKeyConstraint(['id'], [RiskVector.id])

    def __str__(self) -> str:
        return (
            "InternetData("
            + ", ".join(
                [
                    n + "=" + str(self.__getattribute__(n))
                    for n in [
                        "id",
                        "traceroute",
                        "ping",
                        "packetloss",
                        "returncode",
                        "datetime",
                    ]
                ]
            )
            + ")"
        )


from flask_admin.contrib.sqla import ModelView


class InternetDataView(ModelView):
    def __init__(
        self,
        session,
        name=None,
        category=None,
        endpoint=None,
        url=None,
        static_folder=None,
        menu_class_name=None,
        menu_icon_type=None,
        menu_icon_value=None,
    ):
        super().__init__(
            InternetData,
            session,
            name,
            category,
            endpoint,
            url,
            static_folder,
            menu_class_name,
            menu_icon_type,
            menu_icon_value,
        )

    can_delete = True
    column_display_pk = True
    column_hide_backrefs = False
    column_list = ["id", "traceroute", "ping", "packetloss", "returncode", "datetime"]
    # column_searchable_list = ["name"]
    # inline_models = (RiskVector,)
