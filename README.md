# download_github_release：下载 Github 最新 Release

## 注意
本项目以后将不再更新，因为功能已合并至：
- [download_form_github（从 Github 更新 Release 或下载文件）](https://github.com/GB756980/download_form_github)

## 项目说明

项目有两个文件，分别是 config.json 和 download_github_release.py

config.json 包括多种信息，目前有 github_token 和 projects 。

github_token 用于下载文件时，避免访问 GitHub API 时达到请求限制。

projects包括多个项目，项目信息有：仓库所有者、仓库名称、版本信息、保存到本机的地址、需要下载的文件（可设置多个文件）

点击 download_github_release.py 即可更新多个项目。

更新时，将 config.json 中的版本信息与 api.github 中的最新版进行比较。

若有更新的版本，就会下载最新的release，并同步更新config.json的version。

如果版本号为CI，则下载最新release的指定文件，且跳过版本检测、不更新version。如果没有release，则下载最新工件的全部文件。


config.json 格式如下：
```
{
    "github_token": "",
    "projects": [
        {
            "owner": "2dust",
            "name": "v2rayN",
            "version": "6.55",
            "save_path": "D:\\加速",
            "files": [
                "v2rayN.zip"
            ]
        },
        {
            "owner": "6yy66yy",
            "name": "legod-auto-pause",
            "version": "v2.2.1",
            "save_path": "D:\\加速\\雷神加速器\\自动暂停",
            "files": []
        },
        {
            "owner": "sch-lda",
            "name": "yctest2",
            "version": "CI",
            "save_path": "D:\\Game\\GameTools\\GTAV\\线上小助手",
            "files": [
                "GTA5OnlineTools.exe"
            ]
        }
    ]
}
```

不指定需要下载的文件名称，即下载全部文件："files": []。

指定需要下载的文件名称："files": ["A","B"]。
