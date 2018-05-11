#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import importlib


def lookup_and_import(module_list, name, package=None):

    result = next(((mod_name, class_name) 
                for config_name, mod_name, class_name in module_list
                if name == config_name), None)
    
    if package == None:
        import_module = importlib.import_module('photobooth.' + result[0])
    else:
        import_module = importlib.import_module(
            'photobooth.' + package + '.' + result[0])

    if result[1] == None:
        return import_module
    else:
        return getattr(import_module, result[1])
