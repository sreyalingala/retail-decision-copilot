import os
import sys
import time


def main() -> None:
    """
    Seed the retail analytics schema with deterministic synthetic data.

    This delegates to `apps/api/app/db/seed_retail_analytics.py`.
    """

    repo_root = os.path.dirname(os.path.dirname(__file__))
    api_root = os.path.join(repo_root, "apps", "api")
    if api_root not in sys.path:
        sys.path.insert(0, api_root)

    # Import after sys.path is updated.
    from app.db.seed_retail_analytics import run_seed_from_env

    t0 = time.monotonic()
    counts = run_seed_from_env()
    elapsed = time.monotonic() - t0

    print("\nSeed completed.")
    print(f"Elapsed: {elapsed:0.1f}s")
    print("Rows created:")
    for table, count in sorted(counts.items()):
        print(f"  - {table}: {count}")
    print(
        "\nNote: runtime depends mostly on DB speed and the configured scale "
        "(default is ~120k sales + ~200k inventory snapshots). Expect minutes, not seconds, on local setups."
    )


if __name__ == "__main__":
    main()

