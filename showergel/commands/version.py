from showergel.version import get_version
from .main import showergel_cli

@showergel_cli.command()
def version():
    """
    Print Showergel's version and exit
    """
    print(get_version())
