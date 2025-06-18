# nupkgDownloader
Downloads nupkg file for all the dependencies of given nuget package and specific version


###HOW TO RUN

To run the NuGet package downloader, use the following command:

```
python nupkgDownloader.py -p <PACKAGE_NAME> -v <VERSION>
```
Example:

```
python nupkgDownloader.py -p ClosedXML -v 0.102.3
```
By default, all .nupkg files (including dependencies) will be downloaded into a folder named:
`downloaded_packages_<PACKAGE_NAME>_<VERSION>`

For example, if you run with package "ClosedXML" and version "0.102.3", the files will be saved in:
`downloaded_packages_ClosedXML_0.102.3`

To specify a custom folder for saving the downloaded .nupkg files, use the optional -o argument:

```
python nupkgDownloader.py -p <PACKAGE_NAME> -v <VERSION> -o <OUTPUT_FOLDER>
```

Example:
```
python nupkgDownloader.py -p ClosedXML -v 0.102.3 -o my_nupkg_files
```


### MY APPROACH

- GET catalog entry id from https://api.nuget.org/v3/registration5-gz-semver2/{PACKAGE}/{VERSION}.json .catalogEntry.@id
Ex: "https://api.nuget.org/v3/registration5-gz-semver2/closedxml/0.102.3.json"

- GET list of dependencyGroups from catalogId.dependencies  Ex: catalogId = https://api.nuget.org/v3/catalog0/data/2024.07.18.14.41.16/closedxml.0.102.3.json 

- Based on `targetFramework` choose the dependencies

- Make a list of dependencies and their version ranges. 

- GET the available versions for each dependency using https://api.nuget.org/v3-flatcontainer/{package-lowercase}/index.json  Ex: https://api.nuget.org/v3-flatcontainer/documentformat.openxml/index.json

- Download .nupkg file for a package of specific version using the command https://api.nuget.org/v3-flatcontainer/{package-lowercase}/{version-lowercase}/{package-lowercase}.{version-lowercase}.nupkg




