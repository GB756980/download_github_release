项目有两个文件，分别是project.json和download_github_release.py。

project.json包括项目的所有者、仓库名称、版本信息、保存到本机的地址、需要下载的文件（可设置多个。

json中可收录多个项目的信息，点击即可更新多个项目。

更新时，将json文件中的版本信息与api.github中的最新版进行比较，若有更新的版本，就会下载最新的release，并同步更新project.json的version。

如果版本号为CI，则下载最新工件的全部文件。如果版本号为CI，且不生成工件，则下载最新release的指定文件，且跳过版本检测、不更新version。


project.json格式如下：
```
{
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

不指定需要下载的文件名称："files": []。

指定需要下载的文件名称："files": ["A","B"]。

如果版本号是CI，且不生成工件，则必须指定文件名："files": ["GTA5OnlineTools.exe"]。