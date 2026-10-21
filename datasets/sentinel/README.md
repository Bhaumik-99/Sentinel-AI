# Custom dataset for Sentinel AI

Use a labeled dataset you have permission to use. Do not commit large datasets or private footage to Git.

Expected layout: datasets/sentinel/data.yaml, images/train, images/val, labels/train, labels/val.

Ultralytics detection labels use one text file per image. Each line contains: class_id x_center y_center width height. Coordinates are normalized to 0–1. Class IDs must match the names in data.yaml.

Example data.yaml contents (adjust paths and classes):

path: /absolute/path/to/datasets/sentinel
train: images/train
val: images/val
names:
  0: person
  1: vehicle

Keep a held-out validation set; do not report training metrics as generalization performance. Confirm dataset licensing before training or redistributing weights.
