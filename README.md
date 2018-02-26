# WXPrinter
 微信控制串口打印机

这个项目是通过 esp32控制串口打印机打印微信收到的文本消息(暂不支持图片),实际上并没有什么用处.   
市面上有这种打印机是分享出去通过网页给打印机主人'写信',可以自己用Flask做个接口然后扩展一下,这里就不再讨论了.
### 效果展示
- 

### 硬件和软件准备
- 可以使用微信的手机 *1
- TTL串口热敏打印机及电源 *1
- esp32 *1
- 杜邦线若干
- mqtt mosquitto
- 微信通信 itchat
- Arduino IDE 以及部分第三方库 

### 程序编写
#### 微信部分代码
- 代码参考 `/wxmsg.py`
- 由于我需要防撤回的功能,所以有很多多余代码,实际上用到的很少,这个请根据自己的需要修改
- mqtt 客户端 使用了`import paho.mqtt.client as mqtt `

```python
# 在这订阅消息,用来收取打印机状态然后发到微信   
def on_connect(client, userdata, flags, rc):    
    print("Connected with result code "+str(rc))    
    
    # 放在on_connect函数里意味着    
    # 重新连接时订阅主题将会被更新    
    client.subscribe("topic/sub")    

# 这里可以用来收打印机那边传回的状态 打印机那边程序我没有写   
def on_message(client, userdata, msg):
    itchat.send_msg(str(msg), toUserName='filehelper')
 

client = mqtt.Client()
client.on_connect = on_connect #设置连接上服务器回调函数    
client.on_message = on_message  #设置接收到服务器消息回调函数
client.connect("127.0.0.1", 1883, 60)  #连接服务器,端口为1883,维持心跳为60秒
client.loop_forever()
```
- 微信使用的是`import itchat`,其中打印的内容要转成 gbk 内码十六进制,原因后面说

``` python
itchat.auto_login(hotReload=True)
itchat.run()

@itchat.msg_register([TEXT],isFriendChat=True, isGroupChat=True)
def handle_receive_msg(msg):
    global face_bug
    msg_time_rec = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())   #接受消息的时间
    msg_from = ""
    if msg['Type'] == 'Text':     #如果发送的消息是文本
        msg_content = msg['Text']
        if msg['ToUserName'] == "filehelper":#给打印机发的打印内容
           ss = binascii.b2a_hex(msg_content.encode("gbk")) #我的打印机字库是 GBK 所以要转一下
           sss = "{'text':'"+ss+"'}" #简单拼接下 json
           client.publish("inTopic", payload=sss, qos=0, retain=False) #通过 mqtt 发布给打印机    

```
- 两部分整合在一起需要注意下,`client.loop_forever()`和`itchat.run()`需要使用多线程运行,不然会导致微信或 mqtt 的回调函数失效,具体处理方法如下

``` python
t =threading.Thread(target=clientloop)
t1 =threading.Thread(target=itchatrun)
t.start()
t1.start()
```
#### esp32部分代码编写
- 代码参考 /wxmsg.py 
- mqtt连接部分的实现具体看代码就行
- 这里说一下控制热敏打印机用到的一个库`#include <Adafruit_Thermal.h>`,因为我的打印机汉字部分只支持 GBK 编码,所以在这个库基础上对内容打印做了下处理,具体参考`/Adafruit_Thermal_Printer_Library `下的文件内的`writechinese`实现.

### 硬件接线
- 参考图片,其中 esp32 `HardwareSerial Serial1(2);`用的是 pin16,17.线的颜色都很明显,就不过多说明了.




