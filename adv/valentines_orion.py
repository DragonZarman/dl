from core.advbase import *
from slot.a import *

def module():
    return Valentines_Orion

class Valentines_Orion(Adv):
    conf = {}
    conf['slots.a'] = The_Shining_Overlord()+Me_and_My_Bestie()
    conf['acl'] = """
        `dragon
        `s3, fsc and not self.s3_buff
        `s4
        `s1
        `fs, x=3
    """
    coab = ['Blade', 'Marth', 'Serena']
    conf['afflict_res.burn'] = 0
    share = ['Ranzal']

    def s1_proc(self, e):
        self.afflics.burn(e.name,100,0.803)

    def s2_proc(self, e):
        Event('defchain')()

if __name__ == '__main__':
    from core.simulate import test_with_argv
    test_with_argv(None, *sys.argv)
