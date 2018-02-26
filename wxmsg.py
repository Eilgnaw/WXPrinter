# coding:utf-8
import itchat
import paho.mqtt.client as mqtt 
from itchat.content import TEXT
from itchat.content import *
import sys
import time
import threading
import re
import binascii

reload(sys)
sys.setdefaultencoding('utf8')
import os

#程序里有防撤回方面的代码 因为我要用 所以没有移除
msg_information = {}
face_bug=None  #针对表情包的内容
client = mqtt.Client()

@itchat.msg_register([TEXT, PICTURE, FRIENDS, CARD, MAP, SHARING, RECORDING, ATTACHMENT, VIDEO],isFriendChat=True, isGroupChat=True)
def handle_receive_msg(msg):
    global face_bug
    msg_time_rec = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())   #接受消息的时间
    msg_from = ""

    # for key in msg:
    #     print key, 'corresponds to', msg[key]
    if "@@" in msg['FromUserName']:#如果是群聊消息
        msg_from = itchat.search_chatrooms(userName=msg['FromUserName'])['NickName']+"群的"+msg['ActualNickName']
    else:#好友消息
        msg_from = itchat.search_friends(userName=msg['FromUserName'])['NickName']   #在好友列表中查询发送信息的好友昵称
    msg_time = msg['CreateTime']    #信息发送的时间
    msg_id = msg['MsgId']    #每条信息的id
    msg_content = None      #储存信息的内容
    msg_share_url = None    #储存分享的链接，比如分享的文章和音乐
    print msg['Type']
    print msg_from
    if msg['Type'] == 'Text' or msg['Type'] == 'Friends':     #如果发送的消息是文本或者好友推荐
        msg_content = msg['Text']
        if msg['ToUserName'] == "filehelper":#给打印机发打印内容
           ss = binascii.b2a_hex(msg_content.encode("gbk")) #我的打印机字库是 GBK 所以要转一下
           sss = "{'text':'"+ss+"'}"
           client.publish("inTopic", payload=sss, qos=0, retain=False)    
        print msg_content

    #如果发送的消息是附件、视屏、图片、语音
    elif msg['Type'] == "Attachment" or msg['Type'] == "Video" \
            or msg['Type'] == 'Picture' \
            or msg['Type'] == 'Recording':
        msg_content = msg['FileName']    #内容就是他们的文件名
        msg['Text'](str(msg_content))    #下载文件
        # print msg_content
    elif msg['Type'] == 'Card':    #如果消息是推荐的名片
        msg_content = msg['RecommendInfo']['NickName'] + '的名片'    #内容就是推荐人的昵称和性别
        if msg['RecommendInfo']['Sex'] == 1:
            msg_content += '性别为男'
        else:
            msg_content += '性别为女'

        print msg_content
    elif msg['Type'] == 'Map':    #如果消息为分享的位置信息
        x, y, location = re.search(
            "<location x=\"(.*?)\" y=\"(.*?)\".*label=\"(.*?)\".*", msg['OriContent']).group(1, 2, 3)
        if location is None:
            msg_content = r"纬度->" + x.__str__() + " 经度->" + y.__str__()     #内容为详细的地址
        else:
            msg_content = r"" + location
    elif msg['Type'] == 'Sharing':     #如果消息为分享的音乐或者文章，详细的内容为文章的标题或者是分享的名字
        msg_content = msg['Text']
        msg_share_url = msg['Url']       #记录分享的url
        print msg_share_url
    face_bug=msg_content

##将信息存储在字典中，每一个msg_id对应一条信息
    msg_information.update(
        {
            msg_id: {
                "msg_from": msg_from, "msg_time": msg_time, "msg_time_rec": msg_time_rec,
                "msg_type": msg["Type"],
                "msg_content": msg_content, "msg_share_url": msg_share_url
            }
        }
    )


# 在这订阅消息   
def on_connect(client, userdata, flags, rc):    
    print("Connected with result code "+str(rc))    
    
    # 放在on_connect函数里意味着    
    # 重新连接时订阅主题将会被更新    
    client.subscribe("topic/sub")    

# 这里可以用来收打印机那边传回的状态 我没写   
def on_message(client, userdata, msg):
    itchat.send_msg(str(msg), toUserName='filehelper')
 

##这个是用于监听是否有消息撤回
@itchat.msg_register(NOTE, isFriendChat=True, isGroupChat=True, isMpChat=True)
def information(msg):
    #这里如果这里的msg['Content']中包含消息撤回和id，就执行下面的语句
    if '撤回了一条消息' in msg['Content']:
        old_msg_id = re.search("\<msgid\>(.*?)\<\/msgid\>", msg['Content']).group(1)   #在返回的content查找撤回的消息的id
        old_msg = msg_information.get(old_msg_id)    #得到消息
        print old_msg
        if len(old_msg_id)<11:  #如果发送的是表情包
            itchat.send_file(face_bug,toUserName='filehelper')
        else:  #发送撤回的提示给文件助手
            msg_body = old_msg.get('msg_from') + "撤回了" + old_msg.get("msg_type") + "消息" + "\n" \
                       + old_msg.get('msg_time_rec') + "\n" \
                       + r"" + old_msg.get('msg_content')
            #如果是分享的文件被撤回了，那么就将分享的url加在msg_body中发送给文件助手
            if old_msg['msg_type'] == "Sharing":
                msg_body += "\n就是这个链接➣ " + old_msg.get('msg_share_url')

            # 将撤回消息发送到文件助手
            itchat.send_msg(msg_body, toUserName='filehelper')
            # 有文件的话也要将文件发送回去
            if old_msg["msg_type"] == "Picture" \
                    or old_msg["msg_type"] == "Recording" \
                    or old_msg["msg_type"] == "Video" \
                    or old_msg["msg_type"] == "Attachment":
                file = '@fil@%s' % (old_msg['msg_content'])
                itchat.send(msg=file, toUserName='filehelper')
                os.remove(old_msg['msg_content'])
            # 删除字典旧消息
            msg_information.pop(old_msg_id)
def clientloop():
    client.loop_forever()
def itchatrun():
    itchat.run()

client.on_connect = on_connect #设置连接上服务器回调函数    
client.on_message = on_message  #设置接收到服务器消息回调函数
client.connect("127.0.0.1", 1883, 60)  #连接服务器,端口为1883,维持心跳为60秒
itchat.auto_login(hotReload=True)
t =threading.Thread(target=clientloop)
t1 =threading.Thread(target=itchatrun)
t.start()
t1.start()



 