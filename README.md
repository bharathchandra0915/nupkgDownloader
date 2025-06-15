# nupkgDownloader
Downloads nupkg file for all the dependencies of given nuget package and specific version

### MY APPROACH

- GET catalog entry id from https://api.nuget.org/v3/registration5-gz-semver2/{PACKAGE}/{VERSION}.json .catalogEntry.@id
Ex: "https://api.nuget.org/v3/registration5-gz-semver2/closedxml/0.102.3.json"

- GET list of dependencyGroups from catalogId.dependencies  Ex: catalogId = https://api.nuget.org/v3/catalog0/data/2024.07.18.14.41.16/closedxml.0.102.3.json 

- Based on `targetFramework` choose the dependencies

- Make a list of dependencies and their version ranges. 

- GET the available versions for each dependency using https://api.nuget.org/v3-flatcontainer/{package-lowercase}/index.json  Ex: https://api.nuget.org/v3-flatcontainer/documentformat.openxml/index.json

- Download .nupkg file for a package of specific version using the command https://api.nuget.org/v3-flatcontainer/{package-lowercase}/{version-lowercase}/{package-lowercase}.{version-lowercase}.nupkg




