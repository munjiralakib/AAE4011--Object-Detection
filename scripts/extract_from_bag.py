#!/usr/bin/env python3
"""Extract all frames from rosbag compressed image topic."""
import rosbag, cv2, os, argparse
import numpy as np

def extract(bag_path, output_dir="/tmp/extracted_frames",
            topic="/hikcamera/image_2/compressed"):
    os.makedirs(output_dir, exist_ok=True)
    bag   = rosbag.Bag(bag_path, 'r')
    count = 0
    h, w  = None, None

    for _, msg, _ in bag.read_messages(topics=[topic]):
        np_arr = np.frombuffer(msg.data, np.uint8)
        frame  = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if frame is None:
            continue
        if h is None:
            h, w = frame.shape[:2]
        cv2.imwrite(os.path.join(output_dir, f"frame_{count:05d}.jpg"), frame)
        count += 1

    bag.close()
    print("\n===== Image Extraction Summary =====")
    print(f"Topic        : {topic}")
    print(f"Total frames : {count}")
    print(f"Resolution   : {w} x {h}")
    print(f"Saved to     : {output_dir}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--bag',    required=True, help='Path to .bag file')
    parser.add_argument('--outdir', default='/tmp/extracted_frames')
    parser.add_argument('--topic',  default='/hikcamera/image_2/compressed')
    args = parser.parse_args()
    extract(args.bag, args.outdir, args.topic)
