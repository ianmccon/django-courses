#!/usr/bin/env python
from django.core.management import setup_environ
from django.core.exceptions import ObjectDoesNotExist
import re, django, sys, pickle, glob, os, os.path
from xml.dom import minidom


# "OFFICIAL ABBR" : ("UNOFFICIAL ABBR", others...)
DEPT_ABBRS = {
    "ASTRON": ("ASTRO",),
    "BIOLOGY": ("BIO",),
    "BIO ENG": ("BIOE",),
    "UGBA": ("BA",),
    "CHM ENG": ("CHEME",),
    "CIV ENG": ("CIVE", "CEE", "CE", "CIVIL ENGINEERING",),
    "COG SCI": ("COGSCI",),
    "COMPSCI": ("CS",),
    "EL ENG": ("EE",),
    "ENGIN": ("E", "ENG", "ENGINEERING"),
    "HISTORY": ("HIST",), 
    "IND ENG": ("IEOR",),
    "INTEGBI": ("IB",),
    "LINGUIS": ("LING",), 
    "MAT SCI": ("MSE",),
    "MEC ENG": ("ME",),
    "MCELLBI": ("MCB",),
    "PHYSICS": ("PHYS",),
    "POL SCI": ("POLISCI", "PS"), #not actually used
    "STAT": ("STAT", "STATS",),
    "S,SEASN": ("SSEASN", "S,SEASN",),
    "ECON": ("ECON", "ECONOMICS",),
    "UGIS": ("IDS",),
    "ENV SCI" : ("ENV SCI", "ENVIR SCI"),
    "ENVECON" : ("ENVECON", "ENVIR ECON & POLICY"),
    }
DEPT_ABBRS_INV = {}
DEPT_ABBRS_SET = set()



def main():
    for k, v in DEPT_ABBRS.items():
        if k not in v:
            v = list(v) + [k]
            DEPT_ABBRS[k] = v
        for e in v:
            DEPT_ABBRS_INV[e] = k
        DEPT_ABBRS_INV[k] = k
        DEPT_ABBRS_SET.add(k)
        DEPT_ABBRS_SET.update(v)

    departmentFile = os.path.join(os.getcwd(), os.path.dirname(__file__), "data", "departments-sanitized.xml")
    dom = minidom.parse(file(departmentFile, "r"))
    for department in dom.getElementsByTagName("department"):   
        abbr = department.getAttribute('abbr').strip().upper()
        if abbr in DEPT_ABBRS_SET:
            continue
        DEPT_ABBRS[abbr] = (abbr,)
        DEPT_ABBRS_INV[abbr] = abbr
        DEPT_ABBRS_SET.add(abbr)

main()

