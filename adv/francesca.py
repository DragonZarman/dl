import adv.adv_test
from core.advbase import *

def module():
    return Francesca

class Francesca(Adv):
    a1 = ('fs',0.30)
    conf = {}
    conf['acl'] = """
        `rotation
        """
    conf['rotation_init'] = """
        C4FS C4FS C1- 
    """
    conf['rotation'] = """
        S1 C4FS C4FS C1- S1 C1- S2 C4FS C5- S1 C1- S3 
        C4FS C5- S1 C2- S2 C4FS C5- S1 C4FS C4FS C1- S1 C1- S3 C1- S2 c4fs c5
    """



if __name__ == '__main__':
    conf = {}
    adv.adv_test.test(module(), conf, verbose=0, mass=0)

