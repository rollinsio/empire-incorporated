#!/bin/sh
# Upload the generated buckets to real S3 buckets that already exist.
#
# This script creates nothing: the buckets, their region and their access
# policies are yours to set up first. Use separate buckets for the two
# tenants, so the tenant boundary holds in S3 too.
#
#   scripts/upload_to_s3.sh [--dry-run] <empire-bucket> [<kdy-bucket>]
#
# Credentials and region come from the AWS CLI's usual chain (AWS_PROFILE,
# AWS_REGION, environment variables, SSO). Objects already in the target
# bucket that are not in the dataset are left alone.
set -eu

usage() {
    echo "usage: $0 [--dry-run] <empire-bucket> [<kdy-bucket>]" >&2
    exit 2
}

dry_run=""
if [ "${1:-}" = "--dry-run" ]; then
    dry_run="--dryrun"
    shift
fi
[ $# -ge 1 ] && [ $# -le 2 ] || usage

root="$(cd "$(dirname "$0")/.." && pwd)/bucket"

upload() {
    source_dir="$root/$1"
    target="$2"
    [ -d "$source_dir" ] || { echo "missing $source_dir; run 'uv run python -m generator' first" >&2; exit 1; }
    if ! aws s3api head-bucket --bucket "$target" > /dev/null; then
        echo "bucket $target does not exist or is not accessible with these credentials" >&2
        exit 1
    fi
    echo "uploading $source_dir -> s3://$target"
    aws s3 sync "$source_dir" "s3://$target" --no-progress --only-show-errors $dry_run
}

upload empire-inc-engineering "$1"
if [ $# -eq 2 ]; then
    upload kdy-engineering "$2"
fi
