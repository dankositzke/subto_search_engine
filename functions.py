from moviepy.editor import *
import requests, os
from pprint import pprint


# Convert mp4 videos to audio only
def mp4_to_mp3(mp4_file):

    mp3_file = mp4_file[:-1] + "3"

    videoclip = VideoFileClip(mp4_file)
    audioclip = videoclip.audio

    audioclip.write_audiofile(mp3_file)

    audioclip.close()
    videoclip.close()

    return mp3_file


def extract_video_name(raw_string):
    sub1 = "capital\\"
    sub2 = ".mp4"

    # getting index of substrings
    idx1 = raw_string.index(sub1)
    idx2 = raw_string.index(sub2)

    res = ""

    # getting elements in between
    for idx in range(idx1 + len(sub1) + 1, idx2):
        res = res + raw_string[idx]

    return res


def read_file(filename, chunk_size=5242880):
    with open(filename, "rb") as _file:
        while True:
            data = _file.read(chunk_size)
            if not data:
                break
            yield data


def ms_to_hhmmss(millis):
    millis = int(millis)
    seconds = (millis / 1000) % 60
    seconds = int(seconds)
    minutes = (millis / (1000 * 60)) % 60
    minutes = int(minutes)
    hours = (millis / (1000 * 60 * 60)) % 24

    return "%d:%d:%d" % (hours, minutes, seconds)


def get_transcript_paragraphs_with_timestamps(transcript_id, video_name):

    endpoint = f"https://api.assemblyai.com/v2/transcript/{transcript_id}/paragraphs"

    # Pull in API key
    AAI_API_KEY = os.getenv("AAI_API_KEY")

    headers = {
        "authorization": AAI_API_KEY,
        "content-type": "application/json",
    }

    response = requests.get(endpoint, headers=headers)
    transcript_dict = response.json()

    paragraphs = []
    for i in range(len(transcript_dict["paragraphs"])):
        data = transcript_dict["paragraphs"][i]

        desired_keys = ["text", "start", "end"]
        new_data = {key: val for key, val in data.items() if key in desired_keys}

        # Convert milliseconds to readable timestamps
        new_data["start"] = ms_to_hhmmss(new_data["start"])
        new_data["end"] = ms_to_hhmmss(new_data["end"])

        # Add label for the specific video
        new_data["video"] = video_name

        paragraphs.append(new_data)

    updated_paragraphs = extend_paragraphs(paragraphs)
    return updated_paragraphs


def extend_paragraphs(paragraphs):
    updated_paragraphs = []
    l = len(paragraphs)
    for i, p in enumerate(paragraphs):

        if i % 2 == 0 and i < (l - 1):
            end = paragraphs[i + 1]["end"]
            start = paragraphs[i]["start"]
            text = paragraphs[i]["text"] + " " + paragraphs[i + 1]["text"]
            video = paragraphs[i]["video"]

            new_blob = {"end": end, "start": start, "text": text, "video": video}
            updated_paragraphs.append(new_blob)

        if i == (l - 1):
            end = end = paragraphs[i]["end"]
            start = paragraphs[i]["start"]
            text = paragraphs[i]["text"]
            video = paragraphs[i]["video"]

            new_blob = {"end": end, "start": start, "text": text, "video": video}
            updated_paragraphs.append(new_blob)

    return updated_paragraphs


def start_transcription(filename):

    # Define endpoints
    upload_endpoint = "https://api.assemblyai.com/v2/upload"
    transcript_endpoint = "https://api.assemblyai.com/v2/transcript"

    # Pull in API key
    AAI_API_KEY = os.getenv("AAI_API_KEY")

    headers = {
        "authorization": AAI_API_KEY,
        "content-type": "application/json",
    }

    # Send local media file to AssemblyAI server for temporary storage
    upload_response = requests.post(
        upload_endpoint,
        headers=headers,
        data=read_file(filename),
    )

    # Store url of file upload into variable
    upload_url = upload_response.json()["upload_url"]
    pprint(upload_url)

    # Request AssemblyAI to transcribe the uploaded file
    transcript_request = {"audio_url": upload_url}

    transcript_response = requests.post(
        transcript_endpoint, json=transcript_request, headers=headers
    )
    transcript_id = transcript_response.json()["id"]
    pprint("Transcript ID: " + transcript_id)

    # Return polling_endpoint to easily check the status of the transcription
    polling_endpoint = transcript_endpoint + "/" + transcript_id
    return polling_endpoint, transcript_id


def transcription_status(polling_endpoint):

    # Pull in API key
    AAI_API_KEY = os.getenv("AAI_API_KEY")

    headers = {
        "authorization": AAI_API_KEY,
        "content-type": "application/json",
    }

    polling_response = requests.get(polling_endpoint, headers=headers)
    status = polling_response.json()["status"]

    return status
