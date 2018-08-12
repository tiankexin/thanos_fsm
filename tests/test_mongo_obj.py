# -*- coding: utf-8 -*-
from mongoengine import *
from thanos_fsm import *

connect()


class InstructionFSM(BaseFSM):

    __metaclass__ = MetaclassFSM

    await = State(-1, "待执行", initial=True)
    doing = State(0, "处理中")
    success = State(1, "处理成功")
    error = State(2, "处理失败")

    exec_start = Event(from_states=await, to_state=doing)
    exec_success = Event(from_states=doing, to_state=success)
    exec_error = Event(from_states=doing, to_state=error)


@register_fsm(InstructionFSM, state_value="status", state_remark="remark")
class Instruction(Document):

    target_name = StringField(verbose_name=u"奖惩对象", default="")
    status = IntField(verbose_name=u"执行状态", default=-1)
    remark = StringField(verbose_name=u"备注", default=u"")


i = InstructionFSM()
# print i.__state__
# print i.__value_map__
