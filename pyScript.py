import requests
import re
import os

ALL_DEPENDENCIES_LIST = []
TARGET_FOLDER = "downloaded_packages"

FRAMEWORKS_PRIORITY = [
    "net8.0",
    "net7.0",
    "net6.0",
    "net5.0",
    "netcoreapp3.1",
    ".NETStandard2.1",
    ".NETStandard2.0",
    ".NETStandard1.6",
    ".NETStandard1.5",
    ".NETStandard1.4",
    ".NETStandard1.3",
    ".NETStandard1.2",
    ".NETStandard1.1",
    ".NETStandard1.0",
    "netcoreapp2.1",
    "netframework4.8",
    "netframework4.7.2",
    "netframework4.7.1",
    "netframework4.7",
    "netframework4.6.2",
    "netframework4.6.1",
    "netframework4.6",
    "netframework4.5.2",
    "netframework4.5.1",
    "netframework4.5",
    "netframework4.0",
    "netframework3.5"
]

def get_all_available_version(package_name):
    
    versions = []
    url = f"https://api.nuget.org/v3-flatcontainer/{package_name}/index.json"

    try:
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            versions = data.get('versions', [])
            if not versions:
                raise ValueError("No versions found for the package.")
            return versions

        elif response.status_code == 404:
            raise ValueError(f"Package '{package_name}' not found.")
        else:
            raise Exception(f"Unexpected response: {response.status_code}")

    except requests.exceptions.RequestException as e:
        return versions
        raise ConnectionError(f"Network error: {e}")
    except ValueError as ve:
        return versions
        raise ve
    except Exception as e:
        return versions
    

def get_latest_stable_version(versions, range):
    stable_versions = [v for v in versions if re.fullmatch(r"\d+\.\d+\.\d+", v)]
    lower_bracket, upper_bracket = range[0], range[-1]
    range = range[1:-1]

    lower_bound, upper_bound = range.split(',')
    upper_bound = upper_bound.strip()

    if upper_bound == '':
        return stable_versions[-1] if stable_versions else None
    if upper_bracket == ']' and upper_bound in stable_versions:
        return upper_bound
    

    first, second, third = upper_bound.split('.')
    first, second, third = int(first), int(second), int(third)
    if third == 0 and second == 0:
        new_first = first - 1
        to_search = [v for v in stable_versions if v.startswith(f"{new_first}.")]
        return to_search[-1] if to_search else None
    elif third == 0:    
        new_second = second - 1
        to_search = [v for v in stable_versions if v.startswith(f"{first}.{new_second}.")]
        return to_search[-1] if to_search else None
    else:
        new_third = third - 1
        to_search = [v for v in stable_versions if v.startswith(f"{first}.{second}.{new_third}")]
        return to_search[-1] if to_search else None


def get_catalog_id(package_name, version):
    package_name = package_name.lower().replace(" ", "-")  # Normalize package name
    url = f"https://api.nuget.org/v3/registration5-gz-semver2/{package_name}/{version}.json"
    # print(url)
    try:
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            catalog_entry =  data.get("catalogEntry", "")
            if not catalog_entry:
                raise ValueError("No catalog entries found for the package version.")
            return catalog_entry

        elif response.status_code == 404:
            raise ValueError(f"Package '{package_name}' version '{version}' not found.")
        else:
            raise Exception(f"Unexpected response: {response.status_code}")

    except requests.exceptions.RequestException as e:
        raise ConnectionError(f"Network error: {e}")
    except ValueError as ve:
        raise ve
    except Exception as e:
        raise RuntimeError(f"Unknown error: {e}")
    
# print(get_catalog_id("documentformat.openxml", "2.12.0"))


def get_available_tfm(catalog):
    # catalog_url = f"https://api.nuget.org/v3/catalog0/data/2020.12.15.00.29.58/{package_id.lower()}.{version}.json"
    
    available_frameworks = []
    data = catalog

    for group in data.get("dependencyGroups", []):
        tfm = group.get("targetFramework", "")
        available_frameworks.append(tfm)  # skip incompatible frameworks
        
    return available_frameworks

def get_best_compatible_tfm(compatible_frameworks):
    for framework in FRAMEWORKS_PRIORITY:
        if framework in compatible_frameworks:
            return framework
    return None

def get_dependencies_for_framework(catalog, target_framework):
    dependencies = []
    for group in catalog.get("dependencyGroups", []):
        if group.get("targetFramework", "") == target_framework:
            dependencies_list = group.get("dependencies", [])
            for dependency in dependencies_list:
                libray = dependency.get("id", "")
                range = dependency.get("range", "")
                dependencies.append({
                    "id": libray,
                    "range": range
                })
    print(dependencies)
    return dependencies

def get_catalog(catalog_id):
    url = catalog_id
    try:
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            return data

        elif response.status_code == 404:
            raise ValueError(f"Catalog entry '{catalog_id}' not found.")
        else:
            raise Exception(f"Unexpected response: {response.status_code}")

    except requests.exceptions.RequestException as e:
        raise ConnectionError(f"Network error: {e}")
    except ValueError as ve:
        raise ve
    except Exception as e:
        raise RuntimeError(f"Unknown error: {e}")

def get_all_dependencies(package_name, package_version):
    if f"{package_name} {package_version}" in ALL_DEPENDENCIES_LIST:
        print(f"Already downloaded {package_name} {package_version}, skipping...")
        return
    ALL_DEPENDENCIES_LIST.append(f"{package_name} {package_version}")
    print(f"************** Checking for  {package_name} {package_version} **************")

    catalog_id = get_catalog_id(package_name, package_version)
    catalog = get_catalog(catalog_id)
    available_frameworks = get_available_tfm(catalog)
    best_compatible_frameworks = get_best_compatible_tfm(available_frameworks)
    print(f"Available frameworks for {package_name} {package_version} with .NET 8.0: {available_frameworks}")
    print(f"Best compatible framework with .NET 8.0 is: {best_compatible_frameworks}")
    if not best_compatible_frameworks:
        print(f"No compatible frameworks found for {package_name} {package_version} with .NET 8.0.")
        return 
    dependencies = get_dependencies_for_framework(catalog, best_compatible_frameworks)
    # print(package_name, package_version)
    # print(dependencies)
    if len(dependencies) == 0:
        # print(f"No dependencies found for {package_name} {package_version} with .NET 8.0.")
        return
    
    for dep in dependencies:
        dep_package_name = dep.get("id", "")
        dep_version_range = dep.get("range", "")
        all_available_version = get_all_available_version(dep_package_name)
        best_version = get_latest_stable_version(all_available_version, dep_version_range)
        get_all_dependencies(dep_package_name, best_version)


package_name = "ClosedXML"
package_version = "0.102.3"
package_name = package_name.lower().replace(" ", "-")  # Normalize package name

get_all_dependencies(package_name, package_version)
print(f"All dependencies for {package_name} {package_version}:")
print(ALL_DEPENDENCIES_LIST, len(ALL_DEPENDENCIES_LIST))
with open("all_dependencies.txt", "w") as f , open("nupkg_download_links.json", "w") as f_json:
    for dep in ALL_DEPENDENCIES_LIST:
        f.write(dep + "\n")
        package_name, version = dep.rsplit(' ', 1)
        url = f"https://api.nuget.org/v3-flatcontainer/{package_name}/{version}/{package_name}.{version}.nupkg"
        f_json.write(url + "\n" )

def download_nupkg(package_name, version, target_folder):
    package = package_name.lower()
    ver = version.lower()
    url = f"https://api.nuget.org/v3-flatcontainer/{package}/{ver}/{package}.{ver}.nupkg"
    
    response = requests.get(url)
    if response.status_code == 200:
        os.makedirs(target_folder, exist_ok=True)
        filepath = os.path.join(target_folder, f"{package}.{ver}.nupkg")
        with open(filepath, "wb") as f:
            f.write(response.content)
        print(f"Downloaded: {filepath}")
    else:
        print(f"Failed to download. Status code: {response.status_code}")

for dep in ALL_DEPENDENCIES_LIST:
    package_name, version = dep.rsplit(' ', 1)
    download_nupkg(package_name, version, TARGET_FOLDER)
# catalog_id = get_catalog_id(package_name, package_version)
# compatible_frameworks = get_net8_compatible_tfm(catalog_id)
# best_compatible_frameworks = get_best_compatible_tfm(compatible_frameworks)
# if not best_compatible_frameworks:
#     print(f"No compatible frameworks found for {package_name} {package_version} with .NET 8.0.")
#     exit()
# dependencies = get_dependencies_for_framework(catalog_id, best_compatible_frameworks)
# if len(dependencies) == 0:
#     print(f"No dependencies found for {package_name} {package_version} with .NET 8.0.")
#     exit()


# Print the result
# if compatible_deps:
#     print(f"Dependencies for {package_name} {package_version} compatible with .NET 8.0:\n")
#     for dep in compatible_deps:
#         print(f"- {dep['id']} {dep['range']} (TFM: {dep['targetFramework']})")
# else:
#     print("No compatible dependencies found for .NET 8.0.")

