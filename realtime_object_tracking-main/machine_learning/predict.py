import base64
import cv2
import io
import json
import math
import numpy as np
import odoo
import torch
import traceback

from .deep_sort_pytorch.utils.parser import get_config
from .deep_sort_pytorch.deep_sort import DeepSort
from collections import deque
from PIL import Image
from odoo import api
from odoo.addons.bus.websocket import acquire_cursor
from ultralytics import YOLO


class_names = ['person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat', 'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard',
               'tennis racket', 'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple', 'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch', 'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse', 'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink', 'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier', 'toothbrush']

palette = (2 ** 11 - 1, 2 ** 15 - 1, 2 ** 20 - 1)
data_deque = {}


def init_tracker():
    cfg_deep = get_config()
    cfg_deep.merge_from_file(
        "addons/realtime_object_tracking/machine_learning/deep_sort_pytorch/configs/deep_sort.yaml")

    deepsort = DeepSort(cfg_deep.DEEPSORT.REID_CKPT,
                        max_dist=cfg_deep.DEEPSORT.MAX_DIST, min_confidence=cfg_deep.DEEPSORT.MIN_CONFIDENCE,
                        nms_max_overlap=cfg_deep.DEEPSORT.NMS_MAX_OVERLAP, max_iou_distance=cfg_deep.DEEPSORT.MAX_IOU_DISTANCE,
                        max_age=cfg_deep.DEEPSORT.MAX_AGE, n_init=cfg_deep.DEEPSORT.N_INIT, nn_budget=cfg_deep.DEEPSORT.NN_BUDGET,
                        use_cuda=True)

    return deepsort


def compute_color_for_labels(label):
    """
    Simple function that adds fixed color depending on the class
    """
    if label == 0:  # person
        color = (85, 45, 255)
    elif label == 2:  # Car
        color = (222, 82, 175)
    elif label == 3:  # Motobike
        color = (0, 204, 255)
    elif label == 5:  # Bus
        color = (0, 149, 255)
    else:
        color = [int((p * (label ** 2 - label + 1)) % 255) for p in palette]
    return tuple(color)


def draw_border(img, pt1, pt2, color, thickness, r, d):
    x1, y1 = pt1
    x2, y2 = pt2
    # Top left
    cv2.line(img, (x1 + r, y1), (x1 + r + d, y1), color, thickness)
    cv2.line(img, (x1, y1 + r), (x1, y1 + r + d), color, thickness)
    cv2.ellipse(img, (x1 + r, y1 + r), (r, r), 180, 0, 90, color, thickness)
    # Top right
    cv2.line(img, (x2 - r, y1), (x2 - r - d, y1), color, thickness)
    cv2.line(img, (x2, y1 + r), (x2, y1 + r + d), color, thickness)
    cv2.ellipse(img, (x2 - r, y1 + r), (r, r), 270, 0, 90, color, thickness)
    # Bottom left
    cv2.line(img, (x1 + r, y2), (x1 + r + d, y2), color, thickness)
    cv2.line(img, (x1, y2 - r), (x1, y2 - r - d), color, thickness)
    cv2.ellipse(img, (x1 + r, y2 - r), (r, r), 90, 0, 90, color, thickness)
    # Bottom right
    cv2.line(img, (x2 - r, y2), (x2 - r - d, y2), color, thickness)
    cv2.line(img, (x2, y2 - r), (x2, y2 - r - d), color, thickness)
    cv2.ellipse(img, (x2 - r, y2 - r), (r, r), 0, 0, 90, color, thickness)

    cv2.rectangle(img, (x1 + r, y1), (x2 - r, y2), color, -1, cv2.LINE_AA)
    cv2.rectangle(img, (x1, y1 + r), (x2, y2 - r - d), color, -1, cv2.LINE_AA)

    cv2.circle(img, (x1 + r, y1+r), 2, color, 12)
    cv2.circle(img, (x2 - r, y1+r), 2, color, 12)
    cv2.circle(img, (x1 + r, y2-r), 2, color, 12)
    cv2.circle(img, (x2 - r, y2-r), 2, color, 12)

    return img


def UI_box(x, img, color=None, label=None, line_thickness=None):
    # Plots one bounding box on image img
    tl = line_thickness or round(
        0.002 * (img.shape[0] + img.shape[1]) / 2) + 1  # line/font thickness
    color = color or [np.random.randint(0, 255) for _ in range(3)]
    c1, c2 = (int(x[0]), int(x[1])), (int(x[2]), int(x[3]))
    cv2.rectangle(img, c1, c2, color, thickness=tl, lineType=cv2.LINE_AA)
    if label:
        tf = max(tl - 1, 1)  # font thickness
        t_size = cv2.getTextSize(label, 0, fontScale=tl / 3, thickness=tf)[0]

        img = draw_border(img, (c1[0], c1[1] - t_size[1] - 3),
                          (c1[0] + t_size[0], c1[1]+3), color, 1, 8, 2)

        cv2.putText(img, label, (c1[0], c1[1] - 2), 0, tl / 3,
                    [225, 255, 255], thickness=tf, lineType=cv2.LINE_AA)


def draw_boxes(img, bbox, names, object_id, identities=None, offset=(0, 0)):
    # cv2.line(img, line[0], line[1], (46,162,112), 3)

    height, width, _ = img.shape
    # remove tracked point from buffer if object is lost
    for key in list(data_deque):
        if key not in identities:
            data_deque.pop(key)

    for i, box in enumerate(bbox):
        x1, y1, x2, y2 = [int(i) for i in box]
        x1 += offset[0]
        x2 += offset[0]
        y1 += offset[1]
        y2 += offset[1]

        # code to find center of bottom edge
        center = (int((x2+x1) / 2), int((y2+y2)/2))

        # get ID of object
        id = int(identities[i]) if identities is not None else 0

        # create new buffer for new object
        if id not in data_deque:
            data_deque[id] = deque(maxlen=64)
        color = compute_color_for_labels(object_id[i])
        obj_name = names[object_id[i]]
        label = '{}{:d}'.format("", id) + ":" + '%s' % (obj_name)

        # add center to buffer
        data_deque[id].appendleft(center)
        UI_box(box, img, label=label, color=color, line_thickness=2)
        # draw trail
        for i in range(1, len(data_deque[id])):
            # check if on buffer value is none
            if data_deque[id][i - 1] is None or data_deque[id][i] is None:
                continue
            # generate dynamic thickness of trails
            thickness = int(np.sqrt(64 / float(i + i)) * 1.5)
            # draw trails
            cv2.line(img, data_deque[id][i - 1],
                     data_deque[id][i], color, thickness)
    return img


def xyxy_to_xywh(*xyxy):
    """" Calculates the relative bounding box from absolute pixel values. """
    bbox_left = min([xyxy[0].item(), xyxy[2].item()])
    bbox_top = min([xyxy[1].item(), xyxy[3].item()])
    bbox_w = abs(xyxy[0].item() - xyxy[2].item())
    bbox_h = abs(xyxy[1].item() - xyxy[3].item())
    x_c = (bbox_left + bbox_w / 2)
    y_c = (bbox_top + bbox_h / 2)
    w = bbox_w
    h = bbox_h
    return x_c, y_c, w, h


def xyxy_to_tlwh(bbox_xyxy):
    tlwh_bboxs = []
    for i, box in enumerate(bbox_xyxy):
        x1, y1, x2, y2 = [int(i) for i in box]
        top = x1
        left = y1
        w = int(x2 - x1)
        h = int(y2 - y1)
        tlwh_obj = [top, left, w, h]
        tlwh_bboxs.append(tlwh_obj)
    return tlwh_bboxs


class ObjectTracking:
    def __init__(self, model):
        self.model = YOLO(model)
        self.cap = cv2.VideoCapture("D:\\CV\\yolov8\\test.mp4")

    def img_to_base64(self, image):
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG')
        buffer.seek(0)
        base64_data = base64.b64encode(buffer.read()).decode('utf-8')
        return base64_data

    def predict(self, websocket, db):
        try:
            deepsort = init_tracker()

            while self.cap.isOpened():
                xywh_bboxs = []
                confs = []
                oids = []
                outputs = []

                success, frame = self.cap.read()

                if success:
                    results = self.model(frame)

                    bbox_xyxys = results[0].boxes.xyxy.tolist()
                    confidences = results[0].boxes.conf
                    labels = results[0].boxes.cls.tolist()

                    for (bbox_xyxy, confidence, cls) in zip(bbox_xyxys, confidences, labels):
                        bbox = np.array(bbox_xyxy)
                        x1, y1, x2, y2 = bbox[0], bbox[1], bbox[2], bbox[3]
                        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                        conf = math.ceil((confidence*100))/100
                        cx, cy = int((x1+x2)/2), int((y1+y2)/2)
                        bbox_width = abs(x1-x2)
                        bbox_height = abs(y1-y2)
                        xcycwh = [cx, cy, bbox_width, bbox_height]
                        xywh_bboxs.append(xcycwh)
                        confs.append(conf)
                        oids.append(int(cls))
                    xywhs = torch.tensor(xywh_bboxs)
                    confss = torch.tensor(confs)
                    outputs = deepsort.update(xywhs, confss, oids, frame)
                    if len(outputs) > 0:
                        bbox_xyxy = outputs[:, :4]
                        identities = outputs[:, -2]
                        object_id = outputs[:, -1]
                        img = draw_boxes(img=frame, bbox=bbox_xyxy, names=class_names,
                                         object_id=object_id, identities=identities)

                        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
                        image = Image.fromarray(img)

                        buffer = io.BytesIO()
                        image.save(buffer, format='JPEG')
                        buffer.seek(0)
                        base64_data = base64.b64encode(
                            buffer.read()).decode('utf-8')

                        details = json.loads(results[0].tojson())
                        img_base64_format = f"data:image/jpeg;base64,{base64_data}"
                        if details:
                            obj_dict = {}
                            for detail in details:
                                if detail['name'] in obj_dict:
                                    obj_dict[detail['name']] += 1
                                else:
                                    obj_dict[detail['name']] = 1
                            with acquire_cursor(db) as cr:
                                env = api.Environment(
                                    cr, odoo.SUPERUSER_ID, {})
                                object_detection = env['object.tracking'].create({
                                    "object": json.dumps(obj_dict),
                                    "img": base64_data
                                })
                                websocket._send(json.dumps({
                                    "object": json.dumps(obj_dict),
                                    "img": img_base64_format
                                }))
                        else:
                            websocket._send(json.dumps({
                                "prediction": {},
                                "img": img_base64_format
                            }))
                else:
                    break
            self.cap.release()
        except:
            traceback.print_exc()
