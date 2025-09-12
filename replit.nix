language = "python3"
run = "python ultra_minimal.py"

[nix]
channel = "stable-23_05"

[deployment]
run = ["sh", "-c", "python ultra_minimal.py"]