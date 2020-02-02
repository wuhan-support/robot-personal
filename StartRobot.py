from src.robot.NcovWeRobotServer import start_server
import time
if __name__=='__main__':
    warm_tip = "****************************************\n" \
               "**************微信疫情信息小助手**************\n" \
               "****************************************"
    print(warm_tip)
    print("注意！！！稍后会弹出网页版微信登陆的二维码")
    print("扫码登陆成功后手机端文件传输助手会收到提示")
    print("短时间内重新登陆不需要重新扫码")
    print("软件使用期间请不要关闭本窗口")
    print("向文件传输助手发送\"help\"可获取帮助信息")
    print("本软件不会保存任何聊天记录，疫情信息和疫情订阅信息会存在您的本地")
    print("存在一定的安全风险，比如频繁使用可能会造成您最终无法登陆网页版微信")
    print("本项目代码开源，开源地址：https://github.com/wuhan-support/robot-personal")
    print("支持武汉，我们在一起，https://app.feiyan.help")
    time.sleep(3)
    start_server()