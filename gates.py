from db import *

def list_categories():
    return get_categories()

def create_category(name):
    add_category(name)

def remove_category(cat_id):
    delete_category(cat_id)

def create_gate(cat_id, name, command, sites=None, extra=""):
    add_gate(cat_id, name, command, sites, extra)

def remove_gate(gate_id):
    delete_gate(gate_id)

def get_gates_for_category(cat_id):
    return get_gates_by_category(cat_id)

def get_gate_details(command):
    return get_gate_by_command(command)

def get_all_gates_info():
    return get_all_gates()

def get_gate_details_by_id(gate_id):
    return get_gate_by_id(gate_id)
