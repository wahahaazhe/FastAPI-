# myproject/run.py
import uvicorn
import os

if __name__ == "__main__":
    # 打印当前工作目录和 sys.path 可以帮助调试，但通常不需要
    # print(f"Current working directory for run.py: {os.getcwd()}")
    # import sys
    # print(f"sys.path: {sys.path}")

    uvicorn.run(
        "app.main:app",  # 告诉uvicorn，应用实例'app'在'app'包的'main'模块中
        host="0.0.0.0",
        port=8000,
        reload=True
        # 不要使用 app_dir 参数
        # Uvicorn 会在当前工作目录 (即 D:\fastApiProject) 下查找名为 'app' 的包/目录
    )