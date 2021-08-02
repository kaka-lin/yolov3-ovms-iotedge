import datetime

import cv2
import grpc
import numpy as np
from tensorflow import make_tensor_proto, make_ndarray
from tensorflow_serving.apis import predict_pb2
from tensorflow_serving.apis import prediction_service_pb2_grpc

from common import load_classes, generate_colors, draw_outputs
from yolo_utils import yolo_eval


class YoloV3Model:
    def __init__(self,
                 model_name="yolov3",
                 label_file="model_data/coco.names",
                 classes=80,
                 score_threshold=0.5,
                 iou_threshold=0.3):
        self.model_name = model_name
        self.model_label_file = label_file
        self.class_names = load_classes(self.model_label_file)
        self.image_shape = (416, 416)

        self.classes = classes
        self.score_threshold = score_threshold
        self.iou_threshold = iou_threshold

        self.input_layer = "inputs"
        self.output_layers = [
            "detector/yolo-v3/Conv_14/BiasAdd/YoloRegion",
            "detector/yolo-v3/Conv_22/BiasAdd/YoloRegion",
            "detector/yolo-v3/Conv_6/BiasAdd/YoloRegion"
        ]

    def preprocess(self, image):
        image = np.array(image, dtype=np.float32)
        image = cv2.resize(image, self.image_shape)

        # switch from HWC to CHW
        # and reshape to (1, 3, size, size)
        # for model input requirements
        image = image.transpose(2, 0, 1).reshape(1, 3, 416, 416)

        return image

    def score(self, image):
        print("Start processing:")
        print(f"\tModel name: {self.model_name}")

        with grpc.insecure_channel('ovms-server:9010') as channel:
            stub = prediction_service_pb2_grpc.PredictionServiceStub(channel)

            image = self.preprocess(image)

            request = predict_pb2.PredictRequest()
            request.model_spec.name = self.model_name
            request.inputs[self.input_layer].CopyFrom(
                make_tensor_proto(image, shape=(image.shape)))
            # result includes a dictionary with all model outputs
            result = stub.Predict(request, 10.0)

            yolo_outputs = [[], [], []]
            for output_layer in self.output_layers:
                output = make_ndarray(result.outputs[output_layer])
                output_numpy = np.array(output)
                anchor_size = output_numpy.shape[2]
                output_numpy = output_numpy.transpose(0, 2, 3, 1).reshape(
                    1, anchor_size, anchor_size, 3, 85)
                yolo_outputs[int((anchor_size / 13) / 2)] = output_numpy

            scores, boxes, classes = yolo_eval(yolo_outputs,
                                               classes=80,
                                               score_threshold=0.5,
                                               iou_threshold=0.3)

            results = self.postprocess(boxes, scores, classes,
                                       self.class_names)

        return results

    def postprocess(self, boxes, scores, classes, class_names):
        detectedObjects = []

        if len(classes) > 0:
            for i in range(len(classes)):
                idx = int(classes[i])
                temp = boxes[i]  # xmin, ymin, xmax, ymax

                dobj = {
                    "type": "entity",
                    "entity": {
                        "tag": {
                            "value": class_names[idx],
                            "confidence": str(scores[i].numpy())
                        },
                        "box": {
                            "l": str(temp[0].numpy()),  # xmin
                            "t": str(temp[1].numpy()),  # ymax (from top)
                            "w": str((temp[2] - temp[0]).numpy()),  # xmax-xmin
                            "h": str((temp[3] - temp[1]).numpy())  # ymax-ymin
                        }
                    }
                }

                detectedObjects.append(dobj)

        return detectedObjects
