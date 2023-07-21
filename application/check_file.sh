#!/bin/bash

# 遍历 result 文件夹中的每个 sn 号文件夹
for sn_folder in result/*/; do
    sn=$(basename "$sn_folder")
    
    # 检查 sn 号文件夹中的 AgingResult.txt
    txt_file="$sn_folder/AgingResult.txt"

    if [ -f "$txt_file" ]; then
        # 初始化失败行详情字符串
        failure_details=""

        # 逐行检查 AgingResult.txt
        while IFS= read -r line; do
            # 检查行中是否包含 pass/untest 或为空
            if [[ "$line" == *pass* || "$line" == *untest* || -z "{$line// }" ]]; then
                # 成功行
                continue
            else
                # 失败行，去掉行尾回车并添加到失败行详情字符串
                failure_details+=" $(echo "$line" | tr -d '\n')"
            fi
        done < "$txt_file"

        # 写入结果到 result.txt
        if [ -z "$failure_details" ]; then
            echo "$sn: pass" >> result.txt
        else
            echo "$sn:$failure_details" >> result.txt
        fi
    fi
done
