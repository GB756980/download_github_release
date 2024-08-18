import os
import sys
import json
import zipfile
import urllib3
import logging
import requests
from tqdm import tqdm

PROJECTS_JSON_FILE = "projects.json"  # 存储项目配置的 JSON 文件名

# 禁用不安全请求的警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 设置日志文件和格式
log_file = "download_log.txt"
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filename=log_file)
console_handler = logging.StreamHandler(sys.stdout)  # 输出到控制台
console_handler.setLevel(logging.INFO)
logging.getLogger().addHandler(console_handler)

def download_file(url, save_path, file_name):
    """下载文件并保存到指定路径"""
    file_save_path = os.path.join(save_path, file_name)  # 拼接文件保存路径
    logging.info(f"开始下载文件: {file_name}")

    # 使用 requests 下载文件
    with requests.get(url, stream=True, verify=False) as r:
        try:
            r.raise_for_status()  # 检查请求是否成功
        except requests.exceptions.HTTPError:
            logging.error(f"下载文件失败: {file_name}")
            return False

        total_size = int(r.headers.get('content-length', 0))  # 获取文件总大小
        # 使用 tqdm 显示下载进度条
        with open(file_save_path, 'wb') as f, tqdm(
                desc=file_name,
                total=total_size,
                unit='iB',
                unit_scale=True,
                unit_divisor=1024,
                ncols=100,
                ascii=True) as bar:
            for chunk in r.iter_content(chunk_size=8192):  # 分块读取内容
                if chunk:
                    f.write(chunk)  # 写入文件
                    bar.update(len(chunk))  # 更新进度条

    logging.info(f"下载完成: {file_name}")
    return True

def extract_zip(file_path, extract_to, files=None):
    """解压缩 ZIP 文件"""
    logging.info(f"解压缩文件: {file_path}")
    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        if files:
            # 仅解压指定文件
            for file in files:
                if file in zip_ref.namelist():
                    zip_ref.extract(file, extract_to)
        else:
            # 解压所有文件
            zip_ref.extractall(extract_to)
    os.remove(file_path)  # 删除压缩文件
    logging.info(f"解压并删除压缩文件: {file_path}")

def download_release_files(owner, repo, version, save_path, files):
    """下载 GitHub 仓库的发布文件"""
    logging.info(f"开始下载 {owner}/{repo} 的最新发布文件...")
    url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"  # 获取最新发布信息的 URL
    response = requests.get(url, verify=False)

    if response.status_code == 200:
        release = response.json()  # 解析 JSON 响应
        latest_version = release['tag_name']  # 获取最新版本标签

        logging.info(f"当前版本: {version} | 最新版本: {latest_version}")

        # 如果当前版本不是 CI 并且与最新版本相同，则无需下载
        if version != "CI" and version == latest_version:
            logging.info("当前版本已是最新，无需下载。")
            return True, version

        assets = release['assets']  # 获取发布资产列表
        files_to_download = [asset['name'] for asset in assets] if not files else files

        if not files_to_download:
            logging.info("未指定特定文件，将下载所有发布文件...")

        for asset in assets:
            file_name = asset['name']
            if file_name in files_to_download:
                file_url = asset['browser_download_url']
                if download_file(file_url, save_path, file_name):
                    if file_name.endswith(".zip"):
                        extract_zip(os.path.join(save_path, file_name), save_path)

        return True, latest_version if version != "CI" else "CI"
    else:
        logging.error(f"无法获取 {owner}/{repo} 的发布信息。")
    return False, version

def download_artifact_files(owner, repo, save_path, files):
    """下载 GitHub Actions 的最新工件文件"""
    logging.info(f"开始下载 {owner}/{repo} 的最新工件文件...")
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/artifacts"  # 获取工件列表的 URL
    response = requests.get(url, verify=False)

    if response.status_code == 200:
        artifacts = response.json()['artifacts']  # 解析工件列表
        if not artifacts:
            logging.info("没有找到可用的工件，尝试下载最新release...")
            return download_release_files(owner, repo, "CI", save_path, files)

        latest_artifact = artifacts[0]  # 获取最新工件
        artifact_url = latest_artifact['archive_download_url']  # 工件下载 URL

        file_save_path = os.path.join(save_path, f"{repo}_latest_artifact.zip")  # 工件保存路径

        if download_file(artifact_url, save_path, f"{repo}_latest_artifact.zip"):
            if files:
                extract_zip(file_save_path, save_path, files)
            else:
                extract_zip(file_save_path, save_path)
            return True, "CI"
    else:
        logging.error(f"无法获取 {owner}/{repo} 的工件信息。")
    return False, "CI"

def update_projects(json_file):
    """更新项目列表"""
    logging.info("开始更新项目列表...")
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)  # 读取 JSON 文件内容

    updated_projects = []

    for project in data["projects"]:
        owner = project["owner"]
        name = project["name"]
        version = project["version"]
        save_path = project["save_path"]
        files = project.get("files", [])

        logging.info(f"\n处理项目: {owner}/{name}")

        if not os.path.exists(save_path):
            os.makedirs(save_path)  # 创建保存路径目录

        # 根据版本进行下载操作
        if version == "CI":
            success, new_version = download_artifact_files(owner, name, save_path, files)
            if not success:
                success, new_version = download_release_files(owner, name, "CI", save_path, files)
        else:
            success, new_version = download_release_files(owner, name, version, save_path, files)

        if success:
            logging.info(f"项目 {owner}/{name} 下载完成。")
            if version != "CI":
                version = new_version  # 更新项目版本
        else:
            logging.error(f"项目 {owner}/{name} 下载失败。")

        # 记录更新后的项目信息
        updated_projects.append({
            "owner": owner,
            "name": name,
            "version": version,
            "save_path": save_path,
            "files": files
        })

    # 将更新后的项目列表写回 JSON 文件
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump({"projects": updated_projects}, f, ensure_ascii=False, indent=4)
    logging.info("项目已全部更新完成。")

if __name__ == "__main__":
    update_projects(PROJECTS_JSON_FILE)  # 执行更新项目列表的函数