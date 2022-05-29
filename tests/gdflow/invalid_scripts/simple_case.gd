extends Reference

# This should generate two errors:
# 1 - invalid return type
# 2 - invalid argument for greet function, first argument should be str at line 13

#@ (str, int) -> int
func greet(name, number_of_screamers):
    return number_of_screamers

#@ () -> void
func say_hello():
    greet('sfas', 3)

