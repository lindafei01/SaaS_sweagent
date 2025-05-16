import os
import shutil
import stat

def on_rm_error(func, path, exc_info):
    # 解除只读属性
    try:
        os.chmod(path, stat.S_IWRITE)
    except Exception:
        pass
    # 如果是文件，直接删
    if os.path.isfile(path) or os.path.islink(path):
        try:
            os.remove(path)
        except Exception:
            pass
    # 如果是目录，递归删
    elif os.path.isdir(path):
        try:
            shutil.rmtree(path, onerror=on_rm_error)
        except Exception:
            pass

# 获取当前工作目录
root_dir = os.path.abspath('.')
deleted = []

for dirpath, dirnames, filenames in os.walk(root_dir):
    # 判断是否为 sample0/code 目录
    if os.path.basename(dirpath) == 'code' and os.path.basename(os.path.dirname(dirpath)) == 'sample0':
        git_dir = os.path.join(dirpath, '.git')
        if os.path.isdir(git_dir):
            print(f"Deleting: {git_dir}")
            shutil.rmtree(git_dir, onerror=on_rm_error)
            deleted.append(git_dir)

print(f"\n共删除 {len(deleted)} 个 .git 文件夹。")
if deleted:
    print("删除的路径：")
    for d in deleted:
        print(d)
else:
    print("未找到任何 sample0/code/.git 文件夹。")
