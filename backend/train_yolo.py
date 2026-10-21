"""Fine-tune an Ultralytics detector on a labeled dataset.
Example: python train_yolo.py --data ../datasets/sentinel/data.yaml --model yolov8n.pt --epochs 50 --imgsz 640
"""
import argparse
import json
from pathlib import Path
from ultralytics import YOLO

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data",required=True,help="Dataset YAML with train/val images and class names")
    parser.add_argument("--model",default="yolov8n.pt")
    parser.add_argument("--epochs",type=int,default=50)
    parser.add_argument("--imgsz",type=int,default=640)
    parser.add_argument("--batch",type=int,default=8)
    parser.add_argument("--device",default=None,help="0 for first NVIDIA GPU or cpu")
    parser.add_argument("--project",default="runs/sentinel")
    parser.add_argument("--name",default="yolo-finetune")
    args=parser.parse_args(); data=Path(args.data).resolve()
    if not data.is_file(): raise SystemExit(f"Dataset YAML not found: {data}")
    model=YOLO(args.model)
    train=model.train(data=str(data),epochs=max(1,args.epochs),imgsz=max(320,args.imgsz),batch=max(1,args.batch),device=args.device,project=args.project,name=args.name,patience=10,plots=True,save=True,deterministic=True)
    metrics=model.val(data=str(data),imgsz=max(320,args.imgsz),device=args.device)
    report={"weights":str(Path(args.project)/args.name/"weights"/"best.pt"),"dataset_yaml":str(data),"epochs_requested":args.epochs,"metrics":{k:float(v) for k,v in metrics.results_dict.items()},"training_save_dir":str(train.save_dir)}
    out=Path(train.save_dir)/"sentinel_metrics.json"; out.write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps(report,indent=2))

if __name__=="__main__": main()
