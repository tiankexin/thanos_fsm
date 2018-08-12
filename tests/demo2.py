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

    @exec_success.after_hook
    def print_something(self):
        target_name = self.__bind_instance__.target_name
        print "The target_name:{} transition is already finished!".format(target_name)


@register_fsm(InstructionFSM, state_value="status", state_remark="remark")
class Instruction(Document):

    target_name = StringField(verbose_name=u"指令对象", default="")
    status = FsmFieldFactory.modify(IntField)(verbose_name=u"执行状态")
    remark = StringField(verbose_name=u"备注", default=u"")


if __name__ == "__main__":
    i = Instruction(target_name="小方")
    print i.state_fsm.current
    print i.status, i.remark
    i.state_fsm.exec_start()
    print i.state_fsm.current
    print i.status, i.remark
    i.status = 2
    print i.state_fsm.current
    i.state_fsm.__state__ = i.state_fsm.success
    print i.status, i.remark
    i.save()

    # ================== 从db中读取model对象 ===================
    i = Instruction.objects().first()
    print i.status, i.remark  # 1 处理成功
    print i.state_fsm.current  # <Status:success# 1:处理成功>

    i.status = 0
    i.state_fsm.exec_success()

