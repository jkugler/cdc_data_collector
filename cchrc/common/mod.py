import os

def mod_list(dir):
    """
    A quick function that retrieves all the sub modules in a directory that has
    an __init__.py file.  I could use pkgutil.iter_modules, but was hitting an
    odd bug I'd rather not spend time debugging it as this exists and works.
    """

    modList = []
    modHash = {}
    isModule = False
    for ii in os.walk(dir):
        if ii[0] == dir:
            for f in ii[2]:
                # If there is no __init__ file, then the directory
                # upon which mod_list() is operating is not a module
                if f[0:8] == '__init__':
                    isModule = True
                elif f[-3:] == '.py':
                    modHash[f[:-3]] = True
                elif f[-4:] == '.pyc' or f[-4:] == '.pyo':
                    modHash[f[:-4]] = True
    if isModule:
        modList = modHash.keys()
        modList.sort()
        return(modList)
    else:
        # Returning an empty list allows 'in' tests since a list is iterable,
        # and None isn't
        return([])

def get(context, name):
    return __import__(context + '.' + name, globals(), locals(), [context])
