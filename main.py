import os
from flask import Flask, request, Response
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slack_sdk.signature import SignatureVerifier

app = Flask(__name__)
slack_token = os.environ["SLACK_BOT_TOKEN"]
client = WebClient(token=slack_token)
signature_verifier = SignatureVerifier(os.environ["SLACK_SIGNING_SECRET"])


@app.route("/slack/events", methods=["POST"])
def slack_events():
  # Verify the request signature using the app's signing secret
  # Note: this is important to ensure that the request is coming from Slack
  if not signature_verifier.is_valid_request(request.get_data(),
                                             request.headers):
    return "invalid request", 403

  if "challenge" in request.json:
    return request.json["challenge"], 200

  # Handle the event
  if request.json["event"]["type"] == "message" and request.json["event"][
      "channel"] == "C05FYTUJ8SZ":
    try:
      response = client.chat_postMessage(
          channel=request.json["event"]["channel"],
          text=f"Received your message: {request.json['event']['text']}")
      return Response(), 200
    except SlackApiError as e:
      print(f"Error posting message: {e}")
      return Response(), 500

  return Response(), 200


if __name__ == "__main__":
  app.run(port=3000)
