import paho.mqtt.client as mqtt

def on_message(client, userdata, msg):
    with open("data.csv", "a") as f:
        f.write(msg.topic + ";" + msg.payload.decode() + "\n")

client = mqtt.Client()

client.on_message = on_message

client.connect("broker.hivemq.com", 1883)

client.subscribe("IUT/Colmar2026/SAE2.04/Maison1")
client.subscribe("IUT/Colmar2026/SAE2.04/Maison2")


