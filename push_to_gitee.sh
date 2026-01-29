#!/bin/bash
# 快速上传到 Gitee 的脚本
# 使用方法: ./push_to_gitee.sh <你的Gitee用户名> <仓库名>

if [ $# -ne 2 ]; then
    echo "用法: $0 <Gitee用户名> <仓库名>"
    echo "示例: $0 myusername pdf_to_markdown"
    exit 1
fi

USERNAME=$1
REPO_NAME=$2
GITEE_URL="https://gitee.com/${USERNAME}/${REPO_NAME}.git"

echo "正在添加远程仓库: ${GITEE_URL}"
git remote add origin ${GITEE_URL} 2>/dev/null || git remote set-url origin ${GITEE_URL}

echo "正在推送到 Gitee..."
git push -u origin master

echo "✅ 上传完成！"
echo "仓库地址: https://gitee.com/${USERNAME}/${REPO_NAME}"
