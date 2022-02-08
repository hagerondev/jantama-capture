import re
import binascii
from mitmproxy import ctx, http, flowfilter

from game import state_change

filter_jantama = flowfilter.parse("~u ^*mahjongsoul.com*$")

def get_info(action, hai, opt=()):
	state_change(action, hai, opt)
	#print(action,hai,opt)


def get_hai(s):
	split_word = "\\x02"
	for i in s.split(split_word)[1:]:
		if "\\" not in i[:2]:
			return i[:2]
	return False

ingame = True
def websocket_message(flow: http.HTTPFlow):
	global ingame
	assert flow.websocket is not None
	
	if flowfilter.match(filter_jantama, flow):
		message = flow.websocket.messages[-1]
		bin_message = binascii.b2a_base64(message.content)
		content = bin_message.decode("ascii")

		#print("strbinmessage",str(message.content))

		tar = str(message.content)

		#print("_____________________")
		#print(tar)

		if "ActionMJStart" in tar:
			get_info("game","start")
			ingame = True
		if ingame==False:
			return

		if "NotifyFriendStateChange" in tar or "NotifyFriendViewChange" in tar:
			#get_info("\t_","friend_notify")
			return
			#game関係ない
		elif "lq.FastTest.authGame" in tar or "lq.NotifyPlayerLoadGameReady" in tar:
			return
		elif "NotifyRoomPlayerUpdate" in tar:
			get_info("pre","changeplayer")
		elif "checkNetworkDelay" in tar or "\\n\\x00\\x12\\x00" in tar or "lq.Lobby.heatbeat" in tar or "lq.FastTest.fetchGamePlayerStat" in tar or "\\x00\\x12\\x06\\x12\\x04\\x03\\x03\\x03\\x03" in tar:
			#get_info("\t_","check_network "+tar)
			return
			#ネットワーク接続チェック
		elif "lq.FastTest.confirmNewRound" in tar:
			#結果確認（次のラウンド開始）
			return
		elif "ActionNewRound" in tar:
			#ラウンド開始
			hais_str = tar.split('"',1)[1].rsplit('"',1)
			hais = []
			#print("tar",tar)
			#print("hais_str",hais_str[0])
			#up = get_hai(hais_str[1][7:])
			up = []
			for hai in hais_str[1][7:].split("\\x02"):
				if "\\" not in hai[:2] and len(hai)>=2:
					up.append(hai[:2])
			get_info("up",up)
			for hai in hais_str[0].split("\\x02")[1:]:
				if "\\" not in hai[:2]:
					hais.append(hai[:2])
			hais.append(get_hai(hais_str[1]))
			get_info("hand",hais)
		elif "inputOperation" in tar:
			hai = tar.rsplit("(",1)[0].rsplit("\\",1)[1][3:]
			#hai = get_hai(tar)
			get_info("input",hai)
		elif "ActionDiscardTile" in tar:
			#各プレイヤーが出す
			#hai = tar.split("\\x02")[1][:2]
			hai = get_hai(tar)
			isreach = tar.split(r"\x02"+hai)[1][7]
			after = tar.split("ActionDiscardTile")[1]
			direction = after.split("\\",4)[4][2]
			get_info("discard",hai,(int(isreach),int(direction)))
			
			
			#print("direction", direction)
		elif "ActionDealTile" in tar:
			#各プレイヤーがもらう
			hai = get_hai(tar)
			if hai:
				get_info("dealme",hai)
		elif "inputChiPengGang" in tar:
			after = tar.split("inputChiPengGang")[1]
			#client
			if r"\x12" in tar:
				get_info("c_chipon", after[15])
				return
				if r"\x12\x04\x18\x010" in after:
					#\x1ai\x08\x03\x10\x01\x1a\x028s\x1a\x028s\x1a\x028s"
					#\x1a-\x08\x03\x10\x01\x1a\x029p\x1a\x029p\x1a\x029p"\x03\x03\x03\x022\x10\x08\x03\x12\x06\x08\x01\x12\x029p \x00(\xe0\xa7\x128\x00J\x02\x00\x00'
					#\x1a1\x08\x03\x10\x00\x1a\x023p\x1a\x024p\x1a\x025p"\x03\x03\x03\x022\x14\x08\x03\x12\n\x08\x01\x12\x022p\x12\x025p \x00(\xe0\xa7\x128\x00J\x02\x00\x00'

					get_info("c_chipon",False)
				elif r"\x12\x06\x08\x02" in after:
					get_info("c_chi",True)
				elif r"\x12\x06\x08\x03" in after:
					get_info("c_pon",True)
				else:
					print("!ERROR")
					print("maybe RON")
					print(tar)
					print(after)
			else:
				print("NOT MATCH PONCHI")
				print(tar)
				print(after)
		elif "ActionChiPengGang" in tar:
			after = tar.split("ActionChiPengGang")[1]
			#print("s_after is",after)
			hais = []
			for hai in after.split('"')[0].split(r"\x02"):
				if len(hai)>=2 and "\\" not in hai[:2]:
					hais.append(hai[:2])
			if len(hais)==4:
				get_info("kan",sorted(hais)[1])
			else:
				get_info("chipon",hais)
		elif "ActionAnGangAddGang" in tar:
			hai = get_hai(tar.split("ActionAnGangAddGang")[1])
			get_info("kan",hai)
		elif "ActionNoTile" in tar:
			get_info("round","ryukyoku")
		elif "ActionHule" in tar:
			get_info("round","end")
		elif "NotifyGameEndResult" in tar:
			get_info("game","finish")	
			ingame = False

		else:
			return

		


			# was the message sent from the client or server?
			if message.from_client:
				print(f"\tClient: {message.content}")
				#print(f"{message.content.decode('utf-8')}")
			else:
				print(f"\tServer: {message.content}")
				#print(f"DECODE : 「{message.content.decode('utf-8')}」")
				#ctx.log.info(f"Server sent a message: {message.content.decode('utf-8')}")


	# if b'FOOBAR' in message.content:
	#     # kill the message and not send it to the other endpoint
	#     message.drop()