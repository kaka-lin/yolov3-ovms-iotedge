import os
import io
import sys
import json
import logging
from concurrent import futures

import cv2
import grpc
import numpy as np
from flask import Flask, request, jsonify, Response

from arguments import ArgumentParser, ArgumentsType
from exception_handler import PrintGetExceptionDetails
from model_wrapper import YoloV3Model
from inference_engine import InferenceEngine
import extension_pb2_grpc

# Main thread
logger = logging.getLogger(__name__)

YoloV3 = YoloV3Model()

app = Flask(__name__)


# / routes to the default function which returns 'Hello World'
@app.route('/', methods=['GET'])
def defaultPage():
    return Response(response='Hello from Yolov3 inferencing based OVMS',
                    status=200)


# /score routes to scoring function
# This function returns a JSON object with inference duration and detected objects
@app.route('/score', methods=['POST'])
def score():
    try:
        # get request as byte stream
        reqBody = request.get_data(False)

        # convert from byte stream
        inMemFile = io.BytesIO(reqBody)

        # load a sample image
        inMemFile.seek(0)
        fileBytes = np.asarray(bytearray(inMemFile.read()), dtype=np.uint8)

        cvImage = cv2.imdecode(fileBytes, cv2.IMREAD_COLOR)

        # Infer Image
        detectedObjects = YoloV3.score(cvImage)

        if len(detectedObjects) > 0:
            respBody = {"inferences": detectedObjects}

            respBody = json.dumps(respBody)
            return Response(respBody, status=200, mimetype='application/json')
        else:
            return Response(status=204)

    except Exception as err:
        return Response(response='[ERROR] Exception in score : {}'.format(
            repr(err)),
                        status=500)


def main():
    try:
        # Get application arguments
        argument_parser = ArgumentParser(ArgumentsType.SERVER)

        # Get port number
        grpcServerPort = argument_parser.GetGrpcServerPort()
        logger.info("gRPC server port: %s", grpcServerPort)

        # create gRPC server and start running
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        extension_pb2_grpc.add_MediaGraphExtensionServicer_to_server(
            InferenceEngine(), server)
        server.add_insecure_port(f"[::]:{grpcServerPort}")
        server.start()
        #server.wait_for_termination()

        # Run the Http server
        app.run(host='0.0.0.0', port=8888)

    except:
        PrintGetExceptionDetails()
        exit(-1)


if __name__ == '__main__':
    logging_level = logging.DEBUG if os.getenv('DEBUG') else logging.INFO

    # Set logging parameters
    # logging.basicConfig(
    #     level=logging_level,
    #     format='[AVAX] [%(asctime)-15s] [%(threadName)-12.12s] [%(levelname)s]: %(message)s',
    #     handlers=[
    #         #logging.FileHandler(LOG_FILE_NAME),     # write in a log file
    #         logging.StreamHandler(sys.stdout)       # write in stdout
    #     ]
    # )

    main()
