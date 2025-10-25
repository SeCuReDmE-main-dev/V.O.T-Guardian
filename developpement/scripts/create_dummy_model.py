import torch
import torch.nn as nn


class DummyModel(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.fc = nn.Linear(10, 2)

    def forward(self, x):
        return self.fc(x)


def main() -> None:
    model = DummyModel()
    torch.save(model.state_dict(), "models/vot-cnn-lstm-v2.1.pth")


if __name__ == "__main__":
    main()
