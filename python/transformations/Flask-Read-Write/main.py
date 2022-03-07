from quixstreaming import QuixStreamingClient, EventData
from flask import Flask
import os
import requests
import json
import time
from datetime import datetime
import urllib.parse


# Quix injects credentials automatically to the client.
# Alternatively, you can always pass an SDK token manually as an argument.
client = QuixStreamingClient()

print("Opening input and output topics")
input_topic = client.open_input_topic(os.environ["input"], "default-consumer-group")
output_topic = client.open_output_topic(os.environ["output"])


auth_token = '{placeholder:token}'
telemetry_query_base_url = 'https://telemetry-query-{placeholder:workspaceId}.{placeholder:environment.subdomain}.quix.ai/'
# streaming_writer_base_url = 'https://writer-{placeholder:workspaceId}.{placeholder:environment.subdomain}.quix.ai/'

app = Flask("Hello Flask I/O")


# a helper method to do our HTTP posts
def post(url, payload):
    headers = {'Authorization': 'Bearer ' + auth_token, 'Content-type': 'application/json'}
    payload = json.dumps(payload)
    r = requests.post(url, data=payload, headers=headers)
    return r


@app.route("/")
def hello_world():
    return "<p><a href='/streams'>Read Streams</a></p>"


@app.route("/write/<stream_id>")
def write_event(stream_id):
    # Create a new stream to output data, append the current date time to easily identify it for this demo
    output_stream = output_topic.create_stream(stream_id + "-" + datetime.now())
    output_stream.properties.parents.append(stream_id)

    # build an EventData object and add some tags if needed
    event_data = EventData("MyEventId",
                           datetime.now(),
                           "MyEventValue at {}".format(datetime.now()))\
        .add_tag("tag1", "1")\
        .add_tag("tag2", "2")\
        .add_tag("tag3", "3")

    # write the EventData to the output stream
    output_stream.events.write(event_data)

    response = "<p><a href='/'>HOME</a> | <a href='/streams'>Streams</a></p><br/><br/>"

    # display the HTTP status code
    response = response + "Event Sent"
    return response, 200


@app.route("/streams")
def get_streams():

    # build the URL
    url = telemetry_query_base_url + "streams"

    # create the payload, just need topic and the topic name
    payload = {"topic": "{}".format(os.environ["topic"])}

    # post the payload to the URL
    result = post(url, payload)

    # load the json
    streams = json.loads(result.text)

    # build the html response
    response = "<p><a href='/'>HOME</a></p>"
    response = response + "These are the streams for the topic <b>{}</b><br/><br/>".format(os.environ["topic"])

    # display the list of returned streams
    for s in streams:
        safe_string = urllib.parse.quote_plus(s["streamId"])
        response = "{}<a href='/write/{}'>{}</a><br/>".format(response, safe_string, s["streamId"])

    # add some helpful advice
    response = response + "<br/>Click a stream to send an event to it" \
                          "<br/>If you don't see any streams either ensure data is " \
                          "arriving into the topic or turn on topic persistence"

    return response


app.run(debug=True, host="0.0.0.0", port=80)



