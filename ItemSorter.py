from phBot import *
from threading import Timer
from time import sleep

import QtBind
import struct
import copy
import binascii  # for debugging

debug = False

gui = QtBind.init(__name__, 'ItemSorter')

QtBind.createButton(gui, 'sorter_start_inventory', 'sort inventory', 5, 5)
QtBind.createButton(gui, 'sorter_start_storage', 'sort storage', 5, 5 + 30)
QtBind.createButton(gui, 'sorter_start_guild_storage', 'sort guild-storage', 5, 5 + 60)
QtBind.createButton(gui, 'sorter_stop', 'stop processing', 5, 5 + 120)

running = False
timers = []

npc_servernames = {
    'storage': [
        'NPC_CH_WAREHOUSE_M',  # jangan #1
        'NPC_CH_WAREHOUSE_W',  # jangan #2
        'NPC_EU_WAREHOUSE',  # constantinople
        'NPC_WC_WAREHOUSE_M',  # donwhang #1
        'NPC_WC_WAREHOUSE_W',  # donwhang #2
        'NPC_CA_WAREHOUSE',  # samarkand
        'NPC_KT_WAREHOUSE',  # hotan
        'NPC_AR_WAREHOUSE',  # bagdad
        'NPC_SD_M_AREA_WAREHOUSE',  # alexandria south
        'NPC_SD_T_AREA_WAREHOUSE2'  # alexandria north
    ],
    'guild_storage': [
        'NPC_CH_GENARAL_SP',  # jangan
        'NPC_WC_GUILD',  # donwhang
        'NPC_SD_M_AREA_GUILD',  # alexandria south
        'NPC_SD_T_AREA_GUILD2'  # alexandria north
    ]
}

def inject_client(opcode, data, encrypted):
    global debug
    if debug:
        log('[%s] bot to client' % (__name__))
        log('[%s] \topcode: 0x%02X' % (__name__, opcode))
        if data is not None:
            log('[%s] \tdata: %s' % (__name__, binascii.hexlify(data)))
    return inject_silkroad(opcode, data, encrypted)


def inject_server(opcode, data, encrypted):
    global debug
    if debug:
        log('[%s] bot to server' % (__name__))
        log('[%s] \topcode: 0x%02X' % (__name__, opcode))
        if data is not None:
            log('[%s] \tdata: %s' % (__name__, binascii.hexlify(data)))
    return inject_joymax(opcode, data, encrypted)


def handle_silkroad(opcode, data):
    global running
    if running == 'guild_storage':
        if opcode in [0x7250, 0x7251, 0x7252]:
            return False
    return True


def sorter_start_inventory():
    global running
    if running != False:
        return
    running = 'inventory'
    log('[%s] started' % (__name__))
    timers.append(Timer(1, do_sort, [running]).start())


def sorter_start_storage():
    global running
    if running != False:
        return
    running = 'storage'
    log('[%s] started' % (__name__))
    timers.append(Timer(1, do_sort, [running]).start())


def sorter_start_guild_storage():
    global running
    if running != False:
        return
    running = 'guild_storage'
    log('[%s] started' % (__name__))
    timers.append(Timer(1, do_sort, [running]).start())


def sorter_stop():
    global timers
    global running
    if running == False:
        return
    for t in timers:
        if t is not None:
            t.cancel()
    timers = []
    if running == 'inventory':
        pass
    elif running == 'storage':
        storage_close(0)
        npc_unselect(0)
    elif running == 'guild_storage':
        guild_storage_unlock()
        guild_storage_close(0)
        npc_unselect(0)
    running = False
    log('[%s] stopped' % (__name__))


def npc_get_id(type):
    global npc_servernames
    npc_keys = array_get_subkey_filterd_keys(get_npcs(), 'servername', npc_servernames[type])
    if len(npc_keys) == 0:
        return False
    return struct.pack('<H', npc_keys[0])


def npc_select(type, timeout=1.0):
    if get_locale() == 18: # iSRO
        opcode = 0x7045
    elif get_locale() == 22: # vSRO
        opcode = 0x7C45
    else:
        return False
    npc_id = npc_get_id(type)
    if npc_id == False:
        return False
    packet = bytearray(npc_id)
    packet += b'\x00\x00'
    inject_server(opcode, packet, False)
    sleep(timeout)


def npc_unselect(timeout=1.0):
    packet = bytearray(b'\x01')
    inject_client(0xB04B, packet, False)
    sleep(timeout)


def guild_storage_lock(timeout=1.0):
    npc_id = npc_get_id('guild_storage')
    if npc_id == False:
        return False
    packet = bytearray(npc_id)
    packet += b'\x00\x00'
    inject_server(0x7250, packet, False)
    sleep(timeout)


def guild_storage_unlock(timeout=1.0):
    npc_id = npc_get_id('guild_storage')
    if npc_id == False:
        return False
    packet = bytearray(npc_id)
    packet += b'\x00\x00'
    inject_server(0x7251, packet, False)
    sleep(timeout)


def storage_refresh(timeout=1.0):
    npc_id = npc_get_id('storage')
    if npc_id == False:
        return False
    packet = bytearray(npc_id)
    packet += b'\x00\x00\x00'
    inject_server(0x703C, packet, False)
    sleep(timeout)


def guild_storage_refresh(timeout=1.0):
    npc_id = npc_get_id('guild_storage')
    if npc_id == False:
        return False
    packet = bytearray(npc_id)
    packet += b'\x00\x00'
    inject_server(0x7252, packet, False)
    sleep(timeout)


def storage_open(timeout=1.0):
    npc_id = npc_get_id('storage')
    if npc_id == False:
        return False
    packet = bytearray(npc_id)
    packet += b'\x00\x00\x03'
    inject_server(0x7046, packet, False)
    sleep(timeout)


def guild_storage_open(timeout=1.0):
    npc_id = npc_get_id('guild_storage')
    if npc_id == False:
        return False
    packet = bytearray(npc_id)
    packet += b'\x00\x00\x0f'
    inject_server(0x7046, packet, False)
    sleep(timeout)


def storage_close(timeout=1.0):
    npc_id = npc_get_id('storage')
    if npc_id == False:
        return False
    packet = bytearray(npc_id)
    packet += b'\x00\x00'
    inject_server(0x704B, packet, False)
    sleep(timeout)


def guild_storage_close(timeout=1.0):
    npc_id = npc_get_id('guild_storage')
    if npc_id == False:
        return False
    packet = bytearray(npc_id)
    packet += b'\x00\x00'
    inject_server(0x704B, packet, False)
    sleep(timeout)


def move_item(type, source_slot, destination_slot, timeout=1.0):
    if (
            get_items(type)['size'] == 0
            or source_slot > get_items(type)['size']
            or source_slot < 0
            or destination_slot > get_items(type)['size']
            or destination_slot < 0
            or (
            get_items(type)['items'][source_slot] is None
            and
            get_items(type)['items'][destination_slot] is None
    )
    ):
        return False
    packet = bytearray()
    if type == 'inventory':
        packet += b'\x00'
    elif type == 'storage':
        packet += b'\x01'
    elif type == 'guild_storage':
        packet += b'\x1d'
    packet.append(source_slot)
    packet.append(destination_slot)
    packet += struct.pack('<H', get_items(type)['items'][source_slot]['quantity'])
    if type == 'storage' or type == 'guild_storage':
        npc_id = npc_get_id(type)
        if npc_id == False:
            return False
        packet += npc_id
        packet += b'\x00\x00'
    inject_server(0x7034, packet, False)
    sleep(timeout)


def array_sort_by_subkey(array, subkey):
    if not isinstance(array, (list, dict)):
        return Falseubkey(array, subkey)
    sorted_array = copy.deepcopy(array)
    for i, elem in enumerate(sorted_array):
        if not isinstance(elem, (list, dict)):
            sorted_array[i] = elem = {subkey: ''}
        if subkey not in elem:
            sorted_array[i] = elem = {subkey: ''}
        for o, subelem in elem.items():
            if not isinstance(subelem, (int, str)):
                sorted_array[i][o] = ''
    sorted_array = sorted(sorted_array, key=lambda subarray: subarray[subkey], reverse=True)
    return sorted_array


def array_get_subkey_filterd_keys(array, subkey, values):
    keys = []
    if isinstance(array, list):
        for i, subarray in enumerate(array):
            if not isinstance(subarray, (list, dict)):
                continue
            if isinstance(subarray, dict):
                if not subkey in subarray:
                    continue
            if not isinstance(values, list):
                values = [values]
            for value in values:
                if subarray[subkey] == value:
                    keys.append(i)
    elif isinstance(array, dict):
        for i, subarray in array.items():
            if not isinstance(subarray, (list, dict)):
                continue
            if isinstance(subarray, dict):
                if not subkey in subarray:
                    continue
            if not isinstance(values, list):
                values = [values]
            for value in values:
                if subarray[subkey] == value:
                    keys.append(i)
    else:
        return False
    return keys

def get_items(type):
    if type == 'inventory':
        return get_inventory()
    elif type == 'storage':
        return get_storage()
    elif type == 'guild_storage':
        return get_guild_storage()
    return False

def do_sort(type):
    if type == 'storage':
        npc_select(type)
        storage_open()
        storage_refresh()
    elif type == 'guild_storage':
        npc_select(type)
        guild_storage_open()
        guild_storage_lock()
        guild_storage_refresh()
    item_start_slot = 0
    if type == 'inventory':
        item_start_slot = 13
    for i in range(item_start_slot, get_items(type)['size']):
        sorted_items = array_sort_by_subkey(get_items(type)['items'][i:], 'servername')
        if sorted_items == False or len(sorted_items) == 0:
            continue
        item_slots = array_get_subkey_filterd_keys(get_items(type)['items'][i:], 'servername',
                                                   sorted_items[0]['servername'])
        if item_slots == False or len(item_slots) == 0:
            break
        if i + item_slots[0] == i:
            continue
        log('[%s] moving slot %i to slot %i' % (__name__, i + item_slots[0], i))
        if move_item(type, i + item_slots[0], i) == False:
            log('[%s] error: unable to move slot %i to slot %i' % (__name__, i + item_slots[0], i))
            break
    if type == 'storage':
        storage_close()
        npc_unselect()
    elif type == 'guild_storage':
        guild_storage_unlock()
        guild_storage_close()
        # npc_unselect()
    sorter_stop()


log('[%s] loaded' % (__name__))
