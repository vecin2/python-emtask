from termcolor import cprint
from nubia import command, argument, context
from emtask.sql.tasks import rewire_verb
from typing import List, Optional

@command
@argument("current_path", description="e.g. CoreEntities.Implementation.Customer.Verbs.InlineSearch")
@argument("new_path", description="This is optional, it prefixes project prefix")
def override_verb(current_path: str,new_path: str=None):
    """
    This will generate an sql script from a template and will run it on db
    """
    #ctx = context.get_context()
    #cprint("Verbose? {}".format(ctx.args.verbose), "yellow")
    rewire_verb(current_path=current_path,
                new_path=new_path
               )
    return 0# optional, by default it's 0


