from tokenize import Token
from types import MappingProxyType
from typing import List
from unittest import result

from lark import Tree

from .problem import Problem

# Plan:
# Parse function statements, write in dict
#   {'function_name': []}
# Parse gdflow statements, write in dict
#   {'function_name': [int,int,string], 'one_more': [string]}
# >> where's first one - return type

# Find fuctions callbacks
# Check validity of using function types

def lint(parse_tree: Tree, config: MappingProxyType) -> List[Problem]:

    disable = config["disable"]

    checks_to_run_w_tree = [
        (
            "gdflow-arith-types",
            _gdflow_arith_types_check,
        ),
        (
            "gdflow-standalone-calls-check",
            _gdflow_standalone_calls_check,
        ),
        (
            "gdflow-parse-all-arguments-statements",
            gdflow_parse_all_arguments_statements
        )

    ]
    problem_clusters = map(
        lambda x: x[1](parse_tree) if x[0] not in disable else [], checks_to_run_w_tree
    )
    problems = [problem for cluster in problem_clusters for problem in cluster]
    return problems

'''
    Tree(standalone_call,
        [
            Token(NAME, 'greet')
            Token(LPAR, '('),
            Token(NUMBER, '2'),
            Token(COMMA, ','),
            Tree(array, [
                Token(NUMBER, '212'),
                Token(COMMA, ','),
                Tree(string, [
                    Token(REGULAR_STRING, "'121'")
                    ]
                ])
            ])
            Token(RPAR, ')')
        ]
    )
'''
def gdflow_parse_all_arguments_statements(parse_tree: Tree) -> dict: # ONLY FOR TEST CASE
    res_dict = {}
    problem = []
    for func_def in parse_tree.find_data("func_def"):
        func_name = func_def.children[0].children[0]
        for func_args in func_def.find_data("func_args"):
            gdflow = gdflow_parse_func_statements(parse_tree)
            gdflow_args = gdflow[func_name]
            _cnt = 1
            if isinstance(func_args, Tree):
                for arg in func_def.find_data("func_arg_regular"):
                    res_dict[arg.children[0].value] = gdflow_args[_cnt]
                    _cnt += 1

        for return_stmt in func_def.find_data("return_stmt"):
            if res_dict[return_stmt.children[0].children[0].value] != gdflow_args[0]:
                problem.append(
                    Problem(
                        name="invalid_return_type",
                        description=f'invalid return type ({return_stmt.children[0].children[0].value}), must be: {gdflow_args[0]}',
                        line=return_stmt.line,
                        column=return_stmt.column,
                    )
                )
    return problem


def gdflow_parse_func_statements(parse_tree: Tree) -> dict:

    func_state_types = {}
    func_name_list = []  # paralleled with dic.keys for indexation

    # Collect func names in statements on main parser stream
    for func_decl in parse_tree.find_data("func_def"):
        func_state_types.update(
            {func_decl.children[0].children[0].value: []}
            )
        func_name_list.append(func_decl.children[0].children[0].value)

    _cnt = 0  # counter for tie names and args by index of statement
    # Collect types of args and return in gdflow parser stream
    for func_decl in parse_tree.find_data("flow_func_decl"):
        if len(func_decl.children) > 1:  # if func have args
            _child_cnt = len(func_decl.children[0].children)
            [
                func_state_types[func_name_list[_cnt]].append(
                    func_decl.children[0].children[i].children[0].value
                    ) for i in range(_child_cnt)
            ]
            # and insert return type on start of types list
            func_state_types[func_name_list[_cnt]].insert(0, func_decl.children[1].children[0].value)
        else:
            func_state_types[func_name_list[_cnt]].insert(0, func_decl.children[0].children[0].value)
        _cnt += 1

    print(func_state_types)
    return func_state_types

def _gdflow_standalone_calls_check(parse_tree: Tree) -> List[Problem]:
    problems = []
    gdflow_types_dict = gdflow_parse_func_statements(parse_tree)
    for call in parse_tree.find_data("standalone_call"):
        func_name = call.children[0]
        func_types_list = parse_types_from_branch(call)
        for count in range(1, len(func_types_list)):
            gdtypes_list = gdflow_types_dict[func_name]
            if simple_types[func_types_list[count-1]] != simple_types[gdtypes_list[count]]:
                problems.append(
                    Problem(
                        name="invalid_call_types",
                        description=f'invalid argument for greet function, {count} argument should be {gdtypes_list[count]}',
                        line=call.line,
                        column=call.column,
                    )
                )
    return problems


def _gdflow_arith_types_check(parse_tree: Tree) -> List[Problem]:
    problems = []
    return problems
    for arith_expr in parse_tree.find_data("arith_expr"):
        types_list = parse_types_from_branch(arith_expr)
        print(f'types_list: {types_list}')
        mem = types_list[0]
        for type_ in types_list:
            if type_ != mem:
                problems.append(
                    Problem(
                        name="invalid_arith_expr_types",
                        description=f"invalid arguments for '+' operator, can't '+' {mem} and {type_} at line 9",
                        line=arith_expr.line,
                        column=arith_expr.column,
                    )
                )
            mem = type_
    return problems


simple_types = {'NUMBER': 'int', 'string': 'str', 'int': 'int', 'str': 'str'}
array_types = ['array', 'dict', 'c_dict_element', 'kv_pair']
types_list = []


# recursive
def parse_types_from_branch(parse_branch: Tree, inner=False):
    for block in parse_branch.children:
        if isinstance(block, Tree):  # if Tree
            _key = block.data
            if _key in array_types:
                _inner_blocks_dict = {}
                _inner_blocks_dict[_key] = []
                for inner_block in block.children:
                    if isinstance(inner_block, Tree):
                        _inner_blocks_dict[_key].append(parse_types_from_branch(inner_block, True))
                    elif inner_block.type in simple_types:
                        if inner:
                            return simple_types[inner_block.type]
                        else:
                            _inner_blocks_dict[_key].append(simple_types[inner_block.type])
                types_list.append(_inner_blocks_dict)
            elif _key in simple_types:
                types_list.append(_key)
        else:  # if Token
            _type = block.type
            if _type in simple_types:
                types_list.append(simple_types[_type])
    return types_list
     


'''def parse_types_from_branch(parse_branch: Tree, first_run=True, key=''):
    # TODO: rewrite to match/case on Python 3.10
    #       try to avoid wait_dic_value argument and checks

    # manager of results
    _result = ''
    for block in parse_branch.children:
        try:  # is Token
            type = block.type  # must throw except if is not token
            print(f'block.type:{block.type}')
            if type == "NUMBER":
                _result = 'int'
            if type == "COMMA":
                pass
            else:
                continue
        except Exception:  # is Tree
            if str(block).startswith('Tree(string,'):
                _result = 'REGULAR_STRING'
            if str(block).startswith('Tree(array,'):
                types_list.append({'array': ''})
                parse_types_from_branch(block, False, 'array')
            if str(block).startswith('Tree(dict,'):
                parse_types_from_branch(block, False)
            if str(block).startswith('Tree(kv_pair,'):
                pass  # useless unit ?
            if str(block).startswith('Tree(c_dict_element,'):
                _inner_key = parse_types_from_branch(block, False)
                key = _inner_key
                _result = _inner_key

            # manager of result
            if key != '':
                print('TRUE')
                types_list[-1][key] = _result
            elif first_run is False:
                return _result
            else:
                types_list.append(_result)
    print(types_list)'''

'''
INPUT: (2, '121', 1.12, [1,2,3], {'as': 21})
MUST BE ON OUT: [int, str, float, {'array':'int'}, {'dict': 'str','int'}]

Tree(standalone_call, [
    Token(NAME, 'greet'),
    Token(LPAR, '('),
    Token(NUMBER, '2'),
    Token(COMMA, ','),
    Tree(string, [
        Token(REGULAR_STRING, "'121'")
        ]),
    Token(COMMA, ','),
    Token(NUMBER, '1.12'),
    Token(COMMA, ','),
    Tree(array, [
        Token(NUMBER, '1'),
        Token(COMMA, ','),
        Token(NUMBER, '2'),
        Token(COMMA, ','),
        Token(NUMBER, '3')
        ]),
    Token(COMMA, ','),
    Tree(dict, [                                        >{down}
        Tree(kv_pair, [                                 > down
            Tree(c_dict_element, [                      >(down0:down1)
                Tree(string, [                          > down
                    Token(REGULAR_STRING, "'as'")]),    > REGULAR_STRING
                Token(NUMBER, '21')])])]),              > NUMBER
    Token(RPAR, ')')])

'''


'''
return [Problem(
        'Check not implemented',
        'Do something please',
        0, 0
    )]'''
