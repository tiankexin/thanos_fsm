# thanos_fsm
## 背景
thanos_fsm是本人研发的从python应用框架thanos中抽离出来的一个通用状态机组件。由于需要用到状态机的场景较多，而网上已有的开源状态机要么实现方式过于暴力、对类对象本身侵入过多，要么使用方式过于繁琐，甚至存在bug。所以本人在这用最pythonic的方式，实现了这个状态机通用组件。
## 安装

```
pip install thanos_fsm
```
如果从原本的PYPI源被墙无法安装,可以通过[https://pypi.org/project/thanos_fsm/0.0.1/#files](https://pypi.org/project/thanos_fsm/0.0.1/#files)手动下载安装.

## 使用范例

### 范例一

```python
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

# ============================
i = InstructionFSM()
i.current          # <Status:await# -1:待执行>
i.is_success       # False
i.is_await         # True
i.show()           # [<Status:success# 1:处理成功>,<Status:doing# 0:处理中>,<Status:await# -1:待执行>,<Status:error# 2:处理失败>]
i.can_exec_start() # True     判断是否能够进行该Event类型操作
i.exec_start()
i.current          # <Status:doing# 0:处理中>
i.exec_success()
i.exec_start()     # 由于已经到达终态，且配置的event中，success 不能再变成doing ， 所以会raise InvalidStateTransition
```

也可以在event函数执行前后增加hook

例如：

```python
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

    @exec_success.before_hook
    def is_task_finish(self):
        if not is_finished():
            raise RuntimeError("Some task not finished!")
        else:
            pass

    @exec_success.after_hook
    def print_something(self):
        print "The task is already finished!"
```

可以自行在变更状态（例如：执行exec_success）之前增加一些额外的判定条件，也可以在状态变更完毕后，增加一些额外的操作.



### 范例二

也可以把范例一中的状态机对象和我们定义好的类对象或者常用的orm框架中的Model实例进行绑定注册，使得状态机的状态和原本实例的状态关联起来，且对原本的实例毫无侵入性，不用担心会触发莫名的bug，更加安全。

```python
# -*- coding: utf-8 -*-
# 例如我们想要把范例一中的指令状态机与mongoengine中我们自己定义的Instruction这个Model对象关联起来
# 且希望状态机对象的value和remark 与Instruction中的status, remark相映射
from mongoengine import *
from thanos_fsm import register_fsm, FsmFieldFactory
from tests.demo1 import InstructionFSM

connect()

@register_fsm(InstructionFSM, state_value="status", state_remark="remark")
class Instruction(Document):

    target_name = StringField(verbose_name=u"指令对象", default="")
    status = FsmFieldFactory.modify(IntField)(verbose_name=u"执行状态")
    remark = StringField(verbose_name=u"备注", default=u"")

i = Instruction(target_name=u"小方")
print i.state_fsm.current # <Status:await# -1:待执行>  如果Instruction的status初始没有值，则会根据状态机对象i.state_fsm.current
print i.status, i.remark  # -1 待执行
i.state_fsm.exec_start()  # Instruction对象的状态机通过state_fsm来控制
print i.state_fsm.current  # <Status:doing# 0:处理中>
print i.status, i.remark  # 0 处理中
# 如果没有通过状态机中注册的event来转移状态，而是直接更改i.status或者i.state_fsm.__state__的值，则视为人工重置状态，改变其中之一，另一个的值也会随之改变，实现了i.status和i.state_fsm.__state__的双向联动
i.status = 2
print i.state_fsm.current  # <Status:error# 2:处理失败>
i.state_fsm.__state__ = i.state_fsm.success
print i.status, i.remark  # 1 处理成功
i.save()

# ================== 从db中读取model对象 ===================
i = Instruction.objects().first()
print i.status, i.remark  # 1 处理成功
print i.state_fsm.current  # <Status:success# 1:处理成功>
```

注意： 虽然正确注册过后的orm model能够保证注册的状态字段和状态机中的value联动，从而保证数据的一致。但既然配置了event，还是推荐通过定义好的event functions来转移状态， 联动只是为了保证人为重置状态后的状态一致性。


注册过后的Fsm，也可以在hook function中拿到被注册的对象，如下所示：

```python
@exec_success.after_hook
def print_something(self):
    target_name = self.__bind_instance__.target_name
    print "The target_name:{} is already finished!".format(target_name)
# 可以在hook function的self.__bind_instance__中拿到被注册的实例对象
```



## Thanks

后续会陆续更新thanos的其他组件，欢迎讨论~

***

## Background
Tanos_fsm is a generic state machine component which extracted from the python application framework thanos. There are many scenes that need to use the state machine, but the existing open source state machine is either too violent, too intrusive to the class object itself, or too cumbersome to use, or even bugs. So I implemented this state machine generic component in the most pythonic way.

## Install

```
pip install thanos_fsm
```
If the original PYPI source cannot be installed, you can manually download and install it from [https://pypi.org/project/thanos_fsm/0.0.1/#files](https://pypi.org/project/thanos_fsm/0.0.1/#files).

## Quick Start

### Example 1
```python
from thanos_fsm import State, Event, BaseFSM, MetaclassFSM

class InstructionFSM(BaseFSM):

    __metaclass__ = MetaclassFSM

    await = State(-1, "await", initial=True)
    doing = State(0, "doing")
    success = State(1, "success")
    error = State(2, "failed")

    exec_start = Event(from_states=await, to_state=doing)
    exec_success = Event(from_states=doing, to_state=success)
    exec_error = Event(from_states=doing, to_state=error)

# ============================
i = InstructionFSM()
i.current          # <Status:await# -1:await>
i.is_success       # False
i.is_await         # True
i.show()           # [<Status:success# 1:success>,<Status:doing# 0:doing>,<Status:await# -1:await>,<Status:error# 2:failed>]
i.can_exec_start() # True     Determine whether the Event type function can be called
i.exec_start()
i.current          # <Status:doing# 0:doing>
i.exec_success()
i.exec_start()     # Since it has reached the final state and the configured event function, state success can't transfer to the doing state, it will raise InvalidStateTransition exception.
```

You can also add hooks before and after the execution of the event function.
Like this：

```python
from thanos_fsm import State, Event, BaseFSM, MetaclassFSM

class InstructionFSM(BaseFSM):

    __metaclass__ = MetaclassFSM

    await = State(-1, "await", initial=True)
    doing = State(0, "doing")
    success = State(1, "success")
    error = State(2, "failed")

    exec_start = Event(from_states=await, to_state=doing)
    exec_success = Event(from_states=doing, to_state=success)
    exec_error = Event(from_states=doing, to_state=error)

    @exec_success.before_hook
    def is_task_finish(self):
        if not is_finished():
            raise RuntimeError("Some task not finished!")
        else:
            pass

    @exec_success.after_hook
    def print_something(self):
        print "The task is already finished!"
```
You can add some additional decision conditions before changing the state (for example, execute exec_success), or add some extra operations after the state change.

### example 2

You can also bind the state machine object in the first example to the class object we defined or the Model instance in the common ORM framework, so that the state of the state machine is associated with the state of the original instance。This operation is not intrusive to the original instance, no need to worry about triggering inexplicable bugs, it is more secure.

```python
# -*- coding: utf-8 -*-
# For example, we want to associate the instruction state machine in example one with the Model object of our own defined Instruction in mongoengine.
# And hope that the value and remark of the state machine object are mapped to the status and remark in the Instruction.
from mongoengine import *
from thanos_fsm import register_fsm, FsmFieldFactory
from tests.demo1 import InstructionFSM

connect()

@register_fsm(InstructionFSM, state_value="status", state_remark="remark")
class Instruction(Document):

    target_name = StringField(verbose_name=u"target", default="")
    status = FsmFieldFactory.modify(IntField)(verbose_name=u"status")
    remark = StringField(verbose_name=u"remark", default=u"")

i = Instruction(target_name=u"xiao fang")
print i.state_fsm.current # <Status:await# -1:await>  If the status of the Instruction does not initially have a value, it will be based on the state machine object i.state_fsm.current's value
print i.status, i.remark  # -1 await
i.state_fsm.exec_start()  # The state machine of the Instruction object is controlled by state_fsm
print i.state_fsm.current  # <Status:doing# 0:doing>
print i.status, i.remark  # 0 doing
# If you do not transfer the state through the event function registered in the state machine, but directly change the value of i.status or i.state_fsm.__state__, it is regarded as a manual reset state, change one of them, the other value will also follow The change realizes the two-way linkage between i.status and i.state_fsm.__state__
i.status = 2
print i.state_fsm.current  # <Status:error# 2:failed>
i.state_fsm.__state__ = i.state_fsm.success
print i.status, i.remark  # 1 success
i.save()

# ================== query model from database ===================
i = Instruction.objects().first()
print i.status, i.remark  # 1 success
print i.state_fsm.current  # <Status:success# 1:success>
```

Note: Although the data is consistent because of the correctly registered orm model can guarantee the linkage between the registered status field and the value in the state machine. However, it is recommended to transfer the state through the defined event functions since the event is configured. The linkage is only to ensure the state consistency after the reset state.


Registered Fsm can also get the registered object in the hook function as follows:

```python
@exec_success.after_hook
def print_something(self):
    target_name = self.__bind_instance__.target_name
    print "The target_name:{} is already finished!".format(target_name)
# 可以在hook function的self.__bind_instance__中拿到被注册的实例对象
```



## Thanks

Follow-up will continue to update other components of thanos, welcome to discuss ~