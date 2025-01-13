# Bilibili Live Stream Automation

这是一个用于自动化管理Bilibili直播的Python脚本。它可以自动登录Bilibili账号，获取直播间ID，启动和停止直播，并配置OBS推流。

## 依赖

请确保已安装以下依赖项：

```
requests
qrcode
obs-websocket-py
```

你可以通过以下命令安装所有依赖项：

```bash
pip install -r requirements.txt
```

## 使用方法

1. 克隆或下载此项目到本地。
2. 运行脚本：

```bash
python bilibili-live.py
```

3. 如果是第一次运行，脚本会生成一个初始配置文件 `config.json`，请根据需要修改配置文件。
4. 按照提示扫描二维码登录Bilibili账号。
5. 脚本会自动检测直播状态并启动或停止直播。

## 配置文件

`config.json` 文件包含以下配置项：

- `USER_AGENT`: 浏览器的用户代理字符串。
- `COOKIES_FILE`: 保存cookies的文件路径。
- `OBS_HOST`: OBS WebSocket服务器的主机地址。
- `OBS_PORT`: OBS WebSocket服务器的端口。
- `OBS_PASSWORD`: OBS WebSocket服务器的密码。
- `CONFIGURE_OBS`: 是否配置OBS推流。
- `AUTO_STREAM`: 是否自动开始推流。
- `AREA_V2`: 直播分区ID。

## 注意事项

- 请确保OBS已安装并启用了WebSocket插件。
- 请确保配置文件中的OBS WebSocket服务器信息正确。
