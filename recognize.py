from google.cloud import speech_v1p1beta1 as speech
import simple_wer_v2 as wer
import os
os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="your_credentials"

def transcribe_file(speech_file):
    """Transcribe the given audio file asynchronously."""
    

    client = speech.SpeechClient()

    with open(speech_file, "rb") as audio_file:
        content = audio_file.read()

    """
     Note that transcription is limited to a 60 seconds audio file.
     Use a GCS file for audio longer than 1 minute.
    """
    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.FLAC,
        sample_rate_hertz=48000,
        language_code="en-US"
    )

    operation = client.long_running_recognize(config=config, audio=audio)

    print("Waiting for operation to complete...")
    response = operation.result(timeout=90)

    # Each result is for a consecutive portion of the audio. Iterate through
    # them to get the transcripts for the entire audio file.
    for result in response.results:

        # The first alternative is the most likely one for this portion.
        print(u"\n\n\n\n\n\nTranscript: {}\n\n".format(result.alternatives[0].transcript))
        print("Confidence: {}\n\n\n".format(result.alternatives[0].confidence))
    return response

def diagnose(response, outfile, reference):
    hypothesis = "".join([result.alternatives[0].transcript for result in response.results])
    analysis = wer.SimpleWER(
     key_phrases=[],
     preprocess_handler=wer.RemoveCommentTxtPreprocess)
    analysis.AddHypRef(hypothesis, reference)
    summary, details, keyphrases = analysis.GetSummaries()
    aligned_html = f"""<body><html>
    <div>{summary}<br>{details}<br>{keyphrases}</div>
    <div>{"<br>".join(analysis.aligned_htmls)}</div>
    </body></html>"""
    with open(outfile, "wt") as f:
     f.write(aligned_html)

def boost(speech_file, ref):

    client = speech.SpeechClient()

    with open(speech_file, "rb") as audio_file:
        content = audio_file.read()

    """
     Note that transcription is limited to a 60 seconds audio file.
     Use a GCS file for audio longer than 1 minute.
    """
    audio = speech.RecognitionAudio(content=content)

    # Create the adaptation client
    adaptation_client = speech.AdaptationClient()

    # The parent resource where the custom class and phrase set will be created.
    location="global"
    custom_class_id="test-custom-class-0"
    project_id="my-project-1514332366597"
    phrase_set_id="test-phrase-set-0"
    parent=f"projects/{project_id}/locations/{location}"

    # Create the custom class resource
    adaptation_client.create_custom_class(
        {
            "parent": parent,
            "custom_class_id": custom_class_id,
            "custom_class": {
                "items": [
                    {"value": "ahmed"}
                ]
            },
        }
    )
    custom_class_name = (
        f"projects/{project_id}/locations/{location}/customClasses/{custom_class_id}"
    )
    # Create the phrase set resource
    phrase_set_response = adaptation_client.create_phrase_set(
        {
            "parent": parent,
            "phrase_set_id": phrase_set_id,
            "phrase_set": {
                "boost": 0,
                "phrases": [
                    {"value": f"${{{custom_class_name}}}", "boost": 10},
                    {"value": f"this is ${{{custom_class_name}}} and", "boost": 20}
                ],
            },
        }
    )
    phrase_set_name = phrase_set_response.name

    # Speech adaptation configuration
    speech_adaptation = speech.SpeechAdaptation(
        phrase_set_references=[phrase_set_name])

    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.FLAC,
        sample_rate_hertz=48000,
        language_code="en-US",
        adaptation=speech_adaptation,
        enable_word_time_offsets=True,
        model="phone_call",
        use_enhanced=True)
    operation = client.long_running_recognize(config=config, audio=audio)

    print("Waiting for operation to complete...")
    response = operation.result(timeout=90)

    # Each result is for a consecutive portion of the audio. Iterate through
    # them to get the transcripts for the entire audio file.
    for result in response.results:

        # The first alternative is the most likely one for this portion.
        print(u"\n\n\n\n\n\nTranscript: {}\n\n".format(result.alternatives[0].transcript))
        print("Confidence: {}\n\n\n".format(result.alternatives[0].confidence))
    return response


if __name__=="__main__":
    speech_file = "path/to/input/audio.flac"
    ref = "hi this is ahmed and i love eating pancakes with or without a syrup"

    response = transcribe_file(speech_file)
    diagnose(response, "diagnosis.html", ref)


    ## Boost
    boosted_response = boost(speech_file, ref)
    diagnose(boosted_response, "boost.html", ref)



