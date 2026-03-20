import argparse
import flwr as fl
import torch
import torch.nn as nn
import pandas as pd
import numpy as np
import os
from collections import OrderedDict
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import f1_score, accuracy_score
from model import MuleGNN

# --- CUSTOM K-NN GRAPH (100% PyTorch) ---
def pure_pytorch_knn_graph(x, k):
    dist = torch.cdist(x, x)
    _, indices = dist.topk(k + 1, dim=1, largest=False)
    neighbors = indices[:, 1:]
    src = torch.arange(x.size(0), device=x.device).view(-1, 1).repeat(1, k).view(-1)
    dst = neighbors.reshape(-1)
    return torch.stack([src, dst], dim=0)

# 1. Setup Arguments
parser = argparse.ArgumentParser()
parser.add_argument("--data", type=str, required=True, help="Path to bank CSV")
args = parser.parse_args()

print(f"🕸️ [GNN CLIENT] Pure PyTorch Mode! Loading: {args.data}")

# 2. DATA LOADING & FIXING
df = pd.read_csv(args.data)
print(f"📊 Original shape: {df.shape}")

# Drop unnecessary ID columns
cols_to_drop = ['transaction_id', 'nameOrig', 'nameDest', 'step']
for col in cols_to_drop:
    if col in df.columns:
        df = df.drop(columns=[col])

# Factorize categorical text safely (Fixes dimension mismatch)
for col in df.columns:
    if df[col].dtype == 'object' or df[col].dtype == 'category':
        df[col] = pd.factorize(df[col])[0]

numeric_df = df.select_dtypes(include=['number', 'bool']).astype(float).fillna(0)
target_col = 'is_mule' if 'is_mule' in numeric_df.columns else numeric_df.columns[0]

X_raw = numeric_df.drop(target_col, axis=1).values
y_raw = numeric_df[target_col].values

print(f"✅ Features extracted successfully! Shape: {X_raw.shape}")

# Scale Features (Fixes Missing Variable Error)
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_raw)

# 3. Create Tensors & Graph
x_tensor = torch.tensor(X_scaled, dtype=torch.float32)
y_tensor = torch.tensor(y_raw, dtype=torch.float32).unsqueeze(1)
edge_index = pure_pytorch_knn_graph(x_tensor, k=5)

# Train/Test Split Masks (80/20)
num_nodes = x_tensor.size(0)
train_mask = torch.zeros(num_nodes, dtype=torch.bool)
test_mask = torch.zeros(num_nodes, dtype=torch.bool)

split_idx = int(0.8 * num_nodes)
indices = torch.randperm(num_nodes)
train_mask[indices[:split_idx]] = True
test_mask[indices[split_idx:]] = True

# 4. Model Setup
input_dim = x_tensor.size(1)
net = MuleGNN(input_dim)

num_neg = (y_tensor[train_mask] == 0).sum().item()
num_pos = (y_tensor[train_mask] == 1).sum().item()
pos_weight_val = num_neg / (num_pos + 1e-5)
criterion = nn.BCEWithLogitsLoss(pos_weight=torch.tensor([pos_weight_val], dtype=torch.float32))
optimizer = torch.optim.Adam(net.parameters(), lr=0.005, weight_decay=5e-4)

# 5. Flower Client Definition
class GNNClient(fl.client.NumPyClient):
    def __init__(self):
        self.best_f1 = 0.0

    def get_parameters(self, config):
        return [val.cpu().numpy() for _, val in net.state_dict().items()]

    def set_parameters(self, parameters):
        params_dict = zip(net.state_dict().keys(), parameters)
        state_dict = OrderedDict({k: torch.tensor(v) for k, v in params_dict})
        net.load_state_dict(state_dict, strict=True)

    def fit(self, parameters, config):
        self.set_parameters(parameters)
        net.train()
        for epoch in range(15):
            optimizer.zero_grad()
            out = net(x_tensor, edge_index)
            loss = criterion(out[train_mask], y_tensor[train_mask])
            loss.backward()
            optimizer.step()
        return self.get_parameters(config={}), int(train_mask.sum()), {}

    def evaluate(self, parameters, config):
        self.set_parameters(parameters)
        net.eval()
        with torch.no_grad():
            out = net(x_tensor, edge_index)
            loss = criterion(out[test_mask], y_tensor[test_mask]).item()
            
            probs = torch.sigmoid(out[test_mask])
            preds = (probs >= 0.5).float()
            
            # 🔥 FIX: Force Labels to be clean 1D Binary Arrays 🔥
            y_true = (y_tensor[test_mask].cpu().numpy().flatten() > 0).astype(int)
            y_pred = preds.cpu().numpy().flatten().astype(int)
            
            acc = accuracy_score(y_true, y_pred)
            # 🔥 FIX: Use average='macro' to prevent multiclass crash 🔥
            f1 = f1_score(y_true, y_pred, zero_division=0, average='macro')
            
            print(f"\n📊 --- PURE GNN RESULTS ({args.data}) --- 📊")
            print(f"Accuracy: {acc*100:.2f}% | F1-Score (Macro): {f1:.4f}")
            
            if f1 > self.best_f1:
                self.best_f1 = f1
                save_name = f"best_gnn_{os.path.basename(args.data).split('.')[0]}.pth"
                torch.save(net.state_dict(), save_name)
                print(f"💾 [SAVED] Model saved as -> {save_name}")

        return loss, int(test_mask.sum()), {"accuracy": float(acc), "f1_score": float(f1)}

if __name__ == "__main__":
    fl.client.start_client(server_address="127.0.0.1:8080", client=GNNClient().to_client())