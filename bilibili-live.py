import requests as requests_lib
import time
import qrcode
import io
import sys
import json
import os
import obsws_python as obs

# 从配置文件加载设置
config_path = "config.json"
if not os.path.exists(config_path):
    initial_config = {
        "USER_AGENT": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
        "COOKIES_FILE": "cookies.json",
        "OBS_HOST": "localhost",
        "OBS_PORT": 4444,
        "OBS_PASSWORD": "123456",
        "CONFIGURE_OBS": True,
        "AUTO_STREAM": False,
        "AREA_V2": "878"
    }
    with open(config_path, "w") as config_file:
        json.dump(initial_config, config_file, indent=4)
    print(f"初始配置文件已生成: {config_path}")
    input("按任意键退出")
    sys.exit(0)

with open(config_path, "r") as config_file:
    config = json.load(config_file)

USER_AGENT = config["USER_AGENT"]
COOKIES_FILE = config["COOKIES_FILE"]
OBS_HOST = config["OBS_HOST"]
OBS_PORT = config["OBS_PORT"]
OBS_PASSWORD = config["OBS_PASSWORD"]
AUTO_STREAM = config["AUTO_STREAM"]
CONFIGURE_OBS = config["CONFIGURE_OBS"]
AREA_V2 = config["AREA_V2"]

# 全局变量
cookies = {}
headers = {
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'origin': 'https://link.bilibili.com',
    'referer': 'https://link.bilibili.com/p/center/index',
    'sec-ch-ua': '"Microsoft Edge";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-site',
    'user-agent': USER_AGENT,
}

start_data_bls = {
    'room_id': '',  # 填自己的room_id
    'platform': 'pc_link',
    'area_v2': AREA_V2,
    'backup_stream': '0',
    'csrf_token': '',  # 填csrf
    'csrf': '',  # 填csrf，这两个值一样的
}

stop_data_bls = {
    'room_id': '',  # 一样，改room_id
    'platform': 'pc_link',
    'csrf_token': '',  # 一样，改csrf，两个都改
    'csrf': '',
}

def get_qrcode():
    """
    生成登录二维码的URL和key
    """
    url = "https://passport.bilibili.com/x/passport-login/web/qrcode/generate"
    headers = {'User-Agent': USER_AGENT}
    response = requests_lib.get(url, headers=headers)
    return response.json()["data"]

def qr_login(qrcode_key):
    """
    轮询Bilibili服务器检查二维码扫描后的登录状态
    """
    url = "https://passport.bilibili.com/x/passport-login/web/qrcode/poll"
    headers = {'User-Agent': USER_AGENT}
    params = {'qrcode_key': qrcode_key}
    response = requests_lib.get(url, headers=headers, params=params)
    return response

def save_cookies(cookies):
    """
    保存cookies到文件
    """
    with open(COOKIES_FILE, "w") as f:
        json.dump(cookies, f)
    print("Cookies已保存")

def load_cookies():
    """
    从文件加载cookies
    """
    global cookies
    if os.path.exists(COOKIES_FILE):
        with open(COOKIES_FILE, "r") as f:
            cookies = json.load(f)
        print("Cookies已加载")
        return True
    return False

def get_csrf_token_from_cookies():
    """
    从cookies中提取csrf_token和csrf
    """
    global start_data_bls, stop_data_bls
    bili_jct = cookies.get("bili_jct")
    if bili_jct:
        start_data_bls['csrf_token'] = bili_jct
        start_data_bls['csrf'] = bili_jct
        stop_data_bls['csrf_token'] = bili_jct
        stop_data_bls['csrf'] = bili_jct
    else:
        print("无法从cookies中获取bili_jct")
        input("按任意键退出")
        sys.exit(1)

def get_room_id_by_uid():
    """
    使用DedeUserID获取room_id
    """
    dede_user_id = cookies.get("DedeUserID")
    if not dede_user_id:
        print("无法从cookies中获取DedeUserID")
        input("按任意键退出")
        sys.exit(1)
    
    url = f"https://api.live.bilibili.com/room/v2/Room/room_id_by_uid?uid={dede_user_id}"
    response = requests_lib.get(url, headers={'User-Agent': USER_AGENT})
    data = response.json()
    if data['code'] == 0:
        return data['data']['room_id']
    else:
        print(f"获取room_id失败: {data['message']}")
        input("按任意键退出")
        sys.exit(1)

def login():
    """
    主登录函数，生成二维码，显示并检查登录状态
    """
    data = get_qrcode()  # 获取二维码数据
    qrcode_url = data["url"]
    qrcode_key = data["qrcode_key"]

    # 显示二维码URL并生成文本二维码
    print("请扫描二维码或将下面的链接复制到哔哩哔哩内打开")
    print(qrcode_url)
    qr = qrcode.QRCode()
    qr.add_data(qrcode_url)
    f = io.StringIO()
    qr.print_ascii(out=None, tty=False, invert=False)
    f.seek(0)
    print(f.read())

    global cookies
    while not cookies:  # 等待用户扫描并登录
        try:
            login_requests = qr_login(qrcode_key)  # 轮询登录状态
            login_data = login_requests.json()
        except Exception as e:
            print(f"Error: {e}")

        code = login_data["data"]["code"]
        message = login_data["data"]["message"]
        print(f"\r 当前状态:{message}", end="", flush=True)

        if code == 0:
            cookies = login_requests.cookies.get_dict()  # 登录成功后获取cookies
            save_cookies(cookies)  # 保存cookies到文件
            break
        elif code == 86038:
            print("\n二维码已失效，请重新生成")
            input("按任意键退出")
            sys.exit(1)
        elif code == 86090:
            print("\n二维码已扫描，等待确认")

        time.sleep(1.5)  # 每1.5秒轮询一次

    print(f"Cookies: {cookies}")
    print("Cookies储存完成")

def configure_obs_stream(rtmp_addr, rtmp_code):
    """
    配置OBS推流地址和推流码
    """
    if not CONFIGURE_OBS:
        print("跳过OBS配置")
        return

    print("开始配置OBS")

    try:
        ws = obs.ReqClient(host=OBS_HOST, port=OBS_PORT, password=OBS_PASSWORD, timeout=3)
    except obs.error.OBSSDKError as e:
        print(f"OBS 连接失败: {e}")
        input("按任意键退出")
        sys.exit(1)
    
    # 设置推流参数
    settings = {
        "server": rtmp_addr,
        "key": rtmp_code
    }
    ws.set_stream_service_settings(ss_type="rtmp_custom", ss_settings=settings)
    
    if AUTO_STREAM:
        ws.start_stream()  # 自动开始推流
    ws.disconnect()
    print("OBS配置完毕")

def start_live():
    """
    开始直播
    """
    get_csrf_token_from_cookies()  # 从cookies中提取csrf_token
    room_id = get_room_id_by_uid()  # 使用DedeUserID获取room_id
    start_data_bls['room_id'] = room_id
    response = requests_lib.post('https://api.live.bilibili.com/room/v1/Room/startLive', cookies=cookies, headers=headers, data=start_data_bls).json()
    #response = {'code': 0, 'data': {'change': 1, 'status': 'LIVE', 'try_time': '0000-00-00 00:00:00', 'room_type': 0, 'live_key': '605603716031416155', 'sub_session_key': '605603716031416155sub_time:1748580763', 'rtmp': {'type': 1, 'addr': 'rtmp://txy2.live-push.bilivideo.com/live-bvc/', 'code': '?streamname=live_87585800_8233248&key=0fc26a41f2fe8d90db2d7b6c4dcc6e1c&schedule=rtmp&pflag=4', 'new_link': '', 'provider': 'txy2'}, 'protocols': [{'protocol': 'rtmp', 'addr': 'rtmp://txy2.live-push.bilivideo.com/live-bvc/', 'code': '?streamname=live_87585800_8233248&key=0fc26a41f2fe8d90db2d7b6c4dcc6e1c&schedule=rtmp&pflag=4', 'new_link': '', 'provider': 'txy'}], 'notice': {'type': 1, 'status': 0, 'title': '', 'msg': '', 'button_text': '', 'button_url': ''}, 'qr': '', 'need_face_auth': False, 'service_source': 'live-streaming', 'rtmp_backup': None, 'up_stream_extra': {'isp': '小运营商'}}, 'message': '', 'msg': ''} 
    print(response)  # 添加调试信息
    if response['code'] == 0:
        rtmp_info = response['data']['rtmp']
        rtmp_addr = rtmp_info['addr']
        rtmp_code = rtmp_info['code']
        print(f"RTMP地址: {rtmp_addr}")
        print(f"推流码: {rtmp_code}")
        
        configure_obs_stream(rtmp_addr, rtmp_code)  # 配置OBS推流
    else:
        print(f"启动直播失败: {response['message']}")
        print("start_live 请求参数:", {'url': 'https://api.live.bilibili.com/room/v1/Room/startLive', 'cookies': cookies, 'headers': headers, 'data': start_data_bls})

def stop_live():
    """
    停止直播
    """
    get_csrf_token_from_cookies()  # 从cookies中提取csrf_token
    room_id = get_room_id_by_uid()  # 使用DedeUserID获取room_id
    stop_data_bls['room_id'] = room_id
    response = requests_lib.post('https://api.live.bilibili.com/room/v1/Room/stopLive', cookies=cookies, headers=headers, data=stop_data_bls).json()
    if response['code'] == 0:
        print("直播已停止")
        
        if AUTO_STREAM and CONFIGURE_OBS:
            try:
                ws = obs.ReqClient(host=OBS_HOST, port=OBS_PORT, password=OBS_PASSWORD, timeout=3)
            except obs.error.OBSSDKError as e:
                print(f"OBS 连接失败: {e}")
                input("按任意键退出")
                sys.exit(1)
            ws.stop_stream()  # 停止OBS推流
            ws.disconnect()
    else:
        print(f"停止直播失败: {response['message']}")
        print("stop_live 请求参数:", {'url': 'https://api.live.bilibili.com/room/v1/Room/stopLive', 'cookies': cookies, 'headers': headers, 'data': stop_data_bls})

def get_live_status():
    """
    获取直播状态
    """
    room_id = get_room_id_by_uid()
    url = f"https://api.live.bilibili.com/room/v1/Room/get_info?room_id={room_id}"
    response = requests_lib.get(url, headers={'User-Agent': USER_AGENT})
    data = response.json()
    if data['code'] == 0:
        return data['data']['live_status'] == 1
    else:
        print(f"获取直播状态失败: {data['message']}")
        input("按任意键退出")
        sys.exit(1)

if __name__ == "__main__":
    if not load_cookies():
        login()  # 如果没有cookies，提示登录

    if get_live_status():
        print("直播已经开始，准备停止直播")
        stop_live()
    else:
        print("直播尚未开始，准备开始直播")
        start_live()

    input("按任意键退出")
