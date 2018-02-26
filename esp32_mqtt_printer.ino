#include <Adafruit_Thermal.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

const char* ssid = "ZZJH-YM"; 
const char* password = "asdfghjkl!1";

WiFiClient espClient;
PubSubClient client(espClient);
HardwareSerial Serial1(2);
Adafruit_Thermal printer(&Serial1);  


void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    if (client.connect("arduinoClient")) {
      Serial.println("connected");
      client.publish("outTopic", "hello world");
      // 订阅 inTopic 频道
      client.subscribe("inTopic");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}
// 回调函数
void callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Message arrived [");
  Serial.print(topic);
  Serial.print("] ");
  char arr[length];
  for (int i = 0; i < length; i++) {
    arr[i] = (unsigned char)payload[i];
    Serial.print(arr[i]);
  }
  arr[length] = '\0';
  Serial.println();

  // json 数据转换
  StaticJsonBuffer<200> jsonBuffer;
  JsonObject& root = jsonBuffer.parseObject(arr);

  // 是否转换成功
  if (!root.success()) {
    Serial.println("parseObject() failed");
    return;
  }

  // 取数据
    String s;
    const char* ss = root["text"];
    s = ss ;
    //printer.writechinese("b5e7d0c5c1f7c1bfd6facad6d6d8b0f5c0b4cfaec1f7c1bfb2bbcfdec1bfc4e3cac7cbadc4d8d0c5b5c4b9fdbac3cfd6d4dad3d0cab1bce4");
    printer.writechinese(s);
    Serial.println(ss);
    printer.println(F("/n"));
    printer.feed(2);
    printer.sleep();      // Tell printer to sleep
    delay(3000L);         // Sleep for 3 seconds
    printer.wake();       // MUST wake() before printing again, even if reset
    printer.setDefault(); // Restore printer to defaults
}


void setup() {

  Serial1.begin(115200); // Use this instead if using hardware serial
  printer.begin();
  Serial.begin(115200);
  delay(10);
  Serial.println();
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
  // 设置mqtt服务器地址以及端口
  client.setServer("192.168.6.131", 1883);
  // 设置回调函数
  client.setCallback(callback);
  
  
}

void loop() {
  // mqtt 断线重连
  if (!client.connected()) {
    reconnect();
  }
  client.loop();
}

