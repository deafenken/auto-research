import argparse


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--seed", type=int, required=True)
    args = parser.parse_args()
    print(f"hf train stub: config={args.config} seed={args.seed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
