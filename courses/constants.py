from nice_types import NiceDict
from nice_types import enum

from departments_constants import DEPT_ABBRS, DEPT_ABBRS_INV, DEPT_ABBRS_SET

__all__ = ["SEMESTER", "EXAMS_PREFERENCE", "PREFIX", "SUFFIX"]

class SEMESTER( enum.Enum ):
    SPRING = enum.EnumValue('spring', 'Spring', abbr='sp')
    SUMMER = enum.EnumValue('summer', 'Summer', abbr='su')
    FALL = enum.EnumValue('fall', 'Fall', abbr='fa')

class PREFIX( enum.Enum ):
    C = enum.EnumValue("C", "Cross-listed")
    H = enum.EnumValue("H", "Honors")
    R = enum.EnumValue("R", "R")

class SUFFIX( enum.Enum ):
    AC = enum.EnumValue("AC", "American Cultures")
