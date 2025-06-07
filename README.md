# Kyberna CTF

This repository contains a simple client for the Kyberna Capture the Flag competition.

## Requirements

Install dependencies with:

```bash
pip install -r requirements.txt
```

## Running the game

### Manual mode

To play manually just execute `main.py` without any arguments and follow the prompts:

```bash
python main.py
```

### AI mode

To run the provided AI models on a specific map use the `--ais` and `--map` arguments. Example:

```bash
python main.py --ais DijkstraAI,InterceptAI2 --map level-{n}
```

Replace `{n}` with the desired level number.
