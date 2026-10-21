# Experiment log template

Copy this file for each run. Fill it with measured values only.

## Run metadata
- Date:
- Git commit:
- Model/checkpoint:
- Hardware:
- Python / PyTorch / Ultralytics versions:
- Dataset and split:
- Input resolution:
- Sampling interval:
- Confidence threshold:

## Results
| Metric | Baseline | Variant | Notes |
|---|---:|---:|---|
| Precision | | | |
| Recall | | | |
| mAP@0.5 | | | |
| mAP@0.5:0.95 | | | |
| Processing frames per second | | | |
| Peak GPU memory (MB) | | | |
| End-to-end latency (seconds) | | | |

## Error analysis
- False positives:
- False negatives:
- Lighting / occlusion issues:
- Tracking identity switches:
- What failed:
- Next experiment:

Do not compare runs unless dataset split, hardware, resolution, and evaluation procedure are controlled.
