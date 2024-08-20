import os  # 提供与操作系统交互的功能，如文件和目录操作
import sys  # 提供与 Python 解释器的交互功能
import json  # 提供 JSON 数据处理功能
import py7zr  # 提供 7z 格式压缩文件的解压功能
import zipfile  # 提供 ZIP 格式压缩文件的解压功能
import urllib3  # 提供 HTTP 请求功能
import logging  # 提供日志记录功能
import requests  # 提供 HTTP 请求功能
from tqdm import tqdm  # 提供进度条显示功能

# 存储项目配置的 JSON 文件名
PROJECTS_JSON_FILE = "config.json"

# 禁用不安全请求的警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 设置日志文件和格式
log_file = "download.log"  # 日志文件名
logging.basicConfig(
    level=logging.INFO,  # 设置日志记录级别为 INFO
    format='%(asctime)s - %(levelname)s - %(message)s',  # 包含时间、日志级别和消息
    filename=log_file,  # 日志文件名
    datefmt='%Y-%m-%d %H:%M:%S'  # 设置时间格式
)
# 控制台输出日志
console_handler = logging.StreamHandler(sys.stdout)  # 创建一个日志处理器，用于输出到控制台
console_handler.setLevel(logging.INFO)  # 设置控制台日志记录级别为 INFO
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')  # 设置控制台输出日志格式
console_handler.setFormatter(formatter)  # 为控制台处理器设置格式
logging.getLogger().addHandler(console_handler)  # 将控制台日志处理器添加到根记录器

def download_file(url, save_path, file_name, token=None):
    file_save_path = os.path.join(save_path, file_name)  # 构造文件保存路径
    older_version_file_path = os.path.join(save_path, f"【旧版本，请手动删除】{file_name}")  # 旧版本文件路径

    logging.info(f"准备下载文件: {file_name} 从: {url}")  # 记录准备下载的文件信息

    headers = {}  # 初始化请求头
    if token:
        headers['Authorization'] = f'token {token}'  # 如果提供了 token，添加到请求头中

    try:
        # 尝试检查文件是否被占用
        def is_file_locked(file_path):
            try:
                with open(file_path, 'a'):  # 尝试以追加模式打开文件
                    return False
            except IOError:
                return True

        # 检查文件是否存在，并且是否被占用
        if os.path.isfile(file_save_path):
            if is_file_locked(file_save_path):
                logging.warning(f"文件 {file_save_path} 已被占用，尝试重命名为: 【旧版本，请手动删除】{file_name}")  # 记录文件被占用的警告信息
                try:
                    os.rename(file_save_path, older_version_file_path)  # 重命名现有文件
                    logging.info(f"现有文件已重命名为: {older_version_file_path}")  # 记录重命名成功的日志
                except PermissionError:
                    logging.error(f"无法重命名文件: {file_save_path}. 文件可能正在被占用.")  # 记录权限错误
                    return False
                except Exception as e:
                    logging.error(f"重命名文件时发生错误: {e}")  # 记录重命名时的其他错误
                    return False
            else:
                logging.info(f"文件 {file_save_path} 已存在，但未被占用。")  # 记录文件存在但未被占用的日志

        # 下载新文件
        response = requests.get(url, headers=headers, stream=True, verify=False)  # 发起 HTTP GET 请求下载文件
        response.raise_for_status()  # 确保请求成功

        total_size = int(response.headers.get('content-length', 0))  # 获取文件总大小
        os.makedirs(save_path, exist_ok=True)  # 确保目录存在
        with open(file_save_path, 'wb') as f, tqdm(
                desc=file_name,
                total=total_size,
                unit='iB',
                unit_scale=True,
                unit_divisor=1024,
                ncols=100,
                ascii=True) as bar:  # 初始化进度条
            for chunk in response.iter_content(chunk_size=8192):  # 读取文件内容
                if chunk:
                    f.write(chunk)  # 写入文件
                    bar.update(len(chunk))  # 更新进度条

        logging.info(f"文件成功下载到: {file_save_path}")  # 记录下载成功的日志
        return True
    except requests.exceptions.RequestException as e:
        logging.error(f"下载文件失败: {file_name}. 错误信息: {e}")  # 记录下载失败的日志
        return False
    except Exception as e:
        logging.error(f"文件下载时发生错误: {e}")  # 记录文件下载时的其他错误
        return False

def extract_archive(file_path, extract_to, files=None):
    if not os.path.isfile(file_path):  # 检查文件是否存在
        logging.error(f"文件不存在: {file_path}")  # 记录错误日志
        return

    logging.info(f"解压缩文件到: {extract_to}")  # 记录解压缩的目标目录
    try:
        os.makedirs(extract_to, exist_ok=True)  # 确保目录存在
        if file_path.endswith(".zip"):  # 如果是 ZIP 文件
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                if files:
                    for file in files:
                        if file in zip_ref.namelist():  # 检查文件是否在压缩包中
                            zip_ref.extract(file, extract_to)  # 解压指定文件
                else:
                    zip_ref.extractall(extract_to)  # 解压所有文件
        elif file_path.endswith(".7z"):  # 如果是 7z 文件
            with py7zr.SevenZipFile(file_path, mode='r') as archive:
                if files:
                    all_files = archive.getnames()  # 获取所有文件名
                    for file in files:
                        if file in all_files:  # 检查文件是否在压缩包中
                            archive.extract(path=extract_to, targets=[file])  # 解压指定文件
                else:
                    archive.extractall(path=extract_to)  # 解压所有文件
        else:
            logging.error(f"不支持的文件格式: {file_path}")  # 记录不支持的文件格式错误
            return

        os.remove(file_path)  # 解压后删除压缩文件
        logging.info(f"删除压缩文件: {file_path}")  # 记录删除压缩文件的日志
    except (zipfile.BadZipFile, py7zr.exceptions.Bad7zFile) as e:
        logging.error(f"无法解压缩文件: {file_path}. 错误信息: {e}")  # 记录解压缩错误
    except Exception as e:
        logging.error(f"解压缩文件时发生错误: {file_path}. 错误信息: {e}")  # 记录解压缩时的其他错误

def download_and_extract(url, save_path, file_name, files=None, token=None):
    if download_file(url, save_path, file_name, token):  # 下载文件
        if file_name.endswith((".zip", ".7z")):  # 如果是压缩文件
            extract_archive(os.path.join(save_path, file_name), save_path, files)  # 解压缩文件

def download_release_files(owner, repo, version, save_path, files=None, token=None):
    logging.info(f"开始处理项目 {owner}/{repo}，本地版本为 {version}")  # 记录处理项目信息

    url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"  # 获取最新发布版本的 API URL
    headers = {}  # 初始化请求头
    if token:
        headers['Authorization'] = f'token {token}'  # 如果提供了 token，添加到请求头中

    try:
        response = requests.get(url, headers=headers, verify=False)  # 发起 HTTP GET 请求获取最新发布版本信息
        response.raise_for_status()  # 确保请求成功

        release = response.json()  # 解析响应的 JSON 数据
        latest_version = release.get('tag_name', 'unknown')  # 获取最新版本号
        release_link = release.get('html_url', '未提供链接')  # 获取发布链接

        logging.info(f"项目 {owner}/{repo} 最新版本为 {latest_version}")  # 记录最新版本信息
        logging.info(f"查看详情: {release_link}")  # 记录发布详情链接

        if version == "CI" or version != latest_version:  # 如果版本是 "CI" 或本地版本不是最新版本
            assets = release.get('assets', [])  # 获取所有发布文件
            files_to_download = [asset['name'] for asset in assets] if not files else files  # 如果未指定文件，下载所有文件

            if not files_to_download:
                logging.info("未指定特定文件，将下载所有发布文件...")  # 记录未指定特定文件的情况

            for asset in assets:
                file_name = asset['name']  # 获取文件名
                if file_name in files_to_download:  # 如果文件名在待下载列表中
                    file_url = asset['browser_download_url']  # 获取文件下载 URL
                    download_and_extract(file_url, save_path, file_name, files, token)  # 下载并解压文件

            if version != "CI":  # 如果不是 "CI" 版本
                update_version(owner, repo, latest_version)  # 更新版本号

            logging.info(f"成功处理 {owner}/{repo} 项目")  # 记录项目处理成功的日志
            logging.info(f"{'=' * 50}")  # 分隔线
            return True, latest_version  # 返回处理成功和最新版本
        else:
            logging.info("当前版本已是最新，无需下载。")  # 记录版本已经是最新的日志
            logging.info(f"成功处理 {owner}/{repo} 项目")  # 记录项目处理成功的日志
            logging.info(f"{'=' * 50}")  # 分隔线
            return True, latest_version  # 返回处理成功和最新版本
    except requests.exceptions.RequestException as e:
        if response.status_code == 401:
            logging.error("请求未经授权。请确保提供了有效的 GitHub 个人访问令牌（GITHUB_TOKEN）。请在 config.json 中配置你的 GITHUB_TOKEN。")  # 记录授权错误
        elif response.status_code == 403:
            logging.error("你在访问 GitHub API 时达到了请求限制。GitHub API 对匿名请求（未认证的请求）和认证请求（使用个人访问令牌的请求）都有访问频率限制。请在 config.json 中配置你的 GITHUB_TOKEN。")  # 记录请求限制错误
        elif response.status_code == 404:
            logging.error("无法找到资源。请检查项目所有者、仓库名称或 URL 是否正确。")  # 记录资源未找到错误
        elif response.status_code == 500:
            logging.error("服务器遇到内部错误。请稍后重试，或检查 GitHub 状态页面以了解是否存在服务中断。")  # 记录服务器内部错误
        elif response.status_code == 502:
            logging.error("服务器遇到网关错误。请稍后重试，或检查 GitHub 状态页面以了解是否存在服务中断。")  # 记录网关错误
        elif response.status_code == 503:
            logging.error("服务不可用。请稍后重试，或检查 GitHub 状态页面以了解是否存在服务中断。")  # 记录服务不可用错误
        else:
            logging.error(f"无法获取 {owner}/{repo} 的工件信息。错误信息: {e}")  # 记录其他错误
        logging.info(f"{'=' * 50}")  # 分隔线
    return False, version  # 返回处理失败和当前版本

def download_artifact_files(owner, repo, save_path, files=None, token=None):
    logging.info(f"开始下载项目 {owner}/{repo} 的最新工件文件...")  # 记录开始下载工件的日志

    url = f"https://api.github.com/repos/{owner}/{repo}/actions/artifacts"  # 获取工件列表的 API URL
    headers = {}  # 初始化请求头
    if token:
        headers['Authorization'] = f'token {token}'  # 如果提供了 token，添加到请求头中

    try:
        response = requests.get(url, headers=headers, verify=False)  # 发起 HTTP GET 请求获取工件列表
        response.raise_for_status()  # 确保请求成功

        artifacts = response.json().get('artifacts', [])  # 解析响应的 JSON 数据，获取所有工件
        if not artifacts:
            logging.info("没有找到可用的工件。")  # 记录没有工件的日志
            return False, "CI"  # 返回处理失败和 "CI"

        latest_artifact = artifacts[0]  # 获取最新工件
        artifact_url = latest_artifact['archive_download_url']  # 获取工件的下载 URL
        artifact_name = f"{latest_artifact['name']}.zip"  # 工件名称

        download_and_extract(artifact_url, save_path, artifact_name, files, token)  # 下载并解压工件
        logging.info(f"项目 {owner}/{repo} 工件下载成功，处理完成")  # 记录工件下载成功的日志
        logging.info(f"{'=' * 50}")  # 分隔线
        return True, "CI"  # 返回处理成功和 "CI"
    except requests.exceptions.RequestException as e:
        if response.status_code == 401:
            logging.error("请求未经授权。请确保提供了有效的 GitHub 个人访问令牌（GITHUB_TOKEN）。请在 config.json 中配置你的 GITHUB_TOKEN。")  # 记录授权错误
        elif response.status_code == 403:
            logging.error("你在访问 GitHub API 时达到了请求限制。GitHub API 对匿名请求（未认证的请求）和认证请求（使用个人访问令牌的请求）都有访问频率限制。请在 config.json 中配置你的 GITHUB_TOKEN。")  # 记录请求限制错误
        elif response.status_code == 404:
            logging.error("无法找到资源。请检查项目所有者、仓库名称或 URL 是否正确。")  # 记录资源未找到错误
        elif response.status_code == 500:
            logging.error("服务器遇到内部错误。请稍后重试，或检查 GitHub 状态页面以了解是否存在服务中断。")  # 记录服务器内部错误
        elif response.status_code == 502:
            logging.error("服务器遇到网关错误。请稍后重试，或检查 GitHub 状态页面以了解是否存在服务中断。")  # 记录网关错误
        elif response.status_code == 503:
            logging.error("服务不可用。请稍后重试，或检查 GitHub 状态页面以了解是否存在服务中断。")  # 记录服务不可用错误
        else:
            logging.error(f"无法获取 {owner}/{repo} 的工件信息。错误信息: {e}")  # 记录其他错误
        logging.info(f"{'=' * 50}")  # 分隔线
    return False, "CI"  # 返回处理失败和 "CI"

def update_version(owner, repo, new_version):
    logging.info(f"更新项目 {owner}/{repo} 的版本号到 {new_version}")  # 记录更新版本号的日志
    try:
        with open(PROJECTS_JSON_FILE, 'r', encoding='utf-8') as f:  # 以只读模式打开配置文件
            projects = json.load(f)  # 解析 JSON 数据

        updated = False  # 标记是否更新了版本号
        for project in projects.get('projects', []):  # 遍历项目列表
            if project.get('owner') == owner and project.get('name') == repo:  # 找到需要更新的项目
                project['version'] = new_version  # 更新版本号
                updated = True  # 设置标记为 True
                break

        if updated:  # 如果成功更新版本号
            with open(PROJECTS_JSON_FILE, 'w', encoding='utf-8') as f:  # 以写入模式打开配置文件
                json.dump(projects, f, indent=4, ensure_ascii=False)  # 将更新后的 JSON 数据写入文件
            logging.info(f"成功更新 {owner}/{repo} 的版本号到 {new_version}")  # 记录更新成功的日志
        else:
            logging.warning(f"未找到需要更新版本的项目 {owner}/{repo}")  # 记录未找到项目的警告信息

    except Exception as e:
        logging.error(f"更新版本失败: {e}")  # 记录更新版本失败的日志

def update_projects():
    logging.info(f"{'=' * 50}")  # 分隔线
    logging.info(f"读取配置文件: {PROJECTS_JSON_FILE}")  # 记录读取配置文件的日志
    logging.info(f"{'=' * 50}")  # 分隔线

    try:
        with open(PROJECTS_JSON_FILE, 'r', encoding='utf-8') as f:
            projects = json.load(f)  # 读取 JSON 配置文件
    except Exception as e:
        logging.error(f"读取配置文件失败: {e}")  # 记录读取配置文件失败的日志
        return

    token = projects.get('github_token')  # 只读取一次 token

    for project in projects.get('projects', []):  # 遍历配置文件中的项目
        owner = project.get('owner')  # 获取项目所有者
        repo = project.get('name')  # 获取项目名称
        version = project.get('version', 'CI')  # 获取项目版本，默认为 "CI"
        save_path = project.get('save_path', '.')  # 获取文件保存路径，默认为当前目录
        file_list = project.get('files', [])  # 获取要下载的文件列表

        if not owner or not repo:  # 如果项目配置缺少 owner 或 repo
            logging.warning(f"项目配置缺少 owner 或 repo (owner: {owner}, repo: {repo})")  # 记录警告日志
            continue

        success, latest_version = download_release_files(owner, repo, version, save_path, file_list, token)  # 下载和处理发布文件
        if success and version == "CI":  # 如果处理成功且版本为 "CI"
            continue

if __name__ == "__main__":
    update_projects()  # 调用更新项目函数