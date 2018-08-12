# -*- coding: utf-8 -*-

from thanos_fsm import State, Event, BaseFSM, MetaclassFSM


class InstructionFSM(BaseFSM):

    __metaclass__ = MetaclassFSM

    await = State(-1, "待执行", initial=True)
    doing = State(0, "处理中")
    success = State(1, "处理成功")
    error = State(2, "处理失败")

    exec_start = Event(from_states=await, to_state=doing)
    exec_success = Event(from_states=doing, to_state=success)
    exec_error = Event(from_states=doing, to_state=error)

if __name__ == "__main__":

    i = InstructionFSM()
    print i.current          # <Status:await# -1:待执行>
    print i.is_success       # False
    print i.is_await         # True
    print i.show()  # [<Status:success# 1:处理成功>,<Status:doing# 0:处理中>,<Status:await# -1:待执行>,<Status:error# 2:处理失败>]
    i.exec_start()
    print i.current          # <Status:doing# 0:处理中>
    i.exec_success()
    print i.exec_start()     # 由于已经到达终态，且配置的event中，success 不能再变成doing ， 所以会raise InvalidStateTransition
