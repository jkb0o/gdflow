from types import MappingProxyType
from typing import List

from lark import Tree

from .problem import Problem

def lint(parse_tree: Tree, config: MappingProxyType) -> List[Problem]:
    return [Problem(
        'Check not implemented',
        'Do something please',
        0, 0
    )]