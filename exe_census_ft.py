# Useful quick commands 

# View results.pk:
# data = pickle.load(open("your_file.pk", "rb"))
# 
# Run model/eval:
# python exe_census_ft.py --device cpu --nfold 5 

import argparse
import torch
import datetime
import json
import yaml
import os
import time 

from src.main_model_table_ft import TabCSDI
from src.utils_table import train, evaluate_ft

from dataset_census_ft import get_dataloader

start = time.time()

parser = argparse.ArgumentParser(description="TabCSDI")
parser.add_argument("--config", type=str, default="census_ft.yaml")
parser.add_argument("--device", default="cuda", help="Device")
parser.add_argument("--seed", type=int, default=1)
parser.add_argument("--testmissingratio", type=float, default=0.2)
parser.add_argument("--nfold", type=int, default=5, help="for 5-fold test")
parser.add_argument("--unconditional", action="store_true", default=0)
parser.add_argument("--modelfolder", type=str, default="")
parser.add_argument("--nsample", type=int, default=100)

args = parser.parse_args()
print(args)

os.environ["CUDA_LAUNCH_BLOCKING"] = "1"

path = "config/" + args.config
with open(path, "r") as f:
    config = yaml.safe_load(f)

config["model"]["is_unconditional"] = args.unconditional
config["model"]["test_missing_ratio"] = args.testmissingratio

print(json.dumps(config, indent=4))

current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
foldername = "./save/census_fold" + str(args.nfold) + "_" + current_time + "/"
print("model folder:", foldername)
os.makedirs(foldername, exist_ok=True)
with open(foldername + "config.json", "w") as f:
    json.dump(config, f, indent=4)

train_loader, valid_loader, test_loader = get_dataloader(
    seed=args.seed,
    nfold=args.nfold,
    batch_size=config["train"]["batch_size"],
    missing_ratio=config["model"]["test_missing_ratio"],
)
exe_name = "census"
model = TabCSDI(exe_name, config, args.device).to(args.device)

if args.modelfolder == "":
    train(
        model,
        config["train"],
        train_loader,
        valid_loader=valid_loader,
        foldername=foldername,
    )
else:
    model.load_state_dict(torch.load("./save/" + args.modelfolder + "/model.pth"))
print("---------------Start testing---------------")
evaluate_ft(
    exe_name, model, test_loader, nsample=args.nsample, scaler=1, foldername=foldername
)

end = time.time()
with open(foldername + "time_elapsed.txt", "w") as f:
    f.write(f"Elapsed time: {end-start:.4f} seconds\n")