# -*- coding: utf-8 -*-
"""
@author: kexin.tian
用法描述:
class InstructionFSM(BaseFSM):

    __metaclass__ = MetaclassFSM

    sleeping = State(1, "睡眠",  initial=True)
    running = State(2, "跑步")
    cleaning = State(3, "清洁")

    run = Event(from_states=sleeping, to_state=running)
    cleanup = Event(from_states=running, to_state=cleaning)
    sleep = Event(from_states=(running, cleaning), to_state=sleeping)

    @run.before_hook
    def print_something(self):
        print "Start running!!"

如果需要与orm的model对象或者其他对象做绑定映射

@register_fsm(InstructionFSM, state_value="status", state_remark="remark")
class TestInst(BaseDBDocument):

    meta = {
        'db_alias': 'test'
    }

    target_type = IntField(verbose_name=u"奖惩对象类型", required=True)
    target_id = StringField(verbose_name=u"奖惩对象ID", required=True)
    target_name = StringField(verbose_name=u"奖惩对象",default="")
    status = IntField(verbose_name=u"执行状态")
    remark = StringField(verbose_name=u"备注", default=u"")


i = TestInst()

"""
from thanos_fsm.base import register_fsm, BaseFSM, MetaclassFSM, State, Event

__all__ = ["register_fsm", "BaseFSM", "MetaclassFSM",
           "State", "Event"]
