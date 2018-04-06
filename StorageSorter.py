from phBot import *
from threading import Timer
from time import sleep

import QtBind
import struct
import copy
import binascii # for debugging

debug = False

gui = QtBind.init(__name__, 'StorageSorter')

paddingLeft = 373
paddingTop  = 164

QtBind.createButton(gui, 'sorter_start_storage', 'sort storage', paddingLeft-37, paddingTop-46)
QtBind.createButton(gui, 'sorter_start_guild_storage', 'sort guild-storage', paddingLeft-46, paddingTop-46+30)
QtBind.createLabel(gui, '-----------------------', paddingLeft-45, paddingTop-46+55)
QtBind.createButton(gui, 'sorter_stop', 'stop processing', paddingLeft-41, paddingTop-46+70)

running = False
timers  = []

if get_locale() == 18:		# iSRO
	timeoutDefault = 1.0
elif get_locale() == 22:	# vSRO (LegionSRO, ...)
	timeoutDefault = 0.5
else:
	timeoutDefault = 1.0

npcStorageServernames = [
	'NPC_CH_WAREHOUSE_M',		# jangan #1
	'NPC_CH_WAREHOUSE_W',		# jangan #2
	'NPC_EU_WAREHOUSE',			# constantinople
	'NPC_WC_WAREHOUSE_M',		# donwhang #1
	'NPC_WC_WAREHOUSE_W',		# donwhang #2
	'NPC_CA_WAREHOUSE',			# samarkand
	'NPC_KT_WAREHOUSE',			# hotan
	'NPC_AR_WAREHOUSE',			# bagdad
	'NPC_SD_M_AREA_WAREHOUSE',	# alexandria south
	'NPC_SD_T_AREA_WAREHOUSE2',	# alexandria north
]

npcGuildStorageServernames = [
	'NPC_CH_GENARAL_SP',		# jangan
	'NPC_WC_GUILD',				# donwhang
	'NPC_SD_M_AREA_GUILD',		# alexandria south
	'NPC_SD_T_AREA_GUILD2',		# alexandria north
]

def inject_client(opcode, data, encrypted):
	global debug
	if debug == True:
		log('[%s]: bot to client' %(__name__))
		log('[%s]: \topcode: 0x%02X' %(__name__, opcode))
		if data is not None:
			log('[%s]: \tdata: %s' %(__name__, binascii.hexlify(data)))
	return inject_silkroad(opcode, data, encrypted)
	
def inject_server(opcode, data, encrypted):
	if debug == True:
		log('[%s]: bot to server' %(__name__))
		log('[%s]: \topcode: 0x%02X' %(__name__, opcode))
		if data is not None:
			log('[%s]: \tdata: %s' %(__name__, binascii.hexlify(data)))
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
	log('[%s] started' %(__name__))
	timers.append(Timer(1, do_sort, ['storage']).start())
	
def sorter_start_guild_storage():
	global running
	if running != False:
		return
	running = 'guild_storage'
	log('[%s] started' %(__name__))
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
	log('[%s] stopped' %(__name__))

def npc_get_storage_id():
	global npcStorageServernames
	storageNpcKeys = array_get_subkey_filterd_keys(get_npcs(), 'servername', npcStorageServernames)
	if len(storageNpcKeys) == 0:
		return b'\x00\x00'
	return struct.pack('<H', storageNpcKeys[0])
	
def npc_get_guild_storage_id():
	global npcGuildStorageServernames
	storageNpcKeys = array_get_subkey_filterd_keys(get_npcs(), 'servername', npcGuildStorageServernames)
	if len(storageNpcKeys) == 0:
		return b'\x00\x00'
	return struct.pack('<H', storageNpcKeys[0])

def storage_select(timeout = 0.0):
	global timeoutDefault
	if timeout == 0.0:
		timeout = timeoutDefault
	if get_locale() == 18:		# iSRO
		opcode = 0x7045
	elif get_locale() == 22:	# vSRO (LegionSRO, ...)
		opcode = 0x7C45
	else:
		return False
	npcId = npc_get_storage_id()
	if npcId == False:
		return False
	packet = bytearray(npcId)
	packet += b'\x00\x00'
	inject_server(opcode, packet, False)
	sleep(timeout)
	
def guild_storage_select(timeout = 0.0):
	global timeoutDefault
	if timeout == 0.0:
		timeout = timeoutDefault
	if get_locale() == 18:		# iSRO
		opcode = 0x7045
	elif get_locale() == 22:	# vSRO (LegionSRO, ...)
		opcode = 0x7C45
	else:
		return False
	npcId = npc_get_guild_storage_id()
	if npcId == False:
		return False
	packet = bytearray(npcId)
	packet += b'\x00\x00'
	inject_server(opcode, packet, False)
	sleep(timeout)

def storage_unselect(timeout = 0.0):
	global timeoutDefault
	if timeout == 0.0:
		timeout = timeoutDefault
	packet = bytearray(b'\x01')
	inject_client(0xB04B, packet, False)
	sleep(timeout)
	
def guild_storage_unselect(timeout = 0.0):
	global timeoutDefault
	if timeout == 0.0:
		timeout = timeoutDefault
	packet = bytearray(b'\x01')
	inject_client(0xB04B, packet, False)
	sleep(timeout)

def guild_storage_lock(timeout = 0.0):
	global timeoutDefault
	if timeout == 0.0:
		timeout = timeoutDefault
	npcId = npc_get_guild_storage_id()
	if npcId == False:
		return False
	packet = bytearray(npcId)
	packet += b'\x00\x00'
	inject_server(0x7250, packet, False)
	sleep(timeout)
	
def guild_storage_unlock(timeout = 0.0):
	global timeoutDefault
	if timeout == 0.0:
		timeout = timeoutDefault
	npcId = npc_get_guild_storage_id()
	if npcId == False:
		return False
	packet = bytearray(npcId)
	packet += b'\x00\x00'
	inject_server(0x7251, packet, False)
	sleep(timeout)
	
def storage_refresh(timeout = 0.0):
	global timeoutDefault
	if timeout == 0.0:
		timeout = timeoutDefault
	npcId = npc_get_storage_id()
	if npcId == False:
		return False
	packet = bytearray(npcId)
	packet += b'\x00\x00\x00'
	inject_server(0x703C, packet, False)
	sleep(timeout)
	
def guild_storage_refresh(timeout = 0.0):
	global timeoutDefault
	if timeout == 0.0:
		timeout = timeoutDefault
	npcId = npc_get_guild_storage_id()
	if npcId == False:
		return False
	packet = bytearray(npcId)
	packet += b'\x00\x00'
	inject_server(0x7252, packet, False)
	sleep(timeout)

def storage_open(timeout = 0.0):
	global timeoutDefault
	if timeout == 0.0:
		timeout = timeoutDefault
	npcId = npc_get_storage_id()
	if npcId == False:
		return False
	packet = bytearray(npcId)
	packet += b'\x00\x00\x03'
	inject_server(0x7046, packet, False)
	sleep(timeout)

def guild_storage_open(timeout = 0.0):
	global timeoutDefault
	if timeout == 0.0:
		timeout = timeoutDefault
	npcId = npc_get_guild_storage_id()
	if npcId == False:
		return False
	packet = bytearray(npcId)
	packet += b'\x00\x00\x0f'
	inject_server(0x7046, packet, False)
	sleep(timeout)

def storage_close(timeout = 0.0):
	global timeoutDefault
	if timeout == 0.0:
		timeout = timeoutDefault
	npcId = npc_get_storage_id()
	if npcId == False:
		return False
	packet = bytearray(npcId)
	packet += b'\x00\x00'
	inject_server(0x704B, packet, False)
	sleep(timeout)
	
def guild_storage_close(timeout = 0.0):
	global timeoutDefault
	if timeout == 0.0:
		timeout = timeoutDefault
	npcId = npc_get_guild_storage_id()
	if npcId == False:
		return False
	packet = bytearray(npcId)
	packet += b'\x00\x00'
	inject_server(0x704B, packet, False)
	sleep(timeout)

def storage_move_item(sourceSlot, destinationSlot, timeout = 0.0):
	global timeoutDefault
	if timeout == 0.0:
		timeout = timeoutDefault*0.75
	if (
		get_storage()['size'] == 0
		or sourceSlot > get_storage()['size']
		or sourceSlot < 0
		or destinationSlot > get_storage()['size']
		or destinationSlot < 0
		or (
			get_storage()['items'][sourceSlot] == None
			and
			get_storage()['items'][destinationSlot] == None
		)
	):
		return False
	npcId = npc_get_storage_id()
	if npcId == False:
		return False
	packet = bytearray(b'\x01')
	packet.append(sourceSlot)
	packet.append(destinationSlot)
	packet += struct.pack('<H', get_storage()['items'][sourceSlot]['quantity'])
	packet += npcId
	packet += b'\x00\x00'
	inject_server(0x7034, packet, False)
	sleep(timeout)
	
def guild_storage_move_item(sourceSlot, destinationSlot, timeout = 0.0):
	global timeoutDefault
	if timeout == 0.0:
		timeout = timeoutDefault*0.75
	if (
		get_guild_storage()['size'] == 0
		or sourceSlot > get_guild_storage()['size']
		or sourceSlot < 0
		or destinationSlot > get_guild_storage()['size']
		or destinationSlot < 0
		or (
			get_guild_storage()['items'][sourceSlot] == None
			and
			get_guild_storage()['items'][destinationSlot] == None
		)
	):
		return False
	npcId = npc_get_guild_storage_id()
	if npcId == False:
		return False
	packet = bytearray(b'\x1d')
	packet.append(sourceSlot)
	packet.append(destinationSlot)
	packet += struct.pack('<H', get_guild_storage()['items'][sourceSlot]['quantity'])
	packet += npcId
	packet += b'\x00\x00'
	inject_server(0x7034, packet, False)
	sleep(timeout)

def array_sort_by_subkey(array, subkey):
	if not isinstance(array, (list, dict)):
		return Falseubkey(array, subkey)
	sortedArray = copy.deepcopy(array)
	for i, elem in enumerate(sortedArray):
		if not isinstance(elem, (list, dict)):
			sortedArray[i] = elem = {subkey: ''}
		if subkey not in elem:
			sortedArray[i] = elem = {subkey: ''}
		for o, subelem in elem.items():
			if not isinstance(subelem, (int, str)):
				sortedArray[i][o] = ''
	sortedArray = sorted(sortedArray, key=lambda subarray: subarray[subkey], reverse=True)
	return sortedArray

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
			sortedStorageItems = array_sort_by_subkey(get_storage()['items'][i:], 'servername')
			if sortedStorageItems == False or len(sortedStorageItems) == 0:
				continue
			itemSlots = array_get_subkey_filterd_keys(get_storage()['items'][i:], 'servername', sortedStorageItems[0]['servername'])
			if itemSlots == False or len(itemSlots) == 0:
				break
			if i+itemSlots[0] == i:
				continue
			log('[%s] moving slot %i to slot %i' %(__name__, i+itemSlots[0], i))
			if storage_move_item(i+itemSlots[0], i) == False:
				log('[%s] error: unable to move slot %i to slot %i' %(__name__, i+itemSlots[0], i))
				break
		storage_close()
		storage_unselect()
	elif type == 'guild_storage':
		guild_storage_select()
		guild_storage_open()
		guild_storage_lock()
		guild_storage_refresh()
		for i in range(0, get_guild_storage()['size']):
			sortedGuildStorageItems = array_sort_by_subkey(get_guild_storage()['items'][i:], 'servername')
			if sortedGuildStorageItems == False or len(sortedGuildStorageItems) == 0:
				continue
			itemSlots = array_get_subkey_filterd_keys(get_guild_storage()['items'][i:], 'servername', sortedGuildStorageItems[0]['servername'])
			if itemSlots == False or len(itemSlots) == 0:
				break
			if i+itemSlots[0] == i:
				continue
			log('[%s] moving slot %i to slot %i' %(__name__, i+itemSlots[0], i))
			if guild_storage_move_item(i+itemSlots[0], i) == False:
				log('[%s] error: unable to move slot %i to slot %i' %(__name__, i+itemSlots[0], i))
				break
		guild_storage_unlock()
		guild_storage_close()
		#guild_storage_unselect()
	sorter_stop()

log('[%s] loaded' %(__name__))