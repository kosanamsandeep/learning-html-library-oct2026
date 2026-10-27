from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from aiortc import RTCPeerConnection, RTCSessionDescription

app = FastAPI()

peer_connections = []


class Offer(BaseModel):
    sdp: str
    type: str


@app.get("/", response_class=HTMLResponse)
async def index():
    return """
    <!DOCTYPE html>
    <html>
    <body>
      <h2>Python WebRTC Demo</h2>

      <button onclick="start()">Start WebRTC</button>
      <button onclick="sendMessage()">Send Message</button>

      <pre id="log"></pre>

      <script>
        let pc;
        let channel;

        function log(message) {
          document.getElementById("log").textContent += message + "\\n";
          console.log(message);
        }

        async function start() {
          pc = new RTCPeerConnection();

          channel = pc.createDataChannel("chat");

          channel.onopen = () => {
            log("Data channel opened");
          };

          channel.onmessage = (event) => {
            log("Message from Python: " + event.data);
          };

          const offer = await pc.createOffer();
          await pc.setLocalDescription(offer);

          const response = await fetch("/offer", {
            method: "POST",
            headers: {
              "Content-Type": "application/json"
            },
            body: JSON.stringify({
              sdp: pc.localDescription.sdp,
              type: pc.localDescription.type
            })
          });

          const answer = await response.json();

          await pc.setRemoteDescription(answer);

          log("WebRTC connection setup completed");
        }

        function sendMessage() {
          if (!channel || channel.readyState !== "open") {
            log("Channel is not open yet");
            return;
          }

          channel.send("Hello from browser");
          log("Sent: Hello from browser");
        }
      </script>
    </body>
    </html>
    """


@app.post("/offer")
async def offer(offer: Offer):
    pc = RTCPeerConnection()
    peer_connections.append(pc)

    @pc.on("datachannel")
    def on_datachannel(channel):
        print("Data channel created:", channel.label)

        @channel.on("message")
        def on_message(message):
            print("Received from browser:", message)

            channel.send(f"Python server received: {message}")

    remote_description = RTCSessionDescription(sdp=offer.sdp, type=offer.type)

    await pc.setRemoteDescription(remote_description)

    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
