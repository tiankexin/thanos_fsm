# -*- coding: utf-8 -*-
import functools
import six
from copy import copy


def to_python(value):

    if isinstance(value, six.text_type):
        return value
    else:
        try:
            value = value.decode('utf-8')
        except Exception as e:
            pass
        return value


class InvalidStateTransition(Exception):
    pass


class State(object):

    def __init__(self, value, remark="", name=None, initial=False):

        self.value = value
        self.remark = remark
        self.initial = initial
        self.name = name

    def __repr__(self):
        res = u"<Status:{}# {}:{}>".format(to_python(self.name), self.value, to_python(self.remark))
        return res.encode("utf-8")


class Event(object):

    _before_callback = []

    _after_callback = []

    def __init__(self, to_state, from_states, **kwargs):
        """
        状态流转策略
        :param to_state: 转后后
        :param from_states: 转换前
        :param kwargs: TODO add conditions
        """
        self.to_state = to_state
        self.from_states = tuple()
        if isinstance(from_states, (tuple, list)):
            self.from_states = tuple(from_states)
        else:
            self.from_states = (from_states,)

        self._before_callback = copy(self._before_callback)
        self._after_callback = copy(self._after_callback)

    def before_hook(self, func):
        self._before_callback.append(func)
        return func

    def after_hook(self, func):
        self._after_callback.append(func)
        return func


class MetaclassFSM(type):

    def __new__(mcs, name, bases, attrs):
        mcs.process_attr(attrs)
        cls = type.__new__(mcs, name, bases, attrs)
        return cls

    @classmethod
    def process_attr(mcs, attrs):
        event_dict = {}
        state_dict = {"__value_map__": dict()}
        for k, v in attrs.iteritems():
            if isinstance(v, Event):
                mcs.process_event(event_dict, k, v)
            if isinstance(v, State):
                mcs.process_state(state_dict, k, v)
        attrs.update(event_dict)
        attrs.update(state_dict)

    @classmethod
    def process_event(mcs, event_dict, event_name, event_desc):

        if event_name in event_dict:
            raise RuntimeError("Duplicated Event!")

        def event_method(self):
            if self.__state__ not in event_desc.from_states:
                raise InvalidStateTransition()
            for hook_fn in event_desc._before_callback:
                hook_fn(self)
            # transition state
            self.__state__ = event_desc.to_state

            for hook_fn in event_desc._after_callback:
                hook_fn(self)

        event_dict[event_name] = event_method
        event_dict.setdefault("event_fields", []).append(event_name)

    @classmethod
    def process_state(mcs, state_dict, state_name, state_desc):

        if state_name in state_dict:
            raise RuntimeError("Duplicated State!")

        if state_desc.initial:
            state_dict["__state__"] = state_desc
        is_state_string = "is_" + state_name

        def is_state(self):
            return self.__state__ == state_desc
        state_dict[is_state_string] = property(is_state)

        if state_desc.name is None:
            state_desc.name = state_name
            state_dict[state_name] = state_desc

        state_dict.setdefault("state_fields", []).append(state_name)
        if state_desc.value in state_dict["__value_map__"]:
            raise RuntimeError("Duplicated state value!")
        state_dict["__value_map__"][state_desc.value] = state_desc


class BaseFSM(object):

    __state__ = None

    state_fields = []

    event_fields = []

    __value_map__ = {}

    __bind_instance__ = None

    def reset_by_value(self, value):
        if value not in self.__value_map__:
            raise RuntimeError("Invalid State Value!")
        self.__state__ = self.__value_map__[value]

    def show(self):
        return [getattr(self, field) for field in self.state_fields]

    def iter_state(self):

        for field in self.state_fields:
            state_desc = getattr(self, field)
            yield state_desc.value, state_desc.remark

    @property
    def current(self):
        return self.__state__


class FsmPatcher(object):

    """
    for now only support mongoengine object
    """

    def __init__(self, fsm_cls, **kwargs):
        self.state_value = kwargs.get("state_value", None)
        self.state_remark = kwargs.get("state_remark", None)
        self.fsm_cls = fsm_cls
        self.origin_cls = None

    def modify(self, origin_cls):
        self.origin_cls = origin_cls
        self.modify_init()
        return self.origin_cls

    def modify_event(self, state_fsm):
        def patch_event(event_func):

            @functools.wraps(event_func)
            def inner_wrapper(*args, **kwargs):
                event_func(*args, **kwargs)
                if self.state_value:
                    setattr(state_fsm.__bind_instance__,
                            self.state_value, state_fsm.current.value)
                if self.state_remark:
                    setattr(state_fsm.__bind_instance__,
                            self.state_remark, state_fsm.current.remark)
            return inner_wrapper
        for event_name in state_fsm.event_fields:
            setattr(state_fsm, event_name, patch_event(getattr(state_fsm, event_name)))

    def modify_init(self):
        origin_init = self.origin_cls.__init__

        def change_init_func(obj, *args, **kwargs):
            obj.state_fsm = self.fsm_cls()
            res = origin_init(obj, *args, **kwargs)
            curr_value = getattr(obj, str(self.state_value), None)
            if curr_value is not None:
                obj.state_fsm.reset_by_value(curr_value)
            if self.state_value is not None:
                setattr(obj, self.state_value, obj.state_fsm.current.value)
            if self.state_remark is not None:
                setattr(obj, self.state_remark, obj.state_fsm.current.remark)
            obj.state_fsm.__bind_instance__ = obj
            self.modify_event(obj.state_fsm)
            return res
        self.origin_cls.__init__ = change_init_func


def register_fsm(fsm_cls, **kwargs):
    patcher = FsmPatcher(fsm_cls, **kwargs)

    def wrapper(cls):
        return patcher.modify(cls)
    return wrapper


class FsmFieldFactory(object):

    @classmethod
    def modify(cls, field_type):

        def path_set(self, instance, value):
            super(self.__class__, self).__set__(instance, value)
            instance.state_fsm.reset_by_value(value)
        return type("FsmField", (field_type, ), {"__set__": path_set})


class BoundState(object):

    def __init__(self, state, state_value, state_remark):
        self.state = state
        self.state_value = state_value
        self.state_remark = state_remark

    def __set__(self, instance, value):
        if value != self.state:
            self.state = value
            if self.state_value is not None:
                setattr(instance, self.state_value, self.state.current.value)
            if self.state_remark is not None:
                setattr(instance, self.state_remark, self.state.current.remark)
        else:
            pass

    def __get__(self, instance, owner):
        return self.state
