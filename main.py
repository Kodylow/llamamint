import os
from flask import Flask, request, Response
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slack_sdk.signature import SignatureVerifier
import json

app = Flask(__name__)
slack_token = os.environ["SLACK_BOT_TOKEN"]
client = WebClient(token=slack_token)
signature_verifier = SignatureVerifier(os.environ["SLACK_SIGNING_SECRET"])

# Fetch bot user ID on startup to prevent responding to self-posts.
bot_user_id = client.auth_test()["user_id"]

import logging  # Make sure to import logging at the top of your file

# Configure basic logging
logging.basicConfig(
    level=logging.INFO)  # Set to DEBUG if you want even more detailed output


@app.route("/slack/events", methods=["POST"])
def slack_events():
    logging.info("Received a request from Slack: %s", str(request.json))
    # Verify the request signature using the app's signing secret
    if not signature_verifier.is_valid_request(request.get_data(),
                                               request.headers):
        logging.warning("Invalid request signature.")
        return "invalid request", 403

    # Challenge verification for Slack
    if "challenge" in request.json:
        return request.json["challenge"], 200

    event = request.json.get("event", {})
    logging.info("Handling event: %s", str(event))

    # Check if the event is of type message and in the designated channel
    if event.get("type") == "message" and event.get(
            "channel") == "C05FYTUJ8SZ":
        user_id = event.get("user")

        # Check if the message event is sent by the bot itself
        if user_id == bot_user_id:
            logging.info("Message event sent by the bot itself. Ignoring.")
            return Response(), 200

        text = event.get("text", "")
        logging.info("Message text: %s", text)

        # Check if bug report submission from "bot_id": "B06916MHHBQ"
        if "bot_id" in event and event["bot_id"] == "B06916MHHBQ":
            logging.info(
                "Bug report submitted. Preparing acknowledgement message.")
            try:
                # Format and send the pretty printed json in a code block
                pretty_json = "```\n" + json.dumps(
                    event, indent=2, sort_keys=True) + "\n```"
                ack_message = "Acknowledged: " + pretty_json
                response = client.chat_postMessage(channel=event["channel"],
                                                   text=ack_message,
                                                   thread_ts=event.get("ts"))
                logging.info("Acknowledgement message sent: %s", response)
            except SlackApiError as e:
                logging.error("Error posting ack message: %s", str(e))
                return Response(), 500

    return Response(), 200


if __name__ == "__main__":
    try:
        # send an "I'm alive!" message to the channel
        client.chat_postMessage(channel="C05FYTUJ8SZ", text="I'm alive!")
        app.run(host="0.0.0.0", port=3000)
    except Exception as e:
        logging.error("Error starting the Flask app: %s", str(e))
