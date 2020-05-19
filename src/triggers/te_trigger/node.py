# -*- coding: utf-8 -*-
from src.base.xml_builder import XmlTree
from src.base.node_info import Node as xml_node
import hashlib
from src.base.node_info import EDIT_CLASS as edit_class


class Node:
    """
    The node of ui exploration graph
    """
    def __init__(self, page: XmlTree, activity: str):
        self.page = page
        self.class_dict = page.ClassDict
        self.activity = activity
        self.clickable_elements = page.AllClickableElements
        self.button_elements = page.ButtonNodes
        self.edit_elements = page.EditNodes
        for i, element in enumerate(self.clickable_elements):
            element.attribute['is_clicked'] = False
            element.attribute['explore_count'] = 0
            element.attribute['index'] = i
        self.is_has_edit = True if page.EditNodes else False
        self.id = self.calculate_node_id()
        self.addition_res = []
        self.last_ig_input = None
        self.clickable_elements_for_te = self.get_clickable_e_for_te(page)

    def get_clickable_e_for_te(self, page: XmlTree) -> list:
        w_nodes = [e for e in page.ButtonNodes + page.ClickableNodes + page.NoEnabledClickNodes if e.attribute['classType'] not in edit_class]
        f_nodes = list(set(w_nodes))
        f_nodes.sort(key=w_nodes.index)
        return f_nodes

    def reset_exercised_state(self):
        for e in self.clickable_elements_for_te:
            e.is_explored_in_mutation = False

    def is_need_exercise(self):
        if not self.clickable_elements_for_te:
            return True
        return True if [element for element in self.clickable_elements_for_te if not element.is_explored_in_mutation] else False

    def log_addition_res(self, res: [str]):
        self.addition_res.extend(res)

    def log_last_input(self, last_input):
        self.last_ig_input = last_input

    def calculate_node_id(self) -> str:
        if self.edit_elements:
            id_text = self.activity
            id_text += str([e.attribute['classType'] + e.attribute['resourceID'] for e in self.edit_elements])
        else:
            id_text = str({self.activity: self.class_dict})
        id_text += str([element.attribute['text'] for element in self.button_elements])
        return hashlib.md5(id_text.encode()).hexdigest()

    def get_unclicked_elements(self) -> [xml_node]:
        return [node for node in self.clickable_elements if not node.attribute['is_clicked']]

    def get_element_by_index(self, index: int) -> xml_node:
        for element in self.clickable_elements:
            if element.attribute['index'] == index:
                return element

    def is_same_node(self, node) -> bool:
        return self.id == node.id
