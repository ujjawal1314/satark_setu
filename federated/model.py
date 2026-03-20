import torch
import torch.nn as nn

class PureGCNLayer(nn.Module):
    def __init__(self, in_features, out_features):
        super(PureGCNLayer, self).__init__()
        self.linear = nn.Linear(in_features, out_features)

    def forward(self, x, edge_index):
        num_nodes = x.size(0)
        
        # 1. Create Adjacency Matrix
        adj = torch.zeros((num_nodes, num_nodes), device=x.device)
        adj[edge_index[0], edge_index[1]] = 1.0
        
        # 2. Add self-loops
        adj += torch.eye(num_nodes, device=x.device)
        
        # 3. Normalize
        deg = adj.sum(dim=1, keepdim=True)
        adj_norm = adj / deg
        
        # 4. Message Passing
        aggregated_features = torch.matmul(adj_norm, x)
        
        return self.linear(aggregated_features)

class MuleGNN(nn.Module):
    def __init__(self, input_dim):
        super(MuleGNN, self).__init__()
        self.conv1 = PureGCNLayer(input_dim, 64)
        self.conv2 = PureGCNLayer(64, 32)
        
        self.fc1 = nn.Linear(32, 16)
        self.fc2 = nn.Linear(16, 1)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(0.3)

    def forward(self, x, edge_index):
        x = self.relu(self.conv1(x, edge_index))
        x = self.dropout(x)
        x = self.relu(self.conv2(x, edge_index))
        
        x = self.relu(self.fc1(x))
        out = self.fc2(x)
        return out