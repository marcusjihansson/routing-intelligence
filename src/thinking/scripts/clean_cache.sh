#!/bin/bash
# Cache cleaning script for ML and package manager caches.
# Quick, simple interface for terminal users with color output.

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'  # No Color

# Cache directory paths
CACHE_HOME="$HOME/.cache"
DSPY_CACHE="$CACHE_HOME/model_requests_cache"
HUGGINGFACE_CACHE="$CACHE_HOME/huggingface"
UV_CACHE="$CACHE_HOME/uv"
PIP_CACHE="$CACHE_HOME/pip"
DEEPDOCTECTION_CACHE="$CACHE_HOME/deepdoctection"
DOCTR_CACHE="$CACHE_HOME/doctr"
SELENIUM_CACHE="$CACHE_HOME/selenium"

# Function to get directory size in human-readable format
get_cache_size() {
    local path="$1"
    if [ ! -d "$path" ]; then
        echo "0"
        return
    fi
    du -sh "$path" 2>/dev/null | cut -f1
}

# Function to get disk space
get_disk_space() {
    df -h /System/Volumes/Data | tail -1 | awk '{print $2, $3, $4}'
}

# Function to print colored output
print_header() {
    echo -e "${BLUE}============================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}✗ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Function to confirm deletion
confirm_deletion() {
    local cache_name="$1"
    local cache_path="$2"
    local force="$3"

    if [ "$force" = true ]; then
        return 0
    fi

    echo -n "Remove $cache_name cache at $cache_path? [y/N] "
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        return 0
    else
        return 1
    fi
}

# Function to clean cache safely
clean_cache_safe() {
    local cache_name="$1"
    local cache_path="$2"
    local dry_run="$3"
    local force="$4"

    if [ ! -d "$cache_path" ]; then
        if [ "$VERBOSE" = true ]; then
            print_warning "$cache_name: Path doesn't exist: $cache_path"
        fi
        return 1
    fi

    if [ "$dry_run" = true ]; then
        echo -e "  ${GREEN}✓${NC} $cache_name: Would remove $cache_path"
        return 0
    fi

    if confirm_deletion "$cache_name" "$cache_path" "$force"; then
        if rm -rf "$cache_path" 2>/dev/null; then
            print_success "$cache_name: Removed $cache_path"
            return 0
        else
            print_error "$cache_name: Failed to remove $cache_path"
            return 1
        fi
    else
        print_warning "$cache_name: Skipped"
        return 1
    fi
}

# Function to check if cache name is valid
is_valid_cache() {
    local cache_name="$1"
    case "$cache_name" in
        dspy|huggingface|uv|pip|deepdoctection|doctr|selenium)
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

# Function to get cache path by name
get_cache_path() {
    local cache_name="$1"
    case "$cache_name" in
        dspy) echo "$DSPY_CACHE" ;;
        huggingface) echo "$HUGGINGFACE_CACHE" ;;
        uv) echo "$UV_CACHE" ;;
        pip) echo "$PIP_CACHE" ;;
        deepdoctection) echo "$DEEPDOCTECTION_CACHE" ;;
        doctr) echo "$DOCTR_CACHE" ;;
        selenium) echo "$SELENIUM_CACHE" ;;
    esac
}

# Parse command line arguments
DRY_RUN=false
FORCE=false
VERBOSE=false
SPECIFIC_CACHE=""
MIN_SPACE=10

while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --cache)
            SPECIFIC_CACHE="$2"
            shift 2
            ;;
        --min-space)
            MIN_SPACE="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --dry-run        Show what would be cleaned without actually cleaning"
            echo "  --force          Clean without confirmation"
            echo "  --verbose        Print detailed information"
            echo "  --cache NAME      Clean specific cache (dspy, huggingface, uv, pip, etc.)"
            echo "  --min-space GB   Minimum required free space in GB (default: 10)"
            echo "  --help           Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 --dry-run                    # Preview what would be cleaned"
            echo "  $0 --force                      # Clean without confirmation"
            echo "  $0 --cache huggingface          # Clean only HuggingFace cache"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Print cache analysis
print_header "CACHE ANALYSIS"

total_size_str="0"
if [ -d "$DSPY_CACHE" ]; then
    size=$(get_cache_size "$DSPY_CACHE")
    printf "  %-20s %8s  %s\n" "dspy" "$size" "$DSPY_CACHE"
    total_size_str="+"
fi

if [ -d "$HUGGINGFACE_CACHE" ]; then
    size=$(get_cache_size "$HUGGINGFACE_CACHE")
    printf "  %-20s %8s  %s\n" "huggingface" "$size" "$HUGGINGFACE_CACHE"
    total_size_str="+"
fi

if [ -d "$UV_CACHE" ]; then
    size=$(get_cache_size "$UV_CACHE")
    printf "  %-20s %8s  %s\n" "uv" "$size" "$UV_CACHE"
    total_size_str="+"
fi

if [ -d "$PIP_CACHE" ]; then
    size=$(get_cache_size "$PIP_CACHE")
    printf "  %-20s %8s  %s\n" "pip" "$size" "$PIP_CACHE"
    total_size_str="+"
fi

if [ -d "$DEEPDOCTECTION_CACHE" ]; then
    size=$(get_cache_size "$DEEPDOCTECTION_CACHE")
    printf "  %-20s %8s  %s\n" "deepdoctection" "$size" "$DEEPDOCTECTION_CACHE"
    total_size_str="+"
fi

if [ -d "$DOCTR_CACHE" ]; then
    size=$(get_cache_size "$DOCTR_CACHE")
    printf "  %-20s %8s  %s\n" "doctr" "$size" "$DOCTR_CACHE"
    total_size_str="+"
fi

if [ -d "$SELENIUM_CACHE" ]; then
    size=$(get_cache_size "$SELENIUM_CACHE")
    printf "  %-20s %8s  %s\n" "selenium" "$size" "$SELENIUM_CACHE"
    total_size_str="+"
fi

if [ "$total_size_str" = "0" ]; then
    printf "  %-20s %8s  %s\n" "TOTAL" "0"
else
    total_size=$(du -sh "$CACHE_HOME" 2>/dev/null | cut -f1)
    printf "  %-20s %8s\n" "TOTAL" "$total_size"
fi

# Print disk space
echo ""
print_header "DISK SPACE (System/Volumes/Data)"

read total used available <<< $(get_disk_space)
printf "  %-20s %8s\n" "Total" "$total"
printf "  %-20s %8s\n" "Used" "$used"
printf "  %-20s %8s\n" "Available" "$available"

# Extract numbers for comparison (simplified parsing)
used_num=$(echo "$used" | sed 's/[A-Za-z]//g')
total_num=$(echo "$total" | sed 's/[A-Za-z]//g')
if [ -n "$used_num" ] && [ -n "$total_num" ] && [ "$total_num" != "0" ]; then
    usage_percent=$((used_num * 100 / total_num))
    printf "  %-20s %8d%%\n" "Usage" "$usage_percent"
fi

# Select caches to clean
caches_to_clean=()
if [ -n "$SPECIFIC_CACHE" ]; then
    if is_valid_cache "$SPECIFIC_CACHE"; then
        caches_to_clean+=("$SPECIFIC_CACHE")
    else
        print_error "Unknown cache: $SPECIFIC_CACHE"
        exit 1
    fi
else
    # Default caches to clean
    caches_to_clean=("dspy" "huggingface" "uv" "pip")
fi

# Clean caches
echo ""
print_header "$([ "$DRY_RUN" = true ] && echo "DRY RUN - Preview of cache cleanup" || echo "CACHE CLEANUP")"

removed_count=0

for cache_name in "${caches_to_clean[@]}"; do
    cache_path=$(get_cache_path "$cache_name")
    if [ -n "$cache_path" ] && clean_cache_safe "$cache_name" "$cache_path" "$DRY_RUN" "$FORCE"; then
        removed_count=$((removed_count + 1))
    fi
done

echo ""
if [ "$DRY_RUN" = true ]; then
    echo "Would remove $removed_count cache(s)"
else
    print_success "Removed $removed_count cache(s)"
fi

exit 0