from google.cloud import vision
import os

os.environ["GOOGLE_APPLICATION_CREDENTIALS"]='inkterpretor.json'
#(created in step 1)


def detect_document(path):
    """Detects document features in an image."""

    client = vision.ImageAnnotatorClient()

    image = vision.Image()

    image.source.image_uri = path

    response = client.document_text_detection(image=image)

    if response.error.message:
        raise Exception(
        "{}\nFor more info on error messages, check: "
        "https://cloud.google.com/apis/design/errors".format(response.error.message)
    )

    text = response.text_annotations[0].description
    return text

if __name__ == "__main__":
    print(detect_document("C:/Users/JOHN-1/OneDrive - Ashesi University/aug - dec (2023)/Software Engineering/Interpreter/Inkterpretor/API/gcp_image.jpeg"))
