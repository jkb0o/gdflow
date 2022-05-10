extends Reference

# This should generate two errors:
# 1 - invalid arguments for '+' operator, can't '+' str and int at line 9
# 2 - invalid argument for greet function, first argument should be str at line 13

#@ (str, int) -> str
func greet(name, number_of_screamers):
    return "Hello " + name + number_of_screamers

#@ () -> void
func say_hello():
    greet(2, 3)