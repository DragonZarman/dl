import io
import inspect
import imp

from contextlib import redirect_stdout
from flask import Flask
from flask import request
from flask import jsonify
from flask_cors import CORS

import adv.adv_test
import adv
import slot.a
import slot.d
import slot.w

app = Flask(__name__)
CORS(app)

# Helpers
ROOT_DIR = '/home/wildshinobu/dl/'
MEANS_ADV = {
    'addis': 'addis.py.means.py',
    'sazanka': 'sazanka.py.means.py',
    'victor': 'victor.py.m.py',
    'ezelith': 'ezelith.py.means.py',
}

NORMAL_ADV = ['h_lowen']
MASS_SIM_ADV = []

with open(ROOT_DIR+'chara_quick.txt') as f:
    for l in f:
        NORMAL_ADV.append(l.strip().replace('.py', ''))

with open(ROOT_DIR+'chara_slow.txt') as f:
    for l in f:
        MASS_SIM_ADV.append(l.strip().replace('.py', ''))

# ???
# audric.py.dragon.py
# g_mym.py.dragon.py
# euden.py.dragon.py
# euden.py.dragon.sakuya.py
# lathna.py.dragon.py

SPECIAL_ADV = {
    'chelsea_rollfs': {
        'fn': 'chelsea.py.rollfs.py',
        'nc': ['wp']
    },
    'g_cleo_ehjp': {
        'fn': 'g_cleo.py.ehjp.py',
        'nc': ['wp', 'acl']
    },
    'g_luca_maxstacks': {
        'fn': 'g_luca.py.maxstacks.py',
        'nc': []
    }
}

def get_adv_module(adv_name):
    if adv_name in SPECIAL_ADV or adv_name in MEANS_ADV:
        if adv_name in MEANS_ADV:
            fn = MEANS_ADV[adv_name]
        else:
            fn = SPECIAL_ADV[adv_name]['fn']
        with open('{}{}'.format(ROOT_DIR+'adv/', fn), 'rb') as fp:
            return imp.load_module(
                adv_name, fp, fn,
                ('.py', 'rb', imp.PY_SOURCE)
            ).module()
    else:
        return getattr(
            __import__('adv.{}'.format(adv_name.lower())),
            adv_name.lower()
        ).module()


def is_amulet(obj):
    return (inspect.isclass(obj) and issubclass(obj, slot.a.Amulet)
            and obj.__module__ != 'slot.a'
            and obj.__module__ != 'slot')
def is_dragon(obj):
    return (inspect.isclass(obj) and issubclass(obj, slot.d.DragonBase)
            and obj.__module__ != 'slot.d'
            and obj.__module__ != 'slot')
def is_weapon(obj):
    return (inspect.isclass(obj) and issubclass(obj, slot.d.WeaponBase)
            and obj.__module__ != 'slot.w'
            and obj.__module__ != 'slot')
def list_members(module, predicate, element=None):
    members = inspect.getmembers(module, predicate)
    member_list = []
    for m in members:
        n, c = m
        if element is not None:
            if issubclass(c, slot.d.WeaponBase)  and element not in getattr(c, 'ele'):
                continue
        if c.__qualname__ not in member_list:
            member_list.append(c.__qualname__)
    return member_list

def set_teamdps_res(result, r, suffix=''):
    if r['buff_sum'] > 0:
        result['extra' + suffix]['team_buff'] = '+{}%'.format(round(r['buff_sum'] * 100))
    if r['energy_sum'] > 0:
        result['extra' + suffix]['team_energy'] = '{} stacks'.format(r['energy_sum'])
    return result

def set_log_res(result, r, suffix=''):
    result['logs' + suffix] = r['logs']
    return result

# API
@app.route('/simc_adv_test', methods=['POST'])
def run_adv_test():
    if not request.method == 'POST':
        return 'Wrong request method.'
    params = request.get_json(silent=True)
    adv_name = params['adv'].lower() if 'adv' in params else 'euden'
    wp1 = params['wp1'] if 'wp1' in params else None
    wp2 = params['wp2'] if 'wp2' in params else None
    dra = params['dra'] if 'dra' in params else None
    wep = params['wep'] if 'wep' in params else None
    ex  = params['ex'] if 'ex' in params else ''
    acl = params['acl'] if 'acl' in params else None
    teamdps = abs(float(params['teamdps'])) if 'teamdps' in params else None
    t   = abs(int(params['t']) if 't' in params else 180)
    log = -2
    mass = 25 if adv_name in MASS_SIM_ADV and adv_name not in MEANS_ADV else 0
    print(params)

    if adv_name in SPECIAL_ADV:
        not_customizable = SPECIAL_ADV[adv_name]['nc']
        if 'wp' in not_customizable:
            wp1 = None
            wp2 = None
        if 'acl' in not_customizable:
            acl = None

    adv.adv_test.set_ex(ex)
    adv_module = get_adv_module(adv_name)
    def slot_injection(this):
        if wp1 is not None and wp2 is not None:
            this.conf['slots.a'] = getattr(slot.a, wp1)() + getattr(slot.a, wp2)()
        if dra is not None:
            this.conf['slots.d'] = getattr(slot.d, dra)()
        if wep is not None:
            this.conf['slots.w'] = getattr(slot.w, wep)()
        if teamdps is not None:
            adv.adv_test.team_dps = teamdps
            # assume team dps * 1.25 = raw skill dmg
            adv.adv_test.energy_efficiency = (teamdps * 1.25) * 0.5 * 2 / 5 / adv.adv_test.sim_duration
        else:
            adv.adv_test.team_dps = 6000
            adv.adv_test.energy_efficiency = 7500 * 0.5 * 2 / 5 / adv.adv_test.sim_duration
    def acl_injection(this):
        if acl is not None:
            this.conf['acl'] = acl
    adv_module.slot_backdoor = slot_injection
    adv_module.acl_backdoor = acl_injection

    conf = {}
    for afflic in ['poison', 'paralysis', 'burn', 'blind', 'bog', 'stun', 'freeze', 'sleep']:
        try:
            conf['afflict_res.'+afflic] = min(abs(int(params['afflict_res_'+afflic])), 100)
        except:
            pass
    try:
        if params['sim_afflict_type'] in ['burn', 'paralysis', 'poison']:
            conf['sim_afflict.time'] = t * min(abs(int(params['sim_afflict_time'])), 100)/100
            conf['sim_afflict.type'] = params['sim_afflict_type']
    except:
        pass
    try:
        conf['sim_buffbot.buff'] = min(max(int(params['sim_buff_str']), -100), 100)/100
    except:
        pass
    try:
        conf['sim_buffbot.debuff'] = min(max(int(params['sim_buff_def']), -100), 50)/100
    except:
        pass

    result = {'test_output': '', 'extra': {}, 'extra_no_cond': {}, 'logs': ''}
    f = io.StringIO()
    r = None
    try:
        with redirect_stdout(f):
            r = adv.adv_test.test(adv_module, conf, verbose=log, duration=t, mass=mass)
    except Exception as e:
        result['error'] = str(e)
        return jsonify(result)
    result['test_output'] = f.getvalue()
    f.close()
    if r is not None:
        result = set_teamdps_res(result, r)
        result = set_log_res(result, r)
        if 'no_cond' in r:
            result = set_teamdps_res(result, r['no_cond'], '_no_cond')
            # result = set_log_res(result, r['no_cond'], '_no_cond')

    return jsonify(result)


@app.route('/simc_adv_slotlist', methods=['GET', 'POST'])
def get_adv_slotlist():
    result = {}
    result['adv'] = {}
    if request.method == 'GET':
        result['adv']['name'] = request.args.get('adv', default=None)
    elif request.method == 'POST':
        params = request.get_json(silent=True)
        result['adv']['name'] = params['adv'].lower() if 'adv' in params else None
    else:
        return 'Wrong request method.'
    adv_ele = None
    dragon_module = slot.d
    weap_module = slot.w
    if result['adv']['name'] is not None:
        adv_instance = get_adv_module(result['adv']['name'])(cond=1)
        adv_ele = adv_instance.slots.c.ele.lower()
        result['adv']['ele'] = adv_ele
        dragon_module = getattr(slot.d, adv_ele)
        result['adv']['wt'] = adv_instance.slots.c.wt.lower()
        weap_module = getattr(slot.w, result['adv']['wt'])
        result['adv']['pref_dra'] = type(adv_instance.slots.d).__qualname__
        result['adv']['pref_wep'] = type(adv_instance.slots.w).__qualname__
        result['adv']['pref_wp'] = {
            'wp1': type(adv_instance.slots.a).__qualname__,
            'wp2': type(adv_instance.slots.a.a2).__qualname__
        }
        result['adv']['acl'] = adv_instance.conf.acl
        if 'afflict_res' in adv_instance.conf:
            result['adv']['afflict_res'] = dict(adv_instance.conf.afflict_res)
        else:
            result['adv']['afflict_res'] = None
        if result['adv']['name'] in SPECIAL_ADV:
            result['adv']['no_config'] = SPECIAL_ADV[result['adv']['name']]['nc']
    # result['amulets'] = list_members(slot.a, is_amulet)
    result['dragons'] = list_members(dragon_module, is_dragon, element=adv_ele)
    result['weapons'] = list_members(weap_module, is_weapon, element=adv_ele)
    return jsonify(result)


@app.route('/simc_adv_wp_list', methods=['GET', 'POST'])
def get_adv_wp_list():
    if not (request.method == 'GET' or request.method == 'POST'):
        return 'Wrong request method.'
    result = {}
    result['amulets'] = list_members(slot.a, is_amulet)
    result['adv'] = NORMAL_ADV+MASS_SIM_ADV+list(SPECIAL_ADV.keys())
    return jsonify(result)