#!/usr/bin/env python3
"""
ROS node: subscribes to compressed image topic,
runs YOLOv8n vehicle detection, displays annotated UI.
"""
import rospy
import cv2
import numpy as np
from sensor_msgs.msg import CompressedImage
from ultralytics import YOLO

VEHICLE_CLASSES = [2, 3, 5, 7]
CLASS_NAMES     = {2:'car', 3:'motorcycle', 5:'bus', 7:'truck'}

class VehicleDetector:
    def __init__(self):
        rospy.init_node('vehicle_detector_node', anonymous=True)

        rospy.loginfo("Loading YOLOv8n model...")
        self.model = YOLO('yolov8n.pt')

        self.image_topic = rospy.get_param(
            '~image_topic', '/hikcamera/image_2/compressed')
        self.conf_thresh = rospy.get_param('~confidence_threshold', 0.45)

        self.frame_count = 0
        self.total_stats = {name: 0 for name in CLASS_NAMES.values()}

        rospy.Subscriber(self.image_topic, CompressedImage,
                         self.callback, queue_size=1)
        rospy.loginfo(f"Subscribed to: {self.image_topic}")
        rospy.loginfo("Vehicle detector ready! Waiting for images...")

    def callback(self, msg):
        np_arr = np.frombuffer(msg.data, np.uint8)
        frame  = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if frame is None:
            return

        self.frame_count += 1

        results  = self.model(frame, classes=VEHICLE_CLASSES,
                              conf=self.conf_thresh, verbose=False)
        annotated = results[0].plot()

        frame_stats = {name: 0 for name in CLASS_NAMES.values()}
        for box in results[0].boxes:
            cls_id = int(box.cls.item())
            name   = CLASS_NAMES.get(cls_id, 'unknown')
            frame_stats[name]      += 1
            self.total_stats[name] += 1

        total_this_frame = sum(frame_stats.values())
        lines = [
            f"Frame: {self.frame_count}  |  Vehicles: {total_this_frame}",
            f"Cars:{frame_stats['car']}  Buses:{frame_stats['bus']}  "
            f"Trucks:{frame_stats['truck']}  Motos:{frame_stats['motorcycle']}"
        ]
        for i, line in enumerate(lines):
            cv2.putText(annotated, line, (10, 30 + i*30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        cv2.imshow("AAE4011 - Vehicle Detection", annotated)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            rospy.signal_shutdown("User quit")

    def shutdown(self):
        cv2.destroyAllWindows()
        rospy.loginfo("\n===== Detection Summary =====")
        rospy.loginfo(f"Total frames processed: {self.frame_count}")
        for name, count in self.total_stats.items():
            rospy.loginfo(f"  {name:<12}: {count}")

if __name__ == '__main__':
    try:
        det = VehicleDetector()
        rospy.on_shutdown(det.shutdown)
        rospy.spin()
    except rospy.ROSInterruptException:
        pass
    finally:
        cv2.destroyAllWindows()
