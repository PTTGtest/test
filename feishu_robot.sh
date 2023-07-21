#/system/bin/sh
while getopts ":title:content:" opt
do
  case $opt in
    title)
      msg_title = $title
      ;;
    content)
      msg_content = $content
      ;;
  esac
done

python feishu_robot.py -title msg_title -content msg_content