import argparse
import shutil
from pathlib import Path


EXCLUDE_DIR_PREFIXES = (
    "_internal/test",
    "_internal/docs",
    "_internal/devtools",
)
EXCLUDE_FILE_SUFFIXES = (".pyc", ".pyo")


def should_exclude(path: Path, source_root: Path) -> bool:
    rel = path.relative_to(source_root).as_posix()
    name = path.name

    if name.startswith(".git"):
        return True
    if "__pycache__" in path.parts:
        return True
    if name.endswith(EXCLUDE_FILE_SUFFIXES):
        return True
    if rel.startswith(EXCLUDE_DIR_PREFIXES):
        return True
    if rel.startswith("_internal/runtime/fake_scraper_"):
        return True
    return False


def copy_tree(source_root: Path, target_root: Path) -> None:
    for src in source_root.rglob("*"):
        if should_exclude(src, source_root):
            continue
        rel = src.relative_to(source_root)
        dst = target_root / rel
        if src.is_dir():
            dst.mkdir(parents=True, exist_ok=True)
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)


def clean_runtime_dirs(package_root: Path) -> None:
    data_dir = package_root / "data"
    output_dir = package_root / "output"
    runtime_dir = package_root / "_internal" / "runtime"

    for d in (data_dir, output_dir, runtime_dir):
        d.mkdir(parents=True, exist_ok=True)

    for p in data_dir.rglob("*"):
        if p.is_file():
            p.unlink()

    for p in output_dir.rglob("*"):
        if p.is_file():
            p.unlink()

    for p in runtime_dir.rglob("*"):
        if p.is_file() and p.name != ".gitkeep":
            p.unlink()


def build_distribution(with_zip: bool) -> Path:
    repo_root = Path(__file__).resolve().parents[3]
    source_root = repo_root / "apps"
    dist_root = repo_root / "distribution"
    package_root = dist_root / "slot-infomation"

    if not source_root.exists():
        raise FileNotFoundError(f"Source directory not found: {source_root}")

    if package_root.exists():
        shutil.rmtree(package_root)
    package_root.mkdir(parents=True, exist_ok=True)

    copy_tree(source_root, package_root)
    clean_runtime_dirs(package_root)

    if with_zip:
        zip_base = dist_root / "slot-infomation"
        if (dist_root / "slot-infomation.zip").exists():
            (dist_root / "slot-infomation.zip").unlink()
        shutil.make_archive(str(zip_base), "zip", root_dir=dist_root, base_dir="slot-infomation")

    return package_root


def main() -> int:
    parser = argparse.ArgumentParser(description="Build clean distribution package from apps/")
    parser.add_argument("--zip", action="store_true", help="also create distribution/slot-infomation.zip")
    args = parser.parse_args()

    package_root = build_distribution(with_zip=args.zip)
    print(f"Distribution package created: {package_root}")
    if args.zip:
        print(f"Zip created: {package_root}.zip")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
