#!/usr/bin/env python3
import argparse
import requests
import re
import os
import sys
import json
from typing import List, Dict, Optional

ALL_DEPENDENCIES_LIST = []
FRAMEWORKS_PRIORITY = [
    "net8.0", "net7.0", "net6.0", "net5.0", "netcoreapp3.1",
    ".NETStandard2.1", ".NETStandard2.0", ".NETStandard1.6",
    ".NETStandard1.5", ".NETStandard1.4", ".NETStandard1.3",
    ".NETStandard1.2", ".NETStandard1.1", ".NETStandard1.0",
    "netcoreapp2.1", "netframework4.8", "netframework4.7.2",
    "netframework4.7.1", "netframework4.7", "netframework4.6.2",
    "netframework4.6.1", "netframework4.6", "netframework4.5.2",
    "netframework4.5.1", "netframework4.5", "netframework4.0",
    "netframework3.5"
]

def normalize_package_name(package_name: str) -> str:
    """Normalize package name to NuGet format"""
    return package_name.lower().replace(" ", "-")

def get_all_available_versions(package_name: str) -> List[str]:
    """Get all available versions for a package"""
    url = f"https://api.nuget.org/v3-flatcontainer/{package_name}/index.json"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get('versions', [])
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Failed to fetch versions for {package_name}: {str(e)}")

def get_latest_stable_version(versions: List[str], version_range: str) -> Optional[str]:
    """Get latest stable version within a version range"""
    if not version_range or version_range == "(,)" or version_range == "[,]" or version_range == "*":
        stable_versions = [v for v in versions if re.fullmatch(r"\d+\.\d+\.\d+", v)]
        return stable_versions[-1] if stable_versions else None
    
    stable_versions = [v for v in versions if re.fullmatch(r"\d+\.\d+\.\d+", v)]
    if not stable_versions:
        return None

    lower_bracket, upper_bracket = version_range[0], version_range[-1]
    version_range = version_range[1:-1]
    lower_bound, upper_bound = version_range.split(',')
    upper_bound = upper_bound.strip()

    if not upper_bound:
        return stable_versions[-1]
    
    if upper_bracket == ']' and upper_bound in stable_versions:
        return upper_bound

    try:
        parts = [int(p) for p in upper_bound.split('.')]
        if len(parts) < 3:
            return None

        if parts[2] == 0 and parts[1] == 0:
            search_prefix = f"{parts[0]-1}."
            candidates = [v for v in stable_versions if v.startswith(search_prefix)]
        elif parts[2] == 0:
            search_prefix = f"{parts[0]}.{parts[1]-1}."
            candidates = [v for v in stable_versions if v.startswith(search_prefix)]
        else:
            search_prefix = f"{parts[0]}.{parts[1]}.{parts[2]-1}"
            candidates = [v for v in stable_versions if v.startswith(search_prefix)]
        
        return candidates[-1] if candidates else None
    except (ValueError, IndexError):
        return None

def get_catalog_entry(package_name: str, version: str) -> Dict:
    """Get catalog entry for a package version"""
    package_name = normalize_package_name(package_name)
    url = f"https://api.nuget.org/v3/registration5-gz-semver2/{package_name}/{version}.json"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json().get("catalogEntry", {})
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Failed to fetch catalog entry: {str(e)}")

def get_available_frameworks(catalog_entry: Dict) -> List[str]:
    """Get available target frameworks from catalog entry"""
    return [group.get("targetFramework", "") 
            for group in catalog_entry.get("dependencyGroups", [])]

def get_best_compatible_framework(available_frameworks: List[str]) -> Optional[str]:
    """Select best compatible framework based on priority"""
    for framework in FRAMEWORKS_PRIORITY:
        if framework in available_frameworks:
            return framework
    return None

def get_dependencies_for_framework(catalog_entry: Dict, target_framework: str) -> List[Dict]:
    """Get dependencies for a specific framework"""
    for group in catalog_entry.get("dependencyGroups", []):
        if group.get("targetFramework", "") == target_framework:
            return [{"id": dep.get("id", ""), "range": dep.get("range", "")}
                   for dep in group.get("dependencies", [])]
    return []

def resolve_all_dependencies(package_name: str, package_version: str) -> None:
    """Recursively resolve all dependencies"""
    key = f"{package_name} {package_version}"
    if key in ALL_DEPENDENCIES_LIST:
        return
    
    ALL_DEPENDENCIES_LIST.append(key)
    print(f"Processing: {package_name}@{package_version}")

    try:
        catalog_entry = get_catalog_entry(package_name, package_version)
        available_frameworks = get_available_frameworks(catalog_entry)
        best_framework = get_best_compatible_framework(available_frameworks)
        
        if not best_framework:
            print(f"Warning: No compatible framework found for {package_name}@{package_version}")
            return

        dependencies = get_dependencies_for_framework(catalog_entry, best_framework)
        for dep in dependencies:
            dep_name = dep["id"]
            dep_range = dep["range"]
            versions = get_all_available_versions(dep_name)
            dep_version = get_latest_stable_version(versions, dep_range)
            
            if dep_version:
                resolve_all_dependencies(dep_name, dep_version)
    except Exception as e:
        print(f"Error resolving dependencies for {package_name}@{package_version}: {str(e)}")

def download_nupkg(package_name: str, version: str, target_folder: str) -> bool:
    """Download a .nupkg file"""
    package_name = normalize_package_name(package_name)
    url = f"https://api.nuget.org/v3-flatcontainer/{package_name}/{version}/{package_name}.{version}.nupkg"
    
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        os.makedirs(target_folder, exist_ok=True)
        filename = f"{package_name}.{version}.nupkg"
        filepath = os.path.join(target_folder, filename)
        
        with open(filepath, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"Downloaded: {filename}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Failed to download {package_name}@{version}: {str(e)}")
        return False
    except Exception as e:
        print(f"Error downloading {package_name}@{version}: {str(e)}")
        return False

def save_dependencies_list(dependencies: List[str], output_dir: str) -> None:
    """Save dependencies list to files"""
    os.makedirs(output_dir, exist_ok=True)
    
    # Save as text file
    with open(os.path.join(output_dir, "dependencies.txt"), "w") as f:
        f.write("\n".join(dependencies))
    
    # Save as JSON with download URLs
    download_links = []
    for dep in dependencies:
        name, version = dep.rsplit(" ", 1)
        name = normalize_package_name(name)
        url = f"https://api.nuget.org/v3-flatcontainer/{name}/{version}/{name}.{version}.nupkg"
        download_links.append({"package": name, "version": version, "url": url})
    
    with open(os.path.join(output_dir, "download_links.json"), "w") as f:
        json.dump(download_links, f, indent=2)

def main():
    parser = argparse.ArgumentParser(
        description="NuGet Package Downloader - Downloads packages and their dependencies",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        "package",
        help="Package name to download (e.g., 'Newtonsoft.Json')"
    )
    
    parser.add_argument(
        "version",
        help="Package version to download (e.g., '13.0.1')"
    )
    
    parser.add_argument(
        "-o", "--output",
        default="downloaded_packages",
        help="Output directory for downloaded packages"
    )
    
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Only resolve dependencies without downloading"
    )
    
    parser.add_argument(
        "--save-deps",
        action="store_true",
        help="Save dependencies list to files"
    )
    
    args = parser.parse_args()
    
    try:
        print(f"Resolving dependencies for {args.package}@{args.version}...")
        resolve_all_dependencies(args.package, args.version)
        
        if args.save_deps:
            save_dependencies_list(ALL_DEPENDENCIES_LIST, args.output)
        
        if not args.skip_download:
            print("\nDownloading packages...")
            success_count = 0
            for dep in ALL_DEPENDENCIES_LIST:
                name, version = dep.rsplit(" ", 1)
                if download_nupkg(name, version, args.output):
                    success_count += 1
            
            print(f"\nDownload complete: {success_count}/{len(ALL_DEPENDENCIES_LIST)} packages downloaded")
        
        print(f"\nTotal dependencies resolved: {len(ALL_DEPENDENCIES_LIST)}")
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
