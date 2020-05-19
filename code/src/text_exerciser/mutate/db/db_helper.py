# -*- coding: utf-8 -*-
import sqlite3
import os

db_path = '%s/input.db' % os.path.dirname(__file__)

def get_hints_by_type(type: str) -> str:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("select t_content from inputType_hints where t_type = '%s'" % type)
    item = cursor.fetchall()[0]
    cursor.close()
    conn.commit()
    conn.close()
    return item


def get_tags_by_type(type: str) -> (int, [str]):
    tags = []
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("select t_tags from inputType_tag where t_type = '%s'" % type)
    for row in cursor:
        tags.extend(row[0].split(','))
    cursor.close()
    conn.commit()
    conn.close()
    return tags


def get_all_types() -> [str]:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("select distinct t_type from inputType_tag")
    types = [row[0] for row in cursor]
    cursor.close()
    conn.commit()
    conn.close()
    return types


def get_type_order(type: str) -> int:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("select t_order from inputType_tag where t_type = '%s'" % type)
    order = [row[0] for row in cursor]
    cursor.close()
    conn.commit()
    conn.close()
    return max(order)
