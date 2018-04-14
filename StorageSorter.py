from phBot import *
from threading import Timer
from time import sleep

import QtBind
import struct
import copy
import binascii  # for debugging

debug = False

gui = QtBind.init(__name__, 'StorageSorter')

padding_left = 373
padding_top = 164

QtBind.createButton(gui, 'sorter_start_storage', 'sort storage', padding_left - 37, padding_top - 46)
QtBind.createButton(gui, 'sorter_start_guild_storage', 'sort guild-storage', padding_left - 46, padding_top - 46 + 30)
QtBind.createLabel(gui, '-----------------------', padding_left - 45, padding_top - 46 + 55)
QtBind.createButton(gui, 'sorter_stop', 'stop processing', padding_left - 41, padding_top - 46 + 70)

running = False
timers = []

if get_locale() == 18:
    # iSRO
    timeout_default = 1.0
elif get_locale() == 22:
    # vSRO (LegionSRO, ...)
    timeout_default = 0.5
else:
    timeout_default = 1.0

npc_storage_servernames = [
    'NPC_CH_WAREHOUSE_M',  # jangan #1
    'NPC_CH_WAREHOUSE_W',  # jangan #2
    'NPC_EU_WAREHOUSE',  # constantinople
    'NPC_WC_WAREHOUSE_M',  # donwhang #1
    'NPC_WC_WAREHOUSE_W',  # donwhang #2
    'NPC_CA_WAREHOUSE',  # samarkand
    'NPC_KT_WAREHOUSE',  # hotan
    'NPC_AR_WAREHOUSE',  # bagdad
    'NPC_SD_M_AREA_WAREHOUSE',  # alexandria south
    'NPC_SD_T_AREA_WAREHOUSE2',  # alexandria north
]

npc_guild_storage_servernames = [
    'NPC_CH_GENARAL_SP',  # jangan
    'NPC_WC_GUILD',  # donwhang
    'NPC_SD_M_AREA_GUILD',  # alexandria south
    'NPC_SD_T_AREA_GUILD2',  # alexandria north
]


def inject_client(opcode, data, encrypted):
    global debug
    if debug:
        log('[%s]: bot to client' % (__name__))
        log('[%s]: \topcode: 0x%02X' % (__name__, opcode))
        if data is not None:
            log('[%s]: \tdata: %s' % (__name__, binascii.hexlify(data)))
    return inject_silkroad(opcode, data, encrypted)


def inject_server(opcode, data, encrypted):
    global debug
    if debug:
        log('[%s]: bot to server' % (__name__))
        log('[%s]: \topcode: 0x%02X' % (__name__, opcode))
        if data is not None:
            log('[%s]: \tdata: %s' % (__name__, binascii.hexlify(data)))
    return inject_joymax(opcode, data, encrypted)


def handle_silkroad(opcode, data):
    global running
    if running == 'guild_storage':
        if opcode in [0x7250, 0x7251, 0x7252]:
            return False
    return True


def sorter_start_storage():
    global running
    if running != False:
        return
    running = 'storage'
    log('[%s] started' % (__name__))
    timers.append(Timer(1, do_sort, ['storage']).start())


def sorter_start_guild_storage():
    global running
    if running != False:
        return
    running = 'guild_storage'
    log('[%s] started' % (__name__))
    timers.append(Timer(1, do_sort, ['guild_storage']).start())


def sorter_stop():
    global timers
    global running
    if running == False:
        return
    for t in timers:
        if t is not None:
            t.cancel()
    timers = []
    if running == 'storage':
        storage_close(0)
        storage_unselect(0)
    elif running == 'guild_storage':
        guild_storage_unlock()
        guild_storage_close(0)
        guild_storage_unselect(0)
    running = False
    log('[%s] stopped' % (__name__))


def npc_get_storage_id():
    global npc_storage_servernames
    storage_npc_keys = array_get_subkey_filterd_keys(get_npcs(), 'servername', npc_storage_servernames)
    if len(storage_npc_keys) == 0:
        return b'\x00\x00'
    return struct.pack('<H', storage_npc_keys[0])


def npc_get_guild_storage_id():
    global npc_guild_storage_servernames
    storage_npc_keys = array_get_subkey_filterd_keys(get_npcs(), 'servername', npc_guild_storage_servernames)
    if len(storage_npc_keys) == 0:
        return b'\x00\x00'
    return struct.pack('<H', storage_npc_keys[0])


def storage_select(timeout=0.0):
    global timeout_default
    if timeout == 0.0:
        timeout = timeout_default
    if get_locale() == 18:
        # iSRO
        opcode = 0x7045
    elif get_locale() == 22:
        # vSRO (LegionSRO, ...)
        opcode = 0x7C45
    else:
        return False
    npc_id = npc_get_storage_id()
    if npc_id == False:
        return False
    packet = bytearray(npc_id)
    packet += b'\x00\x00'
    inject_server(opcode, packet, False)
    sleep(timeout)


def guild_storage_select(timeout=0.0):
    global timeout_default
    if timeout == 0.0:
        timeout = timeout_default
    if get_locale() == 18:
        # iSRO
        opcode = 0x7045
    elif get_locale() == 22:
        # vSRO (LegionSRO, ...)
        opcode = 0x7C45
    else:
        return False
    npc_id = npc_get_guild_storage_id()
    if npc_id == False:
        return False
    packet = bytearray(npc_id)
    packet += b'\x00\x00'
    inject_server(opcode, packet, False)
    sleep(timeout)


def storage_unselect(timeout=0.0):
    global timeout_default
    if timeout == 0.0:
        timeout = timeout_default
    packet = bytearray(b'\x01')
    inject_client(0xB04B, packet, False)
    sleep(timeout)


def guild_storage_unselect(timeout=0.0):
    global timeout_default
    if timeout == 0.0:
        timeout = timeout_default
    packet = bytearray(b'\x01')
    inject_client(0xB04B, packet, False)
    sleep(timeout)


def guild_storage_lock(timeout=0.0):
    global timeout_default
    if timeout == 0.0:
        timeout = timeout_default
    npc_id = npc_get_guild_storage_id()
    if npc_id == False:
        return False
    packet = bytearray(npc_id)
    packet += b'\x00\x00'
    inject_server(0x7250, packet, False)
    sleep(timeout)


def guild_storage_unlock(timeout=0.0):
    global timeout_default
    if timeout == 0.0:
        timeout = timeout_default
    npc_id = npc_get_guild_storage_id()
    if npc_id == False:
        return False
    packet = bytearray(npc_id)
    packet += b'\x00\x00'
    inject_server(0x7251, packet, False)
    sleep(timeout)


def storage_refresh(timeout=0.0):
    global timeout_default
    if timeout == 0.0:
        timeout = timeout_default
    npc_id = npc_get_storage_id()
    if npc_id == False:
        return False
    packet = bytearray(npc_id)
    packet += b'\x00\x00\x00'
    inject_server(0x703C, packet, False)
    sleep(timeout)


def guild_storage_refresh(timeout=0.0):
    global timeout_default
    if timeout == 0.0:
        timeout = timeout_default
    npc_id = npc_get_guild_storage_id()
    if npc_id == False:
        return False
    packet = bytearray(npc_id)
    packet += b'\x00\x00'
    inject_server(0x7252, packet, False)
    sleep(timeout)


def storage_open(timeout=0.0):
    global timeout_default
    if timeout == 0.0:
        timeout = timeout_default
    npc_id = npc_get_storage_id()
    if npc_id == False:
        return False
    packet = bytearray(npc_id)
    packet += b'\x00\x00\x03'
    inject_server(0x7046, packet, False)
    sleep(timeout)


def guild_storage_open(timeout=0.0):
    global timeout_default
    if timeout == 0.0:
        timeout = timeout_default
    npc_id = npc_get_guild_storage_id()
    if npc_id == False:
        return False
    packet = bytearray(npc_id)
    packet += b'\x00\x00\x0f'
    inject_server(0x7046, packet, False)
    sleep(timeout)


def storage_close(timeout=0.0):
    global timeout_default
    if timeout == 0.0:
        timeout = timeout_default
    npc_id = npc_get_storage_id()
    if npc_id == False:
        return False
    packet = bytearray(npc_id)
    packet += b'\x00\x00'
    inject_server(0x704B, packet, False)
    sleep(timeout)


def guild_storage_close(timeout=0.0):
    global timeout_default
    if timeout == 0.0:
        timeout = timeout_default
    npc_id = npc_get_guild_storage_id()
    if npc_id == False:
        return False
    packet = bytearray(npc_id)
    packet += b'\x00\x00'
    inject_server(0x704B, packet, False)
    sleep(timeout)


def storage_move_item(source_slot, destination_slot, timeout=0.0):
    global timeout_default
    if timeout == 0.0:
        timeout = timeout_default * 0.75
    if (
            get_storage()['size'] == 0
            or source_slot > get_storage()['size']
            or source_slot < 0
            or destination_slot > get_storage()['size']
            or destination_slot < 0
            or (
                get_storage()['items'][source_slot] is None
                and
                get_storage()['items'][destination_slot] is None
            )
    ):
        return False
    npc_id = npc_get_storage_id()
    if npc_id == False:
        return False
    packet = bytearray(b'\x01')
    packet.append(source_slot)
    packet.append(destination_slot)
    packet += struct.pack('<H', get_storage()['items'][source_slot]['quantity'])
    packet += npc_id
    packet += b'\x00\x00'
    inject_server(0x7034, packet, False)
    sleep(timeout)


def guild_storage_move_item(source_slot, destination_slot, timeout=0.0):
    global timeout_default
    if timeout == 0.0:
        timeout = timeout_default * 0.75
    if (
            get_guild_storage()['size'] == 0
            or source_slot > get_guild_storage()['size']
            or source_slot < 0
            or destination_slot > get_guild_storage()['size']
            or destination_slot < 0
            or (
            get_guild_storage()['items'][source_slot] is None
            and
            get_guild_storage()['items'][destination_slot] is None
    )
    ):
        return False
    npc_id = npc_get_guild_storage_id()
    if npc_id == False:
        return False
    packet = bytearray(b'\x1d')
    packet.append(source_slot)
    packet.append(destination_slot)
    packet += struct.pack('<H', get_guild_storage()['items'][source_slot]['quantity'])
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


def do_sort(type):
    if type == 'storage':
        storage_select()
        storage_open()
        storage_refresh()
        for i in range(0, get_storage()['size']):
            sorted_storage_items = array_sort_by_subkey(get_storage()['items'][i:], 'servername')
            if sorted_storage_items == False or len(sorted_storage_items) == 0:
                continue
            item_slots = array_get_subkey_filterd_keys(get_storage()['items'][i:], 'servername',
                                                       sorted_storage_items[0]['servername'])
            if item_slots == False or len(item_slots) == 0:
                break
            if i + item_slots[0] == i:
                continue
            log('[%s] moving slot %i to slot %i' % (__name__, i + item_slots[0], i))
            if storage_move_item(i + item_slots[0], i) == False:
                log('[%s] error: unable to move slot %i to slot %i' % (__name__, i + item_slots[0], i))
                break
        storage_close()
        storage_unselect()
    elif type == 'guild_storage':
        guild_storage_select()
        guild_storage_open()
        guild_storage_lock()
        guild_storage_refresh()
        for i in range(0, get_guild_storage()['size']):
            sorted_guild_storage_items = array_sort_by_subkey(get_guild_storage()['items'][i:], 'servername')
            if sorted_guild_storage_items == False or len(sorted_guild_storage_items) == 0:
                continue
            item_slots = array_get_subkey_filterd_keys(get_guild_storage()['items'][i:], 'servername',
                                                       sorted_guild_storage_items[0]['servername'])
            if item_slots == False or len(item_slots) == 0:
                break
            if i + item_slots[0] == i:
                continue
            log('[%s] moving slot %i to slot %i' % (__name__, i + item_slots[0], i))
            if guild_storage_move_item(i + item_slots[0], i) == False:
                log('[%s] error: unable to move slot %i to slot %i' % (__name__, i + item_slots[0], i))
                break
        guild_storage_unlock()
        guild_storage_close()
    # guild_storage_unselect()
    sorter_stop()


log('[%s] loaded' % (__name__))
