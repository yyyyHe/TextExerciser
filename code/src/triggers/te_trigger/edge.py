# -*- coding: utf-8 -*-
from code.src.base.node_info import Node as xml_node


class Edge:
    TYPE_TE = 'TextExerciser'
    TYPE_TRIGGER = 'Trigger'
    ACTION_CLICK = 'Click'
    ACTION_ENTER = 'Enter'
    ACTION_ERROR = 'ERROR'

    def __init__(self, type: str = '', element: xml_node = None, action: str = ''):
        """
        @param type: type: TextExerciser，Trigger
        """
        self.type = type
        if element is not None:
            self.element_index = element.attribute['index']
        else:
            self.element_index = -1
        self.action = action

    def get_element_index(self) -> int:
        return self.element_index
