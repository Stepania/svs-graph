# How to deploy a new nuget package
First update the `SVSModel.csproj` `<version>` field, then run these commands with the version number replacing the `X.X.X`

```bash
$ dotnet pack SVSModel.csproj
$ dotnet nuget push bin/Debug/SVSModel.X.X.X.nupkg --source "svs-model-calculator" --api-key az --interactive
```
