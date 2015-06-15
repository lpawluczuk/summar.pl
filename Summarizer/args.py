from my_exceptions import ArgumentParserException

def check_arg(arg, name):
    if not arg:
        raise ArgumentParserException(name)

def check_args_dict(args_with_names_dict):
    for arg in args_with_names_dict.keys():
        check_arg(args_with_names_dict[arg], arg)        
