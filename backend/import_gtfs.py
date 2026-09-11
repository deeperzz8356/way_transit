#!/usr/bin/env python3
"""
import_gtfs.py
==============
WAY_TRANSIT GTFS Schedule Importer — CLI Entry Point

Usage:
    python backend/import_gtfs.py
    python backend/import_gtfs.py --folder backend/data/gtfs
    python backend/import_gtfs.py --folder backend/data/gtfs --dry-run
    python backend/import_gtfs.py --folder backend/data/gtfs --validate-only
    python backend/import_gtfs.py --folder backend/data/gtfs --force --batch-size 5000

Arguments:
    --folder PATH         Path to GTFS folder (default: backend/data/gtfs)
    --dry-run             Validate without writing anything to the database
    --validate-only       Alias for --dry-run
    --force               Update/overwrite existing GTFS-sourced records
    --batch-size N        Rows per batch insert for stop_times (default: 7500)

IMPORTANT:
    This importer does NOT delete or truncate any application/user data.
    It is safe to run repeatedly (idempotent).

    ALWAYS BACKUP YOUR DATABASE BEFORE THE FIRST PRODUCTION IMPORT.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

# ── Ensure backend directory is on sys.path so all imports work ──────────────
_THIS_DIR = Path(__file__).parent.resolve()
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))

# ── Setup logging ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("import_gtfs")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="WAY_TRANSIT GTFS Schedule Importer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--folder",
        type=Path,
        default=_THIS_DIR / "data" / "gtfs",
        help="Path to GTFS folder (default: backend/data/gtfs)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate without writing anything to the database",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Alias for --dry-run",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Update/overwrite existing GTFS-sourced records (default: skip existing)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=7500,
        help="Rows per batch insert for stop_times (default: 7500)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    dry_run = args.dry_run or args.validate_only
    folder = args.folder.resolve()
    batch_size = max(1000, min(args.batch_size, 50_000))

    print()
    print("=" * 56)
    print("WAY_TRANSIT GTFS IMPORT")
    print("=" * 56)
    print(f"Feed folder: {folder}")
    print(f"Mode: BUS")
    print(f"Dry run: {'YES (no writes)' if dry_run else 'NO (will write to DB)'}")
    print(f"Force update: {'YES' if args.force else 'NO'}")
    print(f"Batch size: {batch_size:,}")
    print()

    # ── Safety reminder ───────────────────────────────────────────────────────
    print("⚠️  BACKUP DATABASE BEFORE FIRST PRODUCTION IMPORT.")
    print("    This importer will NOT delete application/user data,")
    print("    but a backup is strongly recommended before any bulk write.")
    print()

    # ── Force confirmation if force flag used without dry-run ─────────────────
    if args.force and not dry_run:
        print("  --force is set: existing GTFS records WILL be overwritten.")
        print("  Press Enter to continue or Ctrl-C to abort...")
        try:
            input()
        except (KeyboardInterrupt, EOFError):
            print("\n  Aborted by user.")
            return 1

    # ── Import models and apply schema migration ───────────────────────────────
    try:
        from database import SessionLocal, Base, engine
        import models
        from schema_migrate import ensure_ticket_schema, ensure_gtfs_schema

        print("Applying schema migrations...")
        try:
            # Create all tables from SQLAlchemy models (safe, won't drop existing)
            Base.metadata.create_all(bind=engine)
            ensure_ticket_schema()
            ensure_gtfs_schema()
            print("  ✓ Schema migration: OK")
        except Exception as exc:
            print(f"  ✗ Schema migration failed: {exc}")
            log.exception("Schema migration error")
            return 1

    except ImportError as exc:
        print(f"\n  ERROR: Could not import backend modules: {exc}")
        print(f"  Make sure you run from the project root:")
        print(f"  python backend/import_gtfs.py --folder backend/data/gtfs")
        return 1

    # ── Create DB session ─────────────────────────────────────────────────────
    db = SessionLocal()

    try:
        from gtfs_import.importer import GTFSImporter

        importer = GTFSImporter(
            folder=folder,
            db=db,
            models=models,
            dry_run=dry_run,
            batch_size=batch_size,
            force=args.force,
        )

        # ── Preflight ─────────────────────────────────────────────────────────
        preflight_ok = importer.run_preflight()
        if not preflight_ok:
            print("\n❌  PREFLIGHT FAILED. Import aborted.")
            return 1

        print("\nPreflight: OK")

        # ── Import ─────────────────────────────────────────────────────────────
        if dry_run:
            print("\n🔍  DRY RUN — running import pipeline without DB writes...")
        else:
            print("\n🚀  Starting import pipeline...")

        success = importer.run()

        # ── Summary ────────────────────────────────────────────────────────────
        importer.print_final_summary()

        # ── Bus 310 Verification ───────────────────────────────────────────────
        importer.verify_bus_310()

        # ── Result ────────────────────────────────────────────────────────────
        print("\n" + "=" * 56)
        if success:
            if dry_run:
                print("✅  DRY RUN COMPLETE — no data was written.")
            else:
                print("✅  IMPORT COMPLETE — SUCCESS")
        else:
            print("⚠️  IMPORT COMPLETED WITH ERRORS — check logs above.")

        print("=" * 56 + "\n")
        return 0 if success else 2

    except KeyboardInterrupt:
        print("\n\n  Import interrupted by user. Partial data may be committed.")
        try:
            db.rollback()
        except Exception:
            pass
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
